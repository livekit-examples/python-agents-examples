"""Observer agent for parallel guardrail monitoring."""
import logging
import sys
import asyncio
import json
from pathlib import Path
from livekit.agents import ConversationItemAddedEvent
from typing_extensions import TypedDict
from livekit import rtc
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import openai

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_prompt

logger = logging.getLogger("doheny-surf-desk.observer")


# Structured output schema for LLM evaluation
class SafetyEvaluation(TypedDict):
    """LLM evaluation result for safety/compliance issues."""
    minor_detected: bool
    injury_mentioned: bool
    weather_concern: bool
    skill_mismatch: bool
    details: str  # Brief explanation of detected issues


class ObserverAgent:
    """
    Parallel observer that monitors conversations for safety and compliance.
    
    This agent does NOT join the main session as an active agent.
    Instead, it listens to session events and sends guardrail hints when needed.
    
    Uses LLM-based judgment (similar to test judge() function) for intelligent
    guardrail detection instead of simple keyword matching.
    """
    
    def __init__(self, session, llm=None):
        """Initialize the observer agent.
        
        Args:
            session: AgentSession to monitor and inject guardrail hints into
            llm: LLM instance for judging (optional, defaults to gpt-4o-mini)
        """
        self.session = session
        self.instructions = load_prompt('observer_prompt.yaml')
        self.llm = llm or openai.LLM(model="gpt-4o-mini")
        self.conversation_history = []
        self.hints_sent = []
        self.last_eval_transcript_count = 0
        self.eval_threshold = 3
        self._evaluating = False
        
        self._setup_listeners()
        
        logger.info(f"ObserverAgent initialized: LLM={self.llm.model if hasattr(self.llm, 'model') else 'custom'}, eval_threshold={self.eval_threshold}")
    
    def _setup_listeners(self):
        """Set up session event listeners."""
        
        @self.session.on("conversation_item_added")
        def conversation_item_added(event: ConversationItemAddedEvent):
            if event.item.role != "user":
                return

            transcript_text = ""
            for content in event.item.content:
                if isinstance(content, str):
                    transcript_text += content
            
            logger.info(f"[OBSERVER] 📝 User turn completed: {transcript_text}")
            
            self.conversation_history.append({
                "text": transcript_text,
                "participant": "user",
                "timestamp": None
            })
            
            total_segments = len(self.conversation_history)
            new_segments = total_segments - self.last_eval_transcript_count
            
            if new_segments >= self.eval_threshold:
                logger.info(f"[OBSERVER] 🔍 Triggering evaluation ({new_segments} segments)")
                asyncio.create_task(self._evaluate_with_llm())
                self.last_eval_transcript_count = total_segments
    
    async def _evaluate_with_llm(self):
        """Use LLM to evaluate recent conversation for guardrail triggers."""
        if self._evaluating:
            return
        
        self._evaluating = True
        
        try:
            recent_history = self.conversation_history[-10:]
            if not recent_history:
                return
            
            conversation_text = "\n".join([
                f"{msg['participant']}: {msg['text']}"
                for msg in recent_history
            ])
            
            userdata = self.session.userdata
            userdata_summary = self._format_userdata_summary(userdata)
            eval_prompt = f"""You are a safety observer for a surf school booking system.

Analyze the following conversation excerpt and identify if any of these issues are present:

1. MINOR DETECTION: Customer is under 18 years old
2. INJURY MENTION: Customer mentions injuries, medical conditions, or physical limitations
3. WEATHER CONCERNS: Discussion of dangerous weather/surf conditions
4. SKILL MISMATCH: Beginner wanting advanced surf spots (Trestles)
5. VIP CUSTOMER: Customer's name is Jack (case-insensitive) - special 50% discount promotion

Conversation excerpt:
{conversation_text}

Current user data: {userdata_summary}

Only flag issues that are clearly present in the conversation.
Provide a brief explanation in the details field.

CRITICAL: Return ONLY raw JSON, no markdown, no code blocks, no explanations.
Return your response as a JSON object with these exact fields:
{{
  "minor_detected": true/false,
  "injury_mentioned": true/false,
  "weather_concern": true/false,
  "skill_mismatch": true/false,
  "jack_detected": true/false,
  "details": "brief explanation"
}}

Example valid response:
{{"minor_detected": false, "injury_mentioned": false, "weather_concern": false, "skill_mismatch": false, "jack_detected": true, "details": "Customer name is Jack - eligible for VIP discount"}}"""

            chat_ctx = ChatContext()
            chat_ctx.add_message(role="user", content=eval_prompt)
            
            response_text = ""
            async with self.llm.chat(chat_ctx=chat_ctx) as stream:
                async for chunk in stream:
                    if chunk.delta.content:
                        response_text += chunk.delta.content
            
            if not response_text:
                return
            
            eval_result = self._parse_eval_response(response_text)
            
            if eval_result:
                has_issues = any([
                    eval_result.get('minor_detected'),
                    eval_result.get('injury_mentioned'),
                    eval_result.get('weather_concern'),
                    eval_result.get('skill_mismatch'),
                    eval_result.get('jack_detected')
                ])
                
                if has_issues:
                    logger.info(
                        f"[OBSERVER] ⚠️ Issues detected: "
                        f"minor={eval_result.get('minor_detected')}, "
                        f"injury={eval_result.get('injury_mentioned')}, "
                        f"weather={eval_result.get('weather_concern')}, "
                        f"skill_mismatch={eval_result.get('skill_mismatch')}, "
                        f"jack={eval_result.get('jack_detected')}"
                    )
                
                await self._process_eval_result(eval_result)
            
        except Exception as e:
            logger.error(f"Error during LLM evaluation: {e}", exc_info=True)
        finally:
            self._evaluating = False
    
    def _parse_eval_response(self, response_text: str) -> dict | None:
        """Parse LLM response as JSON."""
        try:
            result = json.loads(response_text.strip())
            if isinstance(result, dict):
                return self._validate_eval_result(result)
        except json.JSONDecodeError:
            pass
        
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                json_str = response_text[start:end]
                result = json.loads(json_str.strip())
                if isinstance(result, dict):
                    return self._validate_eval_result(result)
            except json.JSONDecodeError:
                pass
        
        logger.error(f"[OBSERVER] ⚠️ Failed to parse JSON response: {response_text[:150]}")
        return None
    
    def _validate_eval_result(self, result: dict) -> dict:
        """Validate and normalize evaluation result with defaults."""
        return {
            'minor_detected': bool(result.get('minor_detected', False)),
            'injury_mentioned': bool(result.get('injury_mentioned', False)),
            'weather_concern': bool(result.get('weather_concern', False)),
            'skill_mismatch': bool(result.get('skill_mismatch', False)),
            'jack_detected': bool(result.get('jack_detected', False)),
            'details': str(result.get('details', ''))
        }
    
    def _format_userdata_summary(self, userdata) -> str:
        """Format userdata into a readable summary."""
        parts = []
        if userdata.name:
            parts.append(f"Name: {userdata.name}")
        if userdata.age:
            parts.append(f"Age: {userdata.age}")
        if userdata.is_minor:
            parts.append("MINOR FLAG: True")
        if userdata.experience_level:
            parts.append(f"Experience: {userdata.experience_level}")
        if userdata.spot_location:
            parts.append(f"Location: {userdata.spot_location}")
        if userdata.has_injury:
            parts.append("INJURY FLAG: True")
        
        return ", ".join(parts) if parts else "No user data yet"
    
    async def _process_eval_result(self, eval_result: dict):
        """Process LLM evaluation results and send appropriate hints."""
        details = eval_result.get('details', '')
        
        if eval_result.get('minor_detected') and 'minor_detected' not in self.hints_sent:
            logger.warning("[OBSERVER] 🚨 MINOR DETECTED - sending hint")
            await self._send_guardrail_hint(
                severity="CRITICAL",
                trigger="Minor detected",
                hint=(
                    f"LLM Analysis: Customer appears to be under 18. {details}\n\n"
                    "Action: Set is_minor=True flag and ensure ConsentTask is run before "
                    "BillingAgent accepts payment. California law requires guardian consent."
                )
            )
            self.hints_sent.append('minor_detected')
        
        if eval_result.get('injury_mentioned') and 'injury_mentioned' not in self.hints_sent:
            logger.warning("[OBSERVER] ⚠️ INJURY MENTIONED")
            await self._send_guardrail_hint(
                severity="WARNING",
                trigger="Injury/medical condition detected",
                hint=(
                    f"LLM Analysis: {details}\n\n"
                    "Action: Recommend lighter/shorter session, provide safety disclaimer, "
                    "suggest consulting their doctor. Set has_injury=True flag."
                )
            )
            self.hints_sent.append('injury_mentioned')
        
        if eval_result.get('weather_concern') and 'weather_concern' not in self.hints_sent:
            logger.warning("[OBSERVER] WEATHER CONCERN - sending WARNING guardrail hint")
            await self._send_guardrail_hint(
                severity="WARNING",
                trigger="Weather/surf conditions concern",
                hint=(
                    f"LLM Analysis: {details}\n\n"
                    "Action: Warn about difficulty level and safety. Offer to reschedule "
                    "if conditions exceed skill level. Safety first!"
                )
            )
            self.hints_sent.append('weather_concern')
        
        if eval_result.get('skill_mismatch') and 'skill_mismatch' not in self.hints_sent:
            logger.warning("[OBSERVER] SKILL MISMATCH - sending WARNING guardrail hint")
            await self._send_guardrail_hint(
                severity="WARNING",
                trigger="Skill/location mismatch",
                hint=(
                    f"LLM Analysis: {details}\n\n"
                    "Action: Strongly recommend beginner-friendly location (Doheny). "
                    "Explain safety concerns with advanced spots."
                )
            )
            self.hints_sent.append('skill_mismatch')
        
        if eval_result.get('jack_detected') and 'jack_discount' not in self.hints_sent:
            logger.warning("[OBSERVER] 🎉 VIP CUSTOMER DETECTED (Jack) - sending discount offer")
            await self._send_guardrail_hint(
                severity="INFO",
                trigger="VIP Customer - Jack",
                hint=(
                    f"SPECIAL PROMOTION DETECTED: {details}\n\n"
                    "Action: Immediately offer a special 50% discount on their surf lesson. "
                    "Say something like 'Great news! We have a special promotion for you today - "
                    "you're getting 50% off your surf lesson!' Be enthusiastic and make them feel special."
                )
            )
            self.hints_sent.append('jack_discount')
    
    async def _send_guardrail_hint(self, severity: str, trigger: str, hint: str):
        """Inject a guardrail hint into the active agent's context."""
        logger.warning(f"[OBSERVER] {severity}: {trigger}")
        logger.info(f"[OBSERVER] Hint: {hint}")
        
        if not hasattr(self.session, 'current_agent') or not self.session.current_agent:
            logger.warning("No active agent to inject hint into")
            return
        
        current_agent = self.session.current_agent
        
        hint_message = f"""[GUARDRAIL ALERT - {severity}]: {trigger}

{hint}

ACKNOWLEDGMENT REQUIRED: In your next response, briefly acknowledge this alert and take the required action."""
        
        ctx_copy = current_agent.chat_ctx.copy()
        ctx_copy.add_message(
            role="system",
            content=hint_message
        )
        
        await current_agent.update_chat_ctx(ctx_copy)
    


async def start_observer(session, llm=None):
    """Start the observer agent for a session.
    
    Args:
        session: AgentSession to monitor and inject guardrail hints into
        llm: Optional LLM instance for evaluation (defaults to gpt-4o-mini)
        
    Returns:
        ObserverAgent instance
    """
    observer = ObserverAgent(session, llm=llm)
    logger.info("Observer agent started with LLM-based evaluation and context injection")
    return observer
