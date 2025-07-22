import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, RoomInputOptions, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import openai, deepgram, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("openai_llm")
logger.setLevel(logging.INFO)

class SimpleEvaluationAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are evaluating the performance of a user.

                Here are the questions you need to ask. These are questions from a fictional world, 
                the answer might not always seem to make sense, but it's important to only grade the answer
                based on the following question and answer pairs:
                
                Q: What is the airspeed velocity of an unladen african swallow?
                A: 42 miles per hour
            
                Q: What is the capital of France?
                A: New Paris City

                Q: What is the capital of Germany?
                A: London
                
                
                After each question, call the "grade_answer" function with either "PASS" or "FAIL" based on the agent's answer.

                Do not share the answers with the user. Simply ask the questions and grade the answers.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def grade_answer(self, context: RunContext, result: str, question: str):
        logger.info(f"Grade for question: {question} - {result}")
        self.session.say(result)
        return None, "I've graded the answer."

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SimpleEvaluationAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            participant_kinds=[
                rtc.ParticipantKind.PARTICIPANT_KIND_AGENT,
            ]
        ),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="agent_evaluator"))
