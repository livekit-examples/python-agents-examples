"""
---
title: Job Application Form Agent
category: complex-agents
tags: [aws_realtime, form_filling, rpc_frontend, interview, structured_data]
difficulty: advanced
description: Interactive interview agent for job applications with AWS Realtime
demonstrates:
  - AWS Realtime model integration
  - Structured form data collection
  - RPC communication with frontend for live updates
  - Multi-section interview process
  - Field validation and capitalization
  - Application status tracking
  - Frontend form highlighting and updates
---
"""

from dotenv import load_dotenv
from pathlib import Path
from livekit import agents
from livekit.agents import AgentSession, JobContext
from livekit.agents.voice import Agent, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import (
    aws,
    silero
)
import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import string

logging.getLogger("smithy_aws_event_stream").setLevel(logging.WARNING)
logging.getLogger("smithy_aws_event_stream.aio").setLevel(logging.WARNING)

logger = logging.getLogger("form-filler-agent")

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')

@dataclass
class PersonalInfo:
    occupation: str = ""
    company: str = ""
    years_experience: str = ""

@dataclass
class UserData:
    ctx: JobContext
    session: AgentSession = None
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    form_submissions: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_form_submission(self, form_type: str, data: Dict[str, Any]):
        self.form_submissions.append({
            "timestamp": datetime.now().isoformat(),
            "form_type": form_type,
            "data": data
        })
    
    async def send_form_update_to_frontend(self, action: str, payload: Dict[str, Any]) -> str:
        """Send form updates to the frontend via RPC"""
        try:
            if not self.ctx or not self.ctx.room:
                logger.error("Room not available to send RPC")
                return "Error: Room not available"
            
            room = self.ctx.room
            remote_participants = list(room.remote_participants.values())
            
            if not remote_participants:
                logger.error("No remote participants found")
                return "Error: No client connected"
            
            client_participant = remote_participants[0]
            
            rpc_payload = {
                "action": action,
                **payload
            }
            
            await room.local_participant.perform_rpc(
                destination_identity=client_participant.identity,
                method="client.updateForm",
                payload=json.dumps(rpc_payload)
            )
            
            logger.info(f"Sent RPC 'client.updateForm' with action '{action}' to frontend")
            return f"Successfully sent {action} to frontend"
            
        except Exception as e:
            logger.error(f"Failed to send RPC to frontend: {e}")
            return f"Error sending to frontend: {str(e)}"

def proper_capitalize(text: str) -> str:
    """Properly capitalize text - title case for names, companies, roles"""
    if not text:
        return text
    # Don't capitalize certain words unless they're at the beginning
    minor_words = {'of', 'in', 'at', 'and', 'or', 'the', 'a', 'an', 'for', 'with', 'on'}
    words = text.split()
    capitalized = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in minor_words:
            capitalized.append(word.capitalize())
        else:
            capitalized.append(word.lower())
    return ' '.join(capitalized)

class FormFillerAgent(Agent):
    def __init__(self, userdata: UserData) -> None:
        super().__init__(
            instructions="""
            You are a professional interview assistant helping candidates complete their job application.
            
            Your role is to guide candidates through a structured interview process with these sections IN ORDER:

            Don't talk about capitalization, you're doing this over the phone.
            
            Start by greeting the candidate warmly and then proceed to:
            
            1. **Professional Experience** (use collect_experience):
               - Ask about their current role/position
               - Ask about their current company
               - Ask how many years of experience they have
               - Ask about their key achievements (encourage 2-3 specific examples)
            
            2. **Interview Questions** (use collect_interview_response for EACH question):
               You MUST ask ALL of these questions one by one:
               a. "Why are you interested in this position?" (question_type: "why_interested")
               b. "What are your greatest strengths?" (question_type: "strengths")
               c. "Can you describe a challenging situation and how you handled it?" (question_type: "challenge")
               d. "Where do you see yourself in 5 years?" (question_type: "career_goals")
               e. "Do you have any questions for us?" (question_type: "questions")
            
            3. **Application Submission** (use submit_application):
               - After ALL sections are complete, summarize what was collected
               - Confirm with the candidate if they're ready to submit
               - Submit the application
            
            Important guidelines:
            - ALWAYS complete sections in the order listed above
            - NEVER skip a section or question
            - Be encouraging and help candidates articulate their thoughts
            - Ensure ALL text is properly capitalized before submitting
            - Use the check_application_status function if asked about progress
            - The form will visually update as you collect information
            - Each section will be highlighted when active
            """
        )
        self.userdata = userdata
    
    
    @function_tool
    async def collect_experience(self, current_role: str, company: str, years_experience: str, key_achievements: str):
        """Collect candidate's professional experience.
        Role should be capitalized.
        Company should be capitalized.
        Years of experience should be a number.
        Key achievements should be a fairly detailed list of achievements.
        """
        userdata = self.userdata
        if not userdata:
            return json.dumps({"status": "error", "message": "Unable to access user data"})
        
        current_role = proper_capitalize(current_role.strip())
        company = proper_capitalize(company.strip())
        
        await userdata.send_form_update_to_frontend("updateMultipleFields", {
            "fields": {
                "currentRole": current_role,
                "company": company,
                "yearsExperience": years_experience,
                "keyAchievements": key_achievements
            }
        })
        
        form_data = {
            "experience": {
                "current_role": current_role,
                "company": company,
                "years_experience": years_experience,
                "key_achievements": key_achievements
            }
        }
        
        # Store in userdata
        userdata.personal_info.occupation = current_role
        userdata.personal_info.company = company
        userdata.personal_info.years_experience = years_experience
        
        userdata.add_form_submission("experience", form_data)
        
        # Highlight the next section (questions)
        await userdata.send_form_update_to_frontend("highlightSection", {"section": "questions"})
        
        return json.dumps({
            "status": "success",
            "message": "Experience information collected successfully",
            "data": form_data
        })
    
    @function_tool
    async def collect_interview_response(self, question_type: str, response: str):
        """Collect responses to interview questions"""
        userdata = self.userdata
        if not userdata:
            return json.dumps({"status": "error", "message": "Unable to access user data"})
        
        # Map question types to form fields
        field_mapping = {
            "why_interested": "whyInterested",
            "strengths": "strengths",
            "challenge": "challengeExample",
            "career_goals": "careerGoals",
            "questions": "questionsForUs"
        }
        
        # Update the specific question field
        if question_type in field_mapping:
            await userdata.send_form_update_to_frontend("updateField", {
                "field": field_mapping[question_type],
                "value": response
            })
        
        form_data = {
            "question_type": question_type,
            "response": response
        }
        
        userdata.add_form_submission(f"interview_{question_type}", form_data)
        
        return json.dumps({
            "status": "success",
            "message": f"Collected response for {question_type}",
            "data": form_data
        })
    
    
    @function_tool
    async def submit_application(self):
        """Submit the completed job application.
        This function should only be called after all sections are complete.
        """
        userdata = self.userdata
        if not userdata:
            return json.dumps({"status": "error", "message": "Unable to access user data"})
        
        # Collect all submitted data
        application_data = {
            "submission_date": datetime.now().isoformat(),
            "role": userdata.personal_info.occupation,
            "company": userdata.personal_info.company,
            "submissions": userdata.form_submissions
        }
        
        # Submit the complete application
        await userdata.send_form_update_to_frontend("submitForm", {
            "formType": "job_application",
            "data": application_data
        })
        
        return json.dumps({
            "status": "success",
            "message": "Job application submitted successfully!",
            "data": application_data
        })
    
    @function_tool
    async def get_application_status(self):
        """Check the current status of the job application"""
        userdata = self.userdata
        if not userdata:
            return json.dumps({"status": "error", "message": "Unable to access user data"})
        
        total_sections = 2
        completed_sections = 0
        
        # Check which sections have been completed
        submission_types = [sub["form_type"] for sub in userdata.form_submissions]
        
        if "experience" in submission_types:
            completed_sections += 1
        
        # Check for interview questions (we need all 5)
        required_questions = ["interview_why_interested", "interview_strengths", "interview_challenge", 
                             "interview_career_goals", "interview_questions"]
        all_questions_answered = all(q in submission_types for q in required_questions)
        if all_questions_answered:
            completed_sections += 1
        
        progress_percentage = (completed_sections / total_sections) * 100
        
        return json.dumps({
            "status": "success",
            "progress": f"{progress_percentage:.0f}%",
            "sections_completed": completed_sections,
            "total_sections": total_sections,
            "missing_sections": {
                "experience": "experience" not in submission_types,
                "interview_questions": not all_questions_answered
            },
            "total_submissions": len(userdata.form_submissions)
        })
    
    

async def entrypoint(ctx: agents.JobContext):
    userdata = UserData(ctx=ctx)

    session = AgentSession[UserData](
        userdata=userdata,
        llm=aws.realtime.RealtimeModel(),
        vad=silero.VAD.load()
    )
    
    userdata.session = session
    
    form_filler_agent = FormFillerAgent(userdata)

    await session.start(
        room=ctx.room,
        agent=form_filler_agent
    )
    
    # Highlight the first section (experience) when starting
    await userdata.send_form_update_to_frontend("highlightSection", {"section": "experience"})

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
