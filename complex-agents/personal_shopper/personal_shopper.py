"""
---
title: Personal Shopper Multi-Agent
category: complex-agents
tags: [customer_database, multi_agent_transfer, order_management, customer_identification]
difficulty: advanced
description: E-commerce personal shopper with triage, sales, and returns departments
demonstrates:
  - Customer identification and database management
  - Three specialized agents with different responsibilities
  - Order creation and management with pricing
  - Order history retrieval for returns
  - Context-aware agent transfers with personalization
  - Customer database with order tracking
  - Persistent customer data across sessions
---
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins import noise_cancellation

from utils import load_prompt
from database import CustomerDatabase

logger = logging.getLogger("personal-shopper")
logger.setLevel(logging.INFO)

load_dotenv()

# Initialize the customer database
db = CustomerDatabase()

@dataclass
class UserData:
    """Class to store user data and agents during a call."""
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None

    # Customer information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    customer_id: Optional[str] = None
    current_order: Optional[dict] = None

    def is_identified(self) -> bool:
        """Check if the customer is identified."""
        return self.first_name is not None and self.last_name is not None

    def reset(self) -> None:
        """Reset customer information."""
        self.first_name = None
        self.last_name = None
        self.customer_id = None
        self.current_order = None

    def summarize(self) -> str:
        """Return a summary of the user data."""
        if self.is_identified():
            return f"Customer: {self.first_name} {self.last_name} (ID: {self.customer_id})"
        return "Customer not yet identified."

RunContext_T = RunContext[UserData]

class BaseAgent(Agent):
    async def on_enter(self) -> None:
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({"agent": agent_name})

        # Create a personalized prompt based on customer identification
        custom_instructions = self.instructions
        if userdata.is_identified():
            custom_instructions += f"\n\nYou are speaking with {userdata.first_name} {userdata.last_name}."

        chat_ctx = self.chat_ctx.copy()

        # Copy context from previous agent if it exists
        if userdata.prev_agent:
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, keep_function_call=True
            )
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        chat_ctx.add_message(
            role="system",
            content=f"You are the {agent_name}. {userdata.summarize()}"
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply()

    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 6,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        """Truncate the chat context to keep the last n messages."""
        def _valid_item(item) -> bool:
            if not keep_system_message and item.type == "message" and item.role == "system":
                return False
            if not keep_function_call and item.type in ["function_call", "function_call_output"]:
                return False
            return True

        new_items = []
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]

        while new_items and new_items[0].type in ["function_call", "function_call_output"]:
            new_items.pop(0)

        return new_items

    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
        """Transfer to another agent while preserving context."""
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent

        return next_agent


class TriageAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('triage_prompt.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def identify_customer(self, first_name: str, last_name: str):
        """
        Identify a customer by their first and last name.

        Args:
            first_name: The customer's first name
            last_name: The customer's last name
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.customer_id = db.get_or_create_customer(first_name, last_name)

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def transfer_to_sales(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Sales team who can help you find the perfect product."
        else:
            message = "I'll transfer you to our Sales team who can help you find the perfect product."

        await self.session.say(message)
        return await self._transfer_to_agent("sales", context)

    @function_tool
    async def transfer_to_returns(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Returns department who can assist with your return or exchange."
        else:
            message = "I'll transfer you to our Returns department who can assist with your return or exchange."

        await self.session.say(message)
        return await self._transfer_to_agent("returns", context)


class SalesAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('sales_prompt.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def identify_customer(self, first_name: str, last_name: str):
        """
        Identify a customer by their first and last name.

        Args:
            first_name: The customer's first name
            last_name: The customer's last name
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.customer_id = db.get_or_create_customer(first_name, last_name)

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def start_order(self):
        """Start a new order for the customer."""
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        userdata.current_order = {
            "items": []
        }

        return "I've started a new order for you. What would you like to purchase?"

    @function_tool
    async def add_item_to_order(self, item_name: str, quantity: int, price: float):
        """
        Add an item to the current order.

        Args:
            item_name: The name of the item
            quantity: The quantity to purchase
            price: The price per item
        """
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        if not userdata.current_order:
            userdata.current_order = {"items": []}

        item = {
            "name": item_name,
            "quantity": quantity,
            "price": price
        }

        userdata.current_order["items"].append(item)

        return f"Added {quantity}x {item_name} to your order."

    @function_tool
    async def complete_order(self):
        """Complete the current order and save it to the database."""
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        if not userdata.current_order or not userdata.current_order.get("items"):
            return "There are no items in the current order."

        # Calculate order total
        total = sum(item["price"] * item["quantity"] for item in userdata.current_order["items"])
        userdata.current_order["total"] = total

        # Save order to database
        order_id = db.add_order(userdata.customer_id, userdata.current_order)

        # Create a summary of the order
        summary = f"Order #{order_id} has been completed. Total: ${total:.2f}\n"
        summary += "Items:\n"
        for item in userdata.current_order["items"]:
            summary += f"- {item['quantity']}x {item['name']} (${item['price']} each)\n"

        # Reset the current order
        userdata.current_order = None

        return summary

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Triage agent who can better direct your inquiry."
        else:
            message = "I'll transfer you back to our Triage agent who can better direct your inquiry."

        await self.session.say(message)
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def transfer_to_returns(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Returns department for assistance with your return request."
        else:
            message = "I'll transfer you to our Returns department for assistance with your return request."

        await self.session.say(message)
        return await self._transfer_to_agent("returns", context)


class ReturnsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('returns_prompt.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def identify_customer(self, first_name: str, last_name: str):
        """
        Identify a customer by their first and last name.

        Args:
            first_name: The customer's first name
            last_name: The customer's last name
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.customer_id = db.get_or_create_customer(first_name, last_name)

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def get_order_history(self):
        """Get the order history for the current customer."""
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        order_history = db.get_customer_order_history(userdata.first_name, userdata.last_name)
        return order_history

    @function_tool
    async def process_return(self, order_id: int, item_name: str, reason: str):
        """
        Process a return for an item from a specific order.

        Args:
            order_id: The ID of the order containing the item to return
            item_name: The name of the item to return
            reason: The reason for the return
        """
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        # In a real system, we would update the order in the database
        # For this example, we'll just return a confirmation message
        return f"Return processed for {item_name} from Order #{order_id}. Reason: {reason}. A refund will be issued within 3-5 business days."

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Triage agent who can better direct your inquiry."
        else:
            message = "I'll transfer you back to our Triage agent who can better direct your inquiry."

        await self.session.say(message)
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def transfer_to_sales(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Sales team who can help you find new products."
        else:
            message = "I'll transfer you to our Sales team who can help you find new products."

        await self.session.say(message)
        return await self._transfer_to_agent("sales", context)


async def entrypoint(ctx: JobContext):
    # Initialize user data with context
    userdata = UserData(ctx=ctx)

    # Create agent instances
    triage_agent = TriageAgent()
    sales_agent = SalesAgent()
    returns_agent = ReturnsAgent()

    # Register all agents in the userdata
    userdata.personas.update({
        "triage": triage_agent,
        "sales": sales_agent,
        "returns": returns_agent
    })

    # Create session with userdata
    session = AgentSession[UserData](userdata=userdata)

    await session.start(
        agent=triage_agent,  # Start with the Triage agent
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
