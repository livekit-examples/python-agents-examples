"""
---
title: Education Avatar
category: avatars
tags: [avatar, openai, deepgram, hedra]
difficulty: advanced
description: Shows how to create an avatar that can help a user learn about the Fall of the Roman Empire using flash cards and quizzes.
demonstrates:
  - Creating a new hedra avatar session using a custom image
  - Using RPC to send messages to the client for flash cards and quizzes using `perform_rpc`
  - Using `register_rpc_method` to register the RPC methods so that the agent can receive messages from the client
  - Using UserData to store state for the cards and the quizzes
  - Using custom data classes to represent the flash cards and quizzes
---
"""
import logging
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, TypedDict
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, WorkerPermissions, RoomOutputOptions
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.plugins import openai, silero, deepgram, hedra, inworld
from PIL import Image
import asyncio
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("avatar")
logger.setLevel(logging.INFO)

class QuizAnswerDict(TypedDict):
    text: str
    is_correct: bool

class QuizQuestionDict(TypedDict):
    text: str
    answers: List[QuizAnswerDict]

@dataclass
class FlashCard:
    """Class to represent a flash card."""
    id: str
    question: str
    answer: str
    is_flipped: bool = False

@dataclass
class QuizAnswer:
    """Class to represent a quiz answer option."""
    id: str
    text: str
    is_correct: bool

@dataclass
class QuizQuestion:
    """Class to represent a quiz question."""
    id: str
    text: str
    answers: List[QuizAnswer]

@dataclass
class Quiz:
    """Class to represent a quiz."""
    id: str
    questions: List[QuizQuestion]

@dataclass
class UserData:
    """Class to store user data during a session."""
    ctx: Optional[JobContext] = None
    flash_cards: List[FlashCard] = field(default_factory=list)
    quizzes: List[Quiz] = field(default_factory=list)

    def reset(self) -> None:
        """Reset session data."""
        # Keep flash cards and quizzes intact

    def add_flash_card(self, question: str, answer: str) -> FlashCard:
        """Add a new flash card to the collection."""
        card = FlashCard(
            id=str(uuid.uuid4()),
            question=question,
            answer=answer
        )
        self.flash_cards.append(card)
        return card
    
    def get_flash_card(self, card_id: str) -> Optional[FlashCard]:
        """Get a flash card by ID."""
        for card in self.flash_cards:
            if card.id == card_id:
                return card
        return None
    
    def flip_flash_card(self, card_id: str) -> Optional[FlashCard]:
        """Flip a flash card by ID."""
        card = self.get_flash_card(card_id)
        if card:
            card.is_flipped = not card.is_flipped
            return card
        return None
        
    def add_quiz(self, questions: List[QuizQuestionDict]) -> Quiz:
        """Add a new quiz to the collection."""
        quiz_questions = []
        for q in questions:
            answers = []
            for a in q["answers"]:
                answers.append(QuizAnswer(
                    id=str(uuid.uuid4()),
                    text=a["text"],
                    is_correct=a["is_correct"]
                ))
            quiz_questions.append(QuizQuestion(
                id=str(uuid.uuid4()),
                text=q["text"],
                answers=answers
            ))
        
        quiz = Quiz(
            id=str(uuid.uuid4()),
            questions=quiz_questions
        )
        self.quizzes.append(quiz)
        return quiz
    
    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get a quiz by ID."""
        for quiz in self.quizzes:
            if quiz.id == quiz_id:
                return quiz
        return None
    
    def check_quiz_answers(self, quiz_id: str, user_answers: dict) -> List[tuple]:
        """Check user's quiz answers and return results."""
        quiz = self.get_quiz(quiz_id)
        if not quiz:
            return []
        
        results = []
        for question in quiz.questions:
            user_answer_id = user_answers.get(question.id)
            
            # Find the selected answer and the correct answer
            selected_answer = None
            correct_answer = None
            
            for answer in question.answers:
                if answer.id == user_answer_id:
                    selected_answer = answer
                if answer.is_correct:
                    correct_answer = answer
            
            is_correct = selected_answer and selected_answer.is_correct
            results.append((question, selected_answer, correct_answer, is_correct))
        
        return results

class AvatarAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are also a helpful, patient, and curious study partner for a student learning about the Fall of the Roman Empire.
                Your primary goal is to foster deep understanding through guided discovery, dialogue, and repetition.

                Your responsibilities include:
                    •	Explaining core topics related to the Fall of the Roman Empire, including:
                    •	Economic factors (currency devaluation, overtaxation, wealth inequality)
                    •	Military decline (barbarian invasions, loss of discipline, mercenary reliance)
                    •	Political instability (succession crises, civil wars, corruption)
                    •	Administrative challenges (East-West division, bureaucratic bloat)
                    •	Social and cultural changes (spread of Christianity, shifting values)
                    •	External pressures (Germanic tribes, Huns, Sassanid Persians)
                    •	Environmental factors (climate change, plagues, agricultural decline)
                    •	Using Socratic questioning to help the student reach answers themselves.
                    •	Providing clear explanations only when necessary, then quizzing the student on similar historical questions.
                    •	Alternating between roles: sometimes you ask questions, other times you answer.
                    •	Prioritizing reinforcement through follow-up questions that vary in difficulty and context.
                    •	Maintaining a friendly, encouraging tone that supports confidence and curiosity.

                Do not rush to give the answer. Instead, support reasoning, analytical thinking, and the development of historical understanding.

                It's very important that you remember you are having this talk via voice. You should use clear language and be specific about dates, names, and events related to the Fall of Rome (roughly 376-476 CE, though the Eastern Roman Empire continued until 1453 CE).

                Always start answering a question by first asking questions, try to use the socratic method until it seems like you're both stuck.

                FLASH CARDS FEATURE:4
                You can create flash cards to help the user learn and remember important concepts. Use the create_flash_card function
                to create a new flash card with a question and answer. The flash card will appear beside you in the UI.
                
                Be proactive in creating flash cards for important concepts, especially when:
                - Teaching new vocabulary or terminology
                - Explaining complex principles that are worth remembering
                - Summarizing key points from a discussion
                
                For example, when explaining the causes of the Fall of Rome, you might create a flash card with:
                Question: "What year marks the traditional end of the Western Roman Empire?"
                Answer: "476 CE, when the last Roman Emperor Romulus Augustulus was deposed by Odoacer, the Germanic king."

                Do not tell the user the answer before they look at it!
                
                You can also flip flash cards to show the answer using the flip_flash_card function.
                
                QUIZ FEATURE:
                You can create multiple-choice quizzes to test the user's knowledge. Use the create_quiz function
                to create a new quiz with questions and multiple-choice answers. The quiz will appear on the left side of the UI.
                
                For each question, you should provide:
                - A clear question text
                - 3-5 answer options (one must be marked as correct)
                
                Quizzes are great for:
                - Testing comprehension after explaining a concept
                - Reviewing previously covered material
                - Preparing the user for a test or exam
                - Breaking up longer learning sessions with interactive elements
                
                When the user submits their answers, you'll automatically provide verbal feedback on their performance.
                Don't just read back the questions and answers, give some color commentary that makes it interesting. Use names, 
                dates, or other interesting facts about the question to root it in memory.
                For any incorrectly answered questions, flash cards will be created to help them study the correct answers.
                
                Example format for creating a quiz:
                ```python
                await self.create_quiz([
                    {
                        "text": "What year marks the traditional end of the Western Roman Empire?",
                        "answers": [
                            {"text": "410 CE", "is_correct": False},
                            {"text": "476 CE", "is_correct": True},
                            {"text": "527 CE", "is_correct": False},
                            {"text": "1453 CE", "is_correct": False}
                        ]
                    },
                    {
                        "text": "Who was the last Western Roman Emperor?",
                        "answers": [
                            {"text": "Constantine", "is_correct": False},
                            {"text": "Theodosius", "is_correct": False},
                            {"text": "Romulus Augustulus", "is_correct": True},
                            {"text": "Justinian", "is_correct": False}
                        ]
                    }
                ])
                ```
                
                Start the interaction with a short introduction, and let the student
                guide their own learning journey!

                Keep your speaking turns short, only one or two sentences. We want the
                student to do most of the speaking.
            """,
            stt="assemblyai/universal-streaming",
            llm=openai.LLM(model="gpt-4o"),
            tts=inworld.TTS(
                voice="Hades"
            ),
            vad=silero.VAD.load(),
        )

    @function_tool
    async def create_flash_card(self, context: RunContext[UserData], question: str, answer: str):
        """Create a new flash card and display it to the user.

        Args:
            question: The question or front side of the flash card
            answer: The answer or back side of the flash card
        """
        userdata = context.userdata
        card = userdata.add_flash_card(question, answer)
        
        # Get the room from the userdata
        if not userdata.ctx or not userdata.ctx.room:
            return f"Created a flash card, but couldn't access the room to send it."
        
        room = userdata.ctx.room
        
        # Get the first participant in the room (should be the client)
        participants = room.remote_participants
        if not participants:
            return f"Created a flash card, but no participants found to send it to."
        
        # Get the first participant from the dictionary of remote participants
        participant = next(iter(participants.values()), None)
        if not participant:
            return f"Created a flash card, but couldn't get the first participant."
        payload = {
            "action": "show",
            "id": card.id,
            "question": card.question,
            "answer": card.answer,
            "index": len(userdata.flash_cards) - 1
        }
        
        # Make sure payload is properly serialized
        json_payload = json.dumps(payload)
        logger.info(f"Sending flash card payload: {json_payload}")
        await room.local_participant.perform_rpc(
            destination_identity=participant.identity,
            method="client.flashcard",
            payload=json_payload
        )
        
        return f"I've created a flash card with the question: '{question}'"

    @function_tool
    async def flip_flash_card(self, context: RunContext[UserData], card_id: str):
        """Flip a flash card to show the answer or question.

        Args:
            card_id: The ID of the flash card to flip
        """
        userdata = context.userdata
        card = userdata.flip_flash_card(card_id)
        
        if not card:
            return f"Flash card with ID {card_id} not found."
        
        # Get the room from the userdata
        if not userdata.ctx or not userdata.ctx.room:
            return f"Flipped the flash card, but couldn't access the room to send it."
        
        room = userdata.ctx.room
        
        # Get the first participant in the room (should be the client)
        participants = room.remote_participants
        if not participants:
            return f"Flipped the flash card, but no participants found to send it to."
        
        # Get the first participant from the dictionary of remote participants
        participant = next(iter(participants.values()), None)
        if not participant:
            return f"Flipped the flash card, but couldn't get the first participant."
        payload = {
            "action": "flip",
            "id": card.id
        }
        
        # Make sure payload is properly serialized
        json_payload = json.dumps(payload)
        logger.info(f"Sending flip card payload: {json_payload}")
        await room.local_participant.perform_rpc(
            destination_identity=participant.identity,
            method="client.flashcard",
            payload=json_payload
        )
        
        return f"I've flipped the flash card to show the {'answer' if card.is_flipped else 'question'}"
    
    @function_tool
    async def create_quiz(self, context: RunContext[UserData], questions: List[QuizQuestionDict]):
        """Create a new quiz with multiple choice questions and display it to the user.
        
        Args:
            questions: A list of question objects. Each question object should have:
                - text: The question text
                - answers: A list of answer objects, each with:
                    - text: The answer text
                    - is_correct: Boolean indicating if this is the correct answer
        """
        userdata = context.userdata
        quiz = userdata.add_quiz(questions)
        
        # Get the room from the userdata
        if not userdata.ctx or not userdata.ctx.room:
            return f"Created a quiz, but couldn't access the room to send it."
        
        room = userdata.ctx.room
        
        # Get the first participant in the room (should be the client)
        participants = room.remote_participants
        if not participants:
            return f"Created a quiz, but no participants found to send it to."
        
        # Get the first participant from the dictionary of remote participants
        participant = next(iter(participants.values()), None)
        if not participant:
            return f"Created a quiz, but couldn't get the first participant."
        
        # Format questions for client
        client_questions = []
        for q in quiz.questions:
            client_answers = []
            for a in q.answers:
                client_answers.append({
                    "id": a.id,
                    "text": a.text
                })
            client_questions.append({
                "id": q.id,
                "text": q.text,
                "answers": client_answers
            })
        
        payload = {
            "action": "show",
            "id": quiz.id,
            "questions": client_questions
        }
        
        # Make sure payload is properly serialized
        json_payload = json.dumps(payload)
        logger.info(f"Sending quiz payload: {json_payload}")
        await room.local_participant.perform_rpc(
            destination_identity=participant.identity,
            method="client.quiz",
            payload=json_payload
        )
        
        return f"I've created a quiz with {len(questions)} questions. Please answer them when you're ready."

    async def on_enter(self):
        await asyncio.sleep(5)
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    agent = AvatarAgent()
    await ctx.connect()

    # Create a single AgentSession with userdata
    userdata = UserData(ctx=ctx)
    session = AgentSession[UserData](
        userdata=userdata, 
        turn_detection=EnglishModel()
    )

    # Load the avatar image
    avatar_dir = os.path.dirname(os.path.abspath(__file__))
    avatar_image_path = os.path.join(avatar_dir, 'avatar.png')
    
    if not os.path.exists(avatar_image_path):
        raise FileNotFoundError(f"Avatar image not found at {avatar_image_path}")
    
    avatar_image = Image.open(avatar_image_path)
    
    # Create the avatar session
    avatar = hedra.AvatarSession(
        avatar_participant_identity="education-avatar",
        avatar_image=avatar_image
    )

    # Register RPC method for flipping flash cards from client
    async def handle_flip_flash_card(rpc_data):
        try:
            logger.info(f"Received flash card flip payload: {rpc_data}")
            
            # Extract the payload from the RpcInvocationData object
            payload_str = rpc_data.payload
            logger.info(f"Extracted payload string: {payload_str}")
            
            # Parse the JSON payload
            payload_data = json.loads(payload_str)
            logger.info(f"Parsed payload data: {payload_data}")
            
            card_id = payload_data.get("id")
            
            if card_id:
                card = userdata.flip_flash_card(card_id)
                if card:
                    logger.info(f"Flipped flash card {card_id}, is_flipped: {card.is_flipped}")
                    # Send a message to the user via the agent, we're disabling this for now.
                    # session.generate_reply(user_input=(f"Please describe the {'answer' if card.is_flipped else 'question'}"))
                else:
                    logger.error(f"Card with ID {card_id} not found")
            else:
                logger.error("No card ID found in payload")
                
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for payload '{rpc_data.payload}': {e}")
            return f"error: {str(e)}"
        except Exception as e:
            logger.error(f"Error handling flip flash card: {e}")
            return f"error: {str(e)}"
    
    # Register RPC method for handling quiz submissions
    async def handle_submit_quiz(rpc_data):
        try:
            logger.info(f"Received quiz submission payload: {rpc_data}")
            
            # Extract the payload from the RpcInvocationData object
            payload_str = rpc_data.payload
            logger.info(f"Extracted quiz submission string: {payload_str}")
            
            # Parse the JSON payload
            payload_data = json.loads(payload_str)
            logger.info(f"Parsed quiz submission data: {payload_data}")
            
            quiz_id = payload_data.get("id")
            user_answers = payload_data.get("answers", {})
            
            if not quiz_id:
                logger.error("No quiz ID found in payload")
                return "error: No quiz ID found in payload"
                
            # Check the quiz answers
            quiz_results = userdata.check_quiz_answers(quiz_id, user_answers)
            if not quiz_results:
                logger.error(f"Quiz with ID {quiz_id} not found")
                return "error: Quiz not found"
            
            # Count correct answers
            correct_count = sum(1 for _, _, _, is_correct in quiz_results if is_correct)
            total_count = len(quiz_results)
            
            # Create a verbal response for the agent to say
            result_summary = f"You got {correct_count} out of {total_count} questions correct."
            
            # Generate feedback for each question
            feedback_details = []
            for question, selected_answer, correct_answer, is_correct in quiz_results:
                if is_correct:
                    feedback = f"Question: {question.text}\nYour answer: {selected_answer.text} ✓ Correct!"
                else:
                    feedback = f"Question: {question.text}\nYour answer: {selected_answer.text if selected_answer else 'None'} ✗ Incorrect. The correct answer is: {correct_answer.text}"
                    
                    # Create a flash card for incorrectly answered questions
                    card = userdata.add_flash_card(question.text, correct_answer.text)
                    participant = next(iter(ctx.room.remote_participants.values()), None)
                    if participant:
                        flash_payload = {
                            "action": "show",
                            "id": card.id,
                            "question": card.question,
                            "answer": card.answer,
                            "index": len(userdata.flash_cards) - 1
                        }
                        json_flash_payload = json.dumps(flash_payload)
                        await ctx.room.local_participant.perform_rpc(
                            destination_identity=participant.identity,
                            method="client.flashcard",
                            payload=json_flash_payload
                        )
                
                feedback_details.append(feedback)
            
            detailed_feedback = "\n\n".join(feedback_details)
            full_response = f"{result_summary}\n\n{detailed_feedback}"
            
            # Have the agent say the results
            session.say(full_response)
            
            return "success"
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for quiz submission payload '{rpc_data.payload}': {e}")
            return f"error: {str(e)}"
        except Exception as e:
            logger.error(f"Error handling quiz submission: {e}")
            return f"error: {str(e)}"
    
    # Register RPC methods - The method names need to match exactly what the client is calling
    logger.info("Registering RPC methods")
    ctx.room.local_participant.register_rpc_method(
        "agent.flipFlashCard",
        handle_flip_flash_card
    )
    
    ctx.room.local_participant.register_rpc_method(
        "agent.submitQuiz",
        handle_submit_quiz
    )

    # Start the avatar with the same session that has userdata
    await avatar.start(session, room=ctx.room)

    # Start the agent session with the same session object
    await session.start(
        room=ctx.room,
        room_output_options=RoomOutputOptions(
            audio_enabled=True,  # Enable audio since we want the avatar to speak
        ),
        agent=agent
    )

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )
