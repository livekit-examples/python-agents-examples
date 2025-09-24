""" 
---
title: Shopify Voice Shopping Agent
category: complex-agents
tags: [mcp_server, shopify, dynamic_agent_switching, rpc_navigation, fast_llm_response]
difficulty: advanced
description: Voice shopping assistant for Shopify stores with MCP server integration
demonstrates:
  - MCP server integration for Shopify operations
  - Dynamic shop switching with agent updates
  - RPC navigation to frontend browser
  - Fast LLM for quick acknowledgments
  - Voice-optimized response formatting
  - Factory pattern for agent creation
  - Shop URL handling and validation
---
"""

import logging
import os
import asyncio
import random
from typing import AsyncIterable
from dotenv import load_dotenv
from pathlib import Path
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, mcp
from livekit.agents.llm import function_tool, ChatChunk, FunctionTool
from livekit.agents.llm.chat_context import ChatContext, ChatMessage
from livekit.agents.voice import RunContext, ModelSettings
import json
from livekit.plugins import speechmatics, openai, silero, cartesia
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from dataclasses import dataclass
import urllib.parse

logger = logging.getLogger("mcp-agent")

load_dotenv()

@dataclass
class ShopifyUserData:
    ctx: JobContext
    session: AgentSession = None
    first_run: bool = True
    currently_shopping: bool = False

def create_shopify_agent(shopify_mcp_url: str) -> Agent:
    """Factory function to create an agent with a specific Shopify MCP server URL"""

    class ShopifyAgent(Agent):
        def __init__(self, mcp_url: str) -> None:
            super().__init__(
                instructions=(
                    f"""
                    You are a shopping assistant, you have access to a shopify MCP server to do things like search for products, add to cart, etc.

                    Current shop MCP URL: {mcp_url}

                    # Your tone
                    - You are a friendly sales assistant, not a robot.
                    - Try to use contractions, slang, and other informal language to make the
                      user feel like you're a real person.
                    - Don't use the product name over and over again. That's robotic. If the product name is already
                      referenced in a previous message, don't repeat it. You can use "it" or "this" to refer to the product if appropriate.

                    ## How to respond
                    - The interface is voice-based: This means that everything you return will be spoken to the user.
                    - Don't return any markdown or other formatting, it won't make sense when spoken aloud.
                    - Lists should be comma-separated, not bullet points.
                    - If you're returning a list of items, just say the name of the item and the price unless asked for more information.
                        - Round prices to the nearest dollar, don't include cents.
                        - If you're going to list multiple products, show the user the one that you think is the best fit, then list the rest.
                    - Act like a friendly sales assistant, not a robot.
                    - Like a sales assistant, proactively show the user products. If they say something like,
                      "I want a warm winter coat", you can show them a warm winter coat. Don't just talk about the product, show it to them.
                    - Always say websites like "dot C A" or "dot com" when referring to a website outside of tool calls.

                    ## Showing products
                    - If you want to show a user something, you can send a URL to the frontend for display.
                    - This will navigate the user's browser to the URL.
                    - You have access to the "send_url_to_frontend" function that will navigate the user's browser to the URL.
                    - Don't say things like "I'm showing you a product" or "I'm showing you a list of products",
                      just show the product and assume the user has seen it. This is how a sales associate would do it.


                    ## Switching shops
                    - You can switch shops by calling the "switch_shop" function.
                    - This will switch the shop that you are browsing.
                    - Not all shops end in .myshopify.com, some people will have custom domains like .com or .ca
                    """
                ),
                mcp_servers=[
                    mcp.MCPServerHTTP(
                        url=mcp_url,
                        timeout=30,
                        client_session_timeout_seconds=10
                    ),
                ] if mcp_url else None,
            )
            self.fast_llm = openai.LLM(model="gpt-4.1-nano")

        async def on_enter(self):
            if hasattr(self, 'session') and self.session.userdata and self.session.userdata.first_run:
                self.session.say("Hey! Let's find you something to buy!")
                self.session.userdata.first_run = False
            pass

        async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
            logger.info(f"User turn completed: {new_message.content}")
            if self.session.userdata and self.session.userdata.currently_shopping:
                search_ctx = ChatContext([
                    ChatMessage(
                        type="message",
                        role="system",
                        content=["""
                                You are a digital shopkeeper. If you need to find a product,
                                say a little quip in a few words about looking for it.
                                A few words only.
                                Never respond with a question. Just a little friendly confirmation.
                                """]
                    ),
                    ChatMessage(type="message", role="user", content=[f"The user says: {new_message.content}"])
                ])
                response = ""
                async with self.fast_llm.chat(chat_ctx=search_ctx) as stream:
                    async for chunk in stream:
                        if not chunk:
                            continue
                        content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                        if content:
                            response += content
                self.session.say(response.strip())
            return await super().on_user_turn_completed(turn_ctx, new_message)

        async def _send_url_to_frontend_internal(self, userdata: ShopifyUserData, url: str) -> str:
            """
            Internal method to send a URL to the frontend via RPC.

            Args:
                userdata: The ShopifyUserData containing the JobContext
                url: The URL to send to the frontend

            Returns:
                String message indicating success or failure
            """
            payload = {
                "url": url
            }

            try:
                if not userdata or not userdata.ctx:
                    logger.error("JobContext not found in UserData")
                    return "Error: JobContext not available to send RPC."

                room = userdata.ctx.room
                if not room:
                    logger.error("Room object not found in JobContext")
                    return "Error: Room object not available to send RPC."

                remote_participants = list(room.remote_participants.values())
                if not remote_participants:
                    logger.error("No remote participants found to send RPC 'client.navigate'.")
                    return "Error: No client found in the room to send the URL to."

                client_participant = remote_participants[0]

                await room.local_participant.perform_rpc(
                    destination_identity=client_participant.identity,
                    method="client.navigate",
                    payload=json.dumps(payload)
                )
                logger.info(f"Sent RPC 'client.navigate' to frontend ({client_participant.identity}) with URL: {url}")
                return f"Successfully sent URL {url} to the frontend via RPC."
            except Exception as e:
                logger.error(f"Failed to send RPC 'client.navigate' to frontend: {e}")
                return f"Error sending URL to frontend via RPC: {str(e)}"

        @function_tool
        async def send_url_to_frontend(self, context: RunContext[ShopifyUserData], url: str):
            """
            Sends a URL to the frontend for display via an RPC call. The frontend
            should have an RPC handler registered for "client.navigate". The payload
            will be a JSON object: {"url": "your_url_here"}.

            Args:
                url: The URL to send to the frontend.
            """
            return await self._send_url_to_frontend_internal(context.userdata, url)

        @function_tool
        async def switch_shop(self, context: RunContext[ShopifyUserData], shop_url: str):
            """
            Switch to a different Shopify shop by updating the MCP server URL.
            This URL does not have to my a .myshopify.com URL, some people will have custom domains.

            Args:
                shop_url: The new Shopify MCP server URL to connect to.
            """
            try:
                new_agent = create_shopify_agent(shop_url)

                if context.userdata and context.userdata.session:
                    context.userdata.session.update_agent(new_agent)
                    logger.info(f"Successfully switched to shop with MCP URL: {shop_url}")

                    parsed_url = urllib.parse.urlparse(shop_url)
                    base_shop_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

                    await self._send_url_to_frontend_internal(context.userdata, base_shop_url)
                    context.userdata.currently_shopping = True

                    return f"Successfully switched to the new shop. I'm now showing you their homepage."
                else:
                    logger.error("Session not found in UserData")
                    return "Error: Could not switch shops - session not available."

            except Exception as e:
                logger.error(f"Failed to switch shop to {shop_url}: {e}")
                return f"Error switching to the new shop: {str(e)}"

    return ShopifyAgent(shopify_mcp_url)

async def entrypoint(ctx: JobContext):
    userdata = ShopifyUserData(ctx=ctx)

    session = AgentSession[ShopifyUserData](
        userdata=userdata,
        vad=silero.VAD.load(),
        stt=speechmatics.STT(),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=cartesia.TTS(voice="da69d796-4603-4419-8a95-293bfc5679eb"),
        turn_detection=MultilingualModel(),
        mcp_servers=[],
    )

    userdata.session = session

    initial_mcp_url = os.environ.get("SHOPIFY_MCP_URL")
    initial_agent = create_shopify_agent(initial_mcp_url)

    await session.start(agent=initial_agent, room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))