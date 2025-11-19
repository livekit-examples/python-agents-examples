"""Intake agent for collecting customer profile information."""
from livekit.agents.beta.workflows.email_address import GetEmailResult
from livekit.agents.llm import function_tool
from livekit.agents.beta.workflows import TaskGroup

from .base_agent import BaseAgent, RunContext_T
from tasks.name_task import NameTask
from tasks.phone_task import PhoneTask
from tasks.age_task import AgeTask
from tasks.email_task import GetEmailTask
from tasks.experience_task import ExperienceTask


class IntakeAgent(BaseAgent):
    """Agent responsible for collecting customer profile information via sequential tasks."""
    
    def __init__(self, chat_ctx=None):
        # Note: We need LLM for tasks to use session.generate_reply()
        # Tasks will use the session's LLM, not the agent's LLM
        super().__init__(
            instructions="You collect customer profile information using sequential tasks. The tasks handle all communication.",
            chat_ctx=chat_ctx,
        )
    
    async def on_enter(self) -> None:
        """Called when agent starts - run profile collection tasks sequentially."""
        # Create TaskGroup for sequential profile collection
        task_group = TaskGroup()
        
        task_group.add(
            lambda: NameTask(),
            id="name_task",
            description="Collects customer's full name"
        )
        
        task_group.add(
            lambda: PhoneTask(),
            id="phone_task",
            description="Collects phone number with confirmation"
        )
        
        task_group.add(
            lambda: AgeTask(),
            id="age_task",
            description="Collects age and detects if minor"
        )
        
        task_group.add(
            lambda: GetEmailTask(),
            id="email_task",
            description="Collects email address"
        )
        
        task_group.add(
            lambda: ExperienceTask(),
            id="experience_task",
            description="Collects surfing experience level"
        )
        
        # Execute all tasks sequentially
        # Note: This will wait for user input for each task
        results = await task_group
        task_results = results.task_results
        
        # Update userdata from task results
        userdata = self.session.userdata
        userdata.name = task_results["name_task"].name
        userdata.phone = task_results["phone_task"].phone
        userdata.age = task_results["age_task"].age
        userdata.is_minor = task_results["age_task"].is_minor
        userdata.email = task_results["email_task"].email_address
        userdata.experience_level = task_results["experience_task"].experience_level
        
        await self.session.say(
            f"Perfect, {userdata.name}! I've got your contact info and experience level. "
            "Let me help you find the best time for your lesson."
        )
        
        # Transfer to scheduler agent with chat context
        from agents.scheduler_agent import SchedulerAgent
        self.session.update_agent(SchedulerAgent(chat_ctx=self.chat_ctx))

