"""
---
title: Nutrition Tracker Assistant
category: complex-agents
tags: [sqlite_database, nutrition, food_tracking, rpc_updates, thread_pool]
difficulty: advanced
description: Nutrition tracking assistant with SQLite database and real-time updates
demonstrates:
  - SQLite database for persistent food tracking
  - Thread pool executor for non-blocking database operations
  - Nutritional data calculation and aggregation
  - RPC updates to frontend for live nutrition display
  - Daily summaries and food consumption history
  - Fixed participant identity for testing
  - Initial data sync on connection
---
"""

from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
from livekit.agents.llm import function_tool
from livekit import agents
from livekit.agents.voice import AgentSession, Agent, RunContext, room_io
from livekit.plugins import (
    openai,
    silero,
    noise_cancellation
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Database file path
DB_PATH = Path(__file__).parent / "nutrition_tracker.db"

# Thread pool for database operations
db_executor = ThreadPoolExecutor(max_workers=1)

# Fixed participant identity for testing
FIXED_PARTICIPANT_ID = "test_user"


def init_database():
    """Initialize the SQLite database with the required schema."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_consumptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_name TEXT NOT NULL,
            participant_identity TEXT NOT NULL,
            consumed_at TIMESTAMP NOT NULL,
            calories REAL,
            protein REAL,
            carbs REAL,
            fats REAL
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_participant_date 
        ON food_consumptions(participant_identity, consumed_at)
    """)
    
    conn.commit()
    
    # Debug: Check what's in the database
    cursor.execute("SELECT COUNT(*) FROM food_consumptions")
    count = cursor.fetchone()[0]
    print(f"Database initialized. Total food records: {count}")
    
    # Show recent entries
    cursor.execute("""
        SELECT participant_identity, food_name, consumed_at 
        FROM food_consumptions 
        ORDER BY consumed_at DESC 
        LIMIT 5
    """)
    recent = cursor.fetchall()
    if recent:
        print("Recent food entries:")
        for row in recent:
            print(f"  {row[0]}: {row[1]} at {row[2]}")
    
    conn.close()


@dataclass
class NutritionUserData:
    participant_identity: str
    ctx: agents.JobContext = None


class NutritionAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
            You are a helpful assistant who helps track food consumption. Your job is to:
            1. Record what foods the user has eaten
            2. Track nutritional information when available (calories, protein, carbs, fats)
            3. Provide daily summaries of nutrition intake
            4. Be encouraging and supportive about healthy eating habits

            When users tell you what they've eaten, use the consumed_food tool to record it.
            If they don't provide specific nutritional information, make your best guess as to what the nutritional information in.
            Never log anything without nutritional information attached to it.
            Always confirm what you've recorded after logging their food.
        """)

    @function_tool
    async def consumed_food(self, context: RunContext[NutritionUserData],
                          food_name: str,
                          calories: Optional[float] = None,
                          protein: Optional[float] = None,
                          carbs: Optional[float] = None,
                          fats: Optional[float] = None):
        """
        Record food consumption in the database.

        Args:
            food_name: The name of the food consumed
            calories: The number of calories in the food
            protein: Grams of protein in the food
            carbs: Grams of carbohydrates in the food
            fats: Grams of fat in the food
        """
        print(f"Recording consumption of {food_name}")
        
        try:
            # Run database operation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                db_executor,
                self._insert_food_consumption,
                context.userdata.participant_identity,
                food_name,
                calories,
                protein,
                carbs,
                fats
            )
            
            # Build nutrition info string
            nutrition_parts = []
            if calories is not None:
                nutrition_parts.append(f"{calories} calories")
            if protein is not None:
                nutrition_parts.append(f"{protein}g protein")
            if carbs is not None:
                nutrition_parts.append(f"{carbs}g carbs")
            if fats is not None:
                nutrition_parts.append(f"{fats}g fat")
            
            nutrition_info = ", ".join(nutrition_parts)
            
            # Print for debugging
            await self._print_daily_summary_async(context)
            
            # Send nutrition update via RPC
            await self._send_nutrition_update(context)
            
            if nutrition_info:
                return f"I've recorded that you ate {food_name} ({nutrition_info})."
            else:
                return f"I've recorded that you ate {food_name}."
            
        except Exception as error:
            print(f"Error recording food consumption: {error}")
            return "Failed to record food consumption"

    def _insert_food_consumption(self, participant_identity: str, food_name: str,
                               calories: Optional[float], protein: Optional[float],
                               carbs: Optional[float], fats: Optional[float]):
        """Insert food consumption record into database (runs in thread)."""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO food_consumptions 
            (food_name, participant_identity, consumed_at, calories, protein, carbs, fats)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (food_name, participant_identity, datetime.now(), calories, protein, carbs, fats))
        
        conn.commit()
        conn.close()

    @function_tool
    async def get_daily_calories(self, context: RunContext[NutritionUserData]):
        """
        Get the total calories and macronutrients consumed today.
        """
        try:
            # Run database query in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                db_executor,
                self._get_daily_totals,
                context.userdata.participant_identity
            )
            
            if not result['foods']:
                return "No food logged today."
            
            # Build response
            response_parts = [f"Today's totals: {result['totals']['calories']:.0f} calories"]
            if result['totals']['protein'] > 0:
                response_parts.append(f"{result['totals']['protein']:.1f}g protein")
            if result['totals']['carbs'] > 0:
                response_parts.append(f"{result['totals']['carbs']:.1f}g carbs")
            if result['totals']['fats'] > 0:
                response_parts.append(f"{result['totals']['fats']:.1f}g fat")
            
            # List foods consumed today
            response_parts.append(f"\n\nFoods consumed today: {', '.join(result['foods'])}")
            
            return ", ".join(response_parts[:4]) + response_parts[-1]
            
        except Exception as error:
            print(f"Error getting daily nutrition totals: {error}")
            return "Failed to get daily nutrition totals"

    def _get_daily_totals(self, participant_identity: str):
        """Get daily totals from database (runs in thread)."""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today_start.strftime('%Y-%m-%d')
        
        # Get totals
        cursor.execute("""
            SELECT 
                COALESCE(SUM(calories), 0) as total_calories,
                COALESCE(SUM(protein), 0) as total_protein,
                COALESCE(SUM(carbs), 0) as total_carbs,
                COALESCE(SUM(fats), 0) as total_fats
            FROM food_consumptions
            WHERE participant_identity = ? AND date(consumed_at) >= ?
        """, (participant_identity, today_str))
        
        row = cursor.fetchone()
        totals = {
            'calories': row[0] or 0,
            'protein': row[1] or 0,
            'carbs': row[2] or 0,
            'fats': row[3] or 0
        }
        
        # Get food list
        cursor.execute("""
            SELECT DISTINCT food_name
            FROM food_consumptions
            WHERE participant_identity = ? AND date(consumed_at) >= ?
            ORDER BY consumed_at
        """, (participant_identity, today_str))
        
        foods = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {'totals': totals, 'foods': foods}

    async def _send_nutrition_update(self, context: RunContext[NutritionUserData]):
        """Send current nutrition data to frontend via RPC."""
        try:
            if not context.userdata.ctx or not context.userdata.ctx.room:
                print("No room context available for RPC")
                return
                
            print(f"Sending nutrition update for participant: {context.userdata.participant_identity}")
            
            # Get today's data using existing method
            loop = asyncio.get_event_loop()
            daily_data = await loop.run_in_executor(
                db_executor,
                self._get_daily_totals,
                context.userdata.participant_identity
            )
            
            # Get detailed food list with timestamps
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_str = today_start.strftime('%Y-%m-%d')  # Use date format for consistency
            
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT food_name, consumed_at, calories, protein, carbs, fats
                FROM food_consumptions
                WHERE participant_identity = ? AND date(consumed_at) >= ?
                ORDER BY consumed_at DESC
            """, (context.userdata.participant_identity, today_str))
            
            rows = cursor.fetchall()
            conn.close()
            
            foods = []
            for row in rows:
                food_name, consumed_at, calories, protein, carbs, fats = row
                foods.append({
                    'food_name': food_name,
                    'consumed_at': consumed_at,
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fats': fats
                })
            
            # Send to frontend
            remote_participants = list(context.userdata.ctx.room.remote_participants.values())
            if remote_participants:
                client_participant = remote_participants[0]
                await context.userdata.ctx.room.local_participant.perform_rpc(
                    destination_identity=client_participant.identity,
                    method="nutrition.update",
                    payload=json.dumps({
                        'foods': foods,
                        'totals': daily_data['totals'],
                        'date': today_start.date().isoformat()
                    })
                )
                print(f"Sent nutrition update to frontend ({client_participant.identity})")
                print(f"  Foods: {len(foods)} items")
                print(f"  Totals: {daily_data['totals']}")
            else:
                print("No remote participants found to send nutrition update")
        except Exception as e:
            print(f"Error sending nutrition update: {e}")
            import traceback
            traceback.print_exc()

    async def _print_daily_summary_async(self, context: RunContext[NutritionUserData]):
        """Async wrapper for printing daily summary."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            db_executor,
            self._print_daily_summary,
            context.userdata.participant_identity
        )

    def _print_daily_summary(self, participant_identity: str):
        """Helper method to print the current day's consumption (runs in thread)."""
        print("\n=== Today's Food Consumption ===")
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today_start.strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT food_name, consumed_at, calories, protein, carbs, fats
            FROM food_consumptions
            WHERE participant_identity = ? AND date(consumed_at) >= ?
            ORDER BY consumed_at
        """, (participant_identity, today_str))
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No food logged today")
        else:
            totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
            
            for row in rows:
                food_name, consumed_at, calories, protein, carbs, fats = row
                time_str = datetime.fromisoformat(consumed_at).strftime("%H:%M")
                line = f"{time_str} - {food_name}"
                
                nutrition_parts = []
                if calories is not None:
                    nutrition_parts.append(f"{calories} cal")
                    totals['calories'] += calories
                if protein is not None:
                    nutrition_parts.append(f"{protein}g protein")
                    totals['protein'] += protein
                if carbs is not None:
                    nutrition_parts.append(f"{carbs}g carbs")
                    totals['carbs'] += carbs
                if fats is not None:
                    nutrition_parts.append(f"{fats}g fat")
                    totals['fats'] += fats
                
                if nutrition_parts:
                    line += f" ({', '.join(nutrition_parts)})"
                
                print(line)
            
            print(f"\nDaily Totals: {totals['calories']:.0f} calories, "
                  f"{totals['protein']:.1f}g protein, {totals['carbs']:.1f}g carbs, "
                  f"{totals['fats']:.1f}g fat")
        
        conn.close()
        print("================================\n")


async def send_initial_nutrition_update(ctx: agents.JobContext, participant_identity: str):
    """Send initial nutrition data when user connects."""
    try:
        print(f"Sending initial nutrition update for participant: {participant_identity}")
        
        # Get today's data - use date() to ensure we get all entries from today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today_start.strftime('%Y-%m-%d')  # Use date format instead of full ISO format
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get totals
        cursor.execute("""
            SELECT 
                COALESCE(SUM(calories), 0) as total_calories,
                COALESCE(SUM(protein), 0) as total_protein,
                COALESCE(SUM(carbs), 0) as total_carbs,
                COALESCE(SUM(fats), 0) as total_fats
            FROM food_consumptions
            WHERE participant_identity = ? AND date(consumed_at) >= ?
        """, (participant_identity, today_str))
        
        row = cursor.fetchone()
        totals = {
            'calories': row[0] or 0,
            'protein': row[1] or 0,
            'carbs': row[2] or 0,
            'fats': row[3] or 0
        }
        
        # Get detailed food list
        cursor.execute("""
            SELECT food_name, consumed_at, calories, protein, carbs, fats
            FROM food_consumptions
            WHERE participant_identity = ? AND date(consumed_at) >= ?
            ORDER BY consumed_at DESC
        """, (participant_identity, today_str))
        
        rows = cursor.fetchall()
        conn.close()
        
        foods = []
        for row in rows:
            food_name, consumed_at, calories, protein, carbs, fats = row
            foods.append({
                'food_name': food_name,
                'consumed_at': consumed_at,
                'calories': calories,
                'protein': protein,
                'carbs': carbs,
                'fats': fats
            })
        
        # Send to frontend
        remote_participants = list(ctx.room.remote_participants.values())
        if remote_participants:
            client_participant = remote_participants[0]
            await ctx.room.local_participant.perform_rpc(
                destination_identity=client_participant.identity,
                method="nutrition.update",
                payload=json.dumps({
                    'foods': foods,
                    'totals': totals,
                    'date': today_start.date().isoformat()
                })
            )
            print(f"Sent initial nutrition update to frontend ({client_participant.identity})")
            print(f"  Foods: {len(foods)} items")
            print(f"  Totals: {totals}")
        else:
            print("No remote participants found for initial nutrition update")
            
    except Exception as e:
        print(f"Error sending initial nutrition update: {e}")
        import traceback
        traceback.print_exc()


async def entrypoint(ctx: agents.JobContext):
    # Initialize database on startup
    init_database()

    # Connect to the room *before* awaiting the participant
    await ctx.connect()
    
    # Wait for participant
    participant = await ctx.wait_for_participant()
    print(f"Starting nutrition assistant for {participant.identity} (using fixed ID: {FIXED_PARTICIPANT_ID})")

    session = AgentSession[NutritionUserData](
        userdata=NutritionUserData(participant_identity=FIXED_PARTICIPANT_ID, ctx=ctx),
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-realtime-preview-2025-06-03",
            voice="sage"
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel()
    )

    # Create agent instance
    agent = NutritionAssistant()
    
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=room_io.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        )
    )

    await asyncio.sleep(0.5)
    
    await send_initial_nutrition_update(ctx, FIXED_PARTICIPANT_ID)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))