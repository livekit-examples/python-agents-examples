"""
---
title: OpenAI Realtime with Function Tools (Duplicate)
category: realtime-agents
tags: [duplicate_example, function_tools, math_operations]
difficulty: intermediate
description: Duplicate of realtime/openai-realtime-tools.py with same 50+ tools
demonstrates:
  - Same extensive function tool collection
  - Duplicate example for testing
  - Math and string operations
  - List manipulations
---
"""

import librosa
import random, math
import numpy as np
import os
from typing import AsyncIterable
from dotenv import load_dotenv
from pathlib import Path
from livekit.agents.llm import function_tool
from livekit import agents, rtc
from livekit.agents import utils, mcp
from livekit.agents.voice import AgentSession, Agent, RunContext
from livekit.plugins import (
    openai,
    silero
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
                            You are a helpful voice AI assistant. Please speak in english!
                         """)

    @function_tool
    async def print_to_console(self, context: RunContext):
        """Print a confirmation message to the console."""
        print("Console Print Success!")
        return "I've printed to the console."

    @function_tool
    async def add_numbers(self, context: RunContext, a: float, b: float):
        """Return the sum of two numbers."""
        print(f"Adding {a} and {b}")
        return str(a + b)

    @function_tool
    async def subtract_numbers(self, context: RunContext, a: float, b: float):
        """Return the difference between two numbers."""
        print(f"Subtracting {a} and {b}")
        return str(a - b)

    @function_tool
    async def multiply_numbers(self, context: RunContext, a: float, b: float):
        """Multiply two numbers."""
        print(f"Multiplying {a} and {b}")
        return str(a * b)

    @function_tool
    async def divide_numbers(self, context: RunContext, a: float, b: float):
        """Divide ``a`` by ``b``. Returns ``inf`` if ``b`` is 0."""
        print(f"Dividing {a} by {b}")
        return str(a / b if b != 0 else 'inf')

    @function_tool
    async def roll_die(self, context: RunContext, sides: int = 6):
        """Roll a die with the specified number of sides."""
        print(f"Rolling a die with {sides} sides")
        return random.randint(1, max(1, int(sides)))

    @function_tool
    async def random_choice(self, context: RunContext, *items: str):
        """Return a random item from the provided list of strings."""
        print(f"Choosing a random item from {items}")
        return random.choice(items) if items else ''

    @function_tool
    async def random_word_from_list(self, context: RunContext, words: list[str]):
        """Return a random word from ``words``."""
        print(f"Choosing a random word from {words}")
        return random.choice(words) if words else ''

    @function_tool
    async def random_integer(self, context: RunContext, start: int, end: int):
        """Return a random integer between ``start`` and ``end`` inclusive."""
        print(f"Choosing a random integer between {start} and {end}")
        return str(random.randint(start, end))

    @function_tool
    async def square_number(self, context: RunContext, n: float):
        """Return ``n`` squared."""
        print(f"Squaring {n}")
        return str(n ** 2)

    @function_tool
    async def cube_number(self, context: RunContext, n: float):
        """Return ``n`` cubed."""
        print(f"Cubing {n}")
        return str(n ** 3)

    @function_tool
    async def sqrt_number(self, context: RunContext, n: float):
        """Return the square root of ``n``."""
        print(f"Taking the square root of {n}")
        return str(math.sqrt(n))

    @function_tool
    async def factorial(self, context: RunContext, n: int):
        """Return the factorial of ``n``."""
        print(f"Calculating the factorial of {n}")
        return str(math.factorial(n))

    @function_tool
    async def reverse_string(self, context: RunContext, text: str):
        """Return ``text`` reversed."""
        print(f"Reversing {text}")
        return text[::-1]

    @function_tool
    async def sort_numbers(self, context: RunContext, numbers: list[float]):
        """Sort a list of numbers in ascending order."""
        print(f"Sorting {numbers}")
        return str(sorted(numbers))

    @function_tool
    async def find_max(self, context: RunContext, numbers: list[float]):
        """Return the maximum number from ``numbers``."""
        print(f"Finding the maximum number from {numbers}")
        return str(max(numbers))

    @function_tool
    async def find_min(self, context: RunContext, numbers: list[float]):
        """Return the minimum number from ``numbers``."""
        print(f"Finding the minimum number from {numbers}")
        return str(min(numbers))

    @function_tool
    async def average_numbers(self, context: RunContext, numbers: list[float]):
        """Return the arithmetic mean of ``numbers``."""
        print(f"Calculating the average of {numbers}")
        return str(sum(numbers) / len(numbers) if numbers else 0)

    @function_tool
    async def count_words(self, context: RunContext, text: str):
        """Count the number of words in ``text``."""
        print(f"Counting the number of words in {text}")
        return str(len(text.split()))

    @function_tool
    async def uppercase_string(self, context: RunContext, text: str):
        """Convert ``text`` to uppercase."""
        print(f"Converting {text} to uppercase")
        return text.upper()

    @function_tool
    async def lowercase_string(self, context: RunContext, text: str):
        """Convert ``text`` to lowercase."""
        print(f"Converting {text} to lowercase")
        return text.lower()

    @function_tool
    async def titlecase_string(self, context: RunContext, text: str):
        """Convert ``text`` to title case."""
        print(f"Converting {text} to title case")
        return text.title()

    @function_tool
    async def join_strings(self, context: RunContext, *strings: str):
        """Join multiple strings with spaces."""
        print(f"Joining {strings}")
        return ' '.join(strings)

    @function_tool
    async def check_palindrome(self, context: RunContext, text: str):
        """Check if ``text`` reads the same backwards as forwards."""
        t = text.lower().replace(' ', '')
        print(f"Checking if {text} is a palindrome")
        return str(t == t[::-1])

    @function_tool
    async def count_vowels(self, context: RunContext, text: str):
        """Count the vowels in ``text``."""
        vowels = 'aeiouAEIOU'
        print(f"Counting the vowels in {text}")
        return str(sum(1 for c in text if c in vowels))

    @function_tool
    async def count_consonants(self, context: RunContext, text: str):
        """Count the consonant letters in ``text``."""
        vowels = 'aeiouAEIOU'
        print(f"Counting the consonants in {text}")
        return str(sum(1 for c in text if c.isalpha() and c not in vowels))

    @function_tool
    async def is_prime(self, context: RunContext, n: int):
        """Return ``True`` if ``n`` is a prime number."""
        if n < 2:
            print(f"{n} is not a prime number")
            return 'False'
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                print(f"{n} is not a prime number")
                return 'False'
        return 'True'

    @function_tool
    async def generate_fibonacci(self, context: RunContext, count: int):
        """Generate a Fibonacci sequence of ``count`` numbers."""
        print(f"Generating a Fibonacci sequence of {count} numbers")
        seq = []
        a, b = 0, 1
        for _ in range(max(0, count)):
            seq.append(a)
            a, b = b, a + b
        return str(seq)

    @function_tool
    async def sum_list(self, context: RunContext, numbers: list[float]):
        """Return the sum of a list of numbers."""
        print(f"Summing the list of numbers {numbers}")
        return str(sum(numbers))

    @function_tool
    async def product_list(self, context: RunContext, numbers: list[float]):
        """Return the product of all numbers in ``numbers``."""
        print(f"Calculating the product of {numbers}")
        prod = 1
        for n in numbers:
            prod *= n
        return str(prod)

    @function_tool
    async def difference_between_max_and_min(self, context: RunContext, numbers: list[float]):
        """Return the difference between the largest and smallest numbers."""
        print(f"Calculating the difference between the largest and smallest numbers in {numbers}")
        return str(max(numbers) - min(numbers))

    @function_tool
    async def convert_to_binary(self, context: RunContext, n: int):
        """Convert an integer to its binary representation."""
        print(f"Converting {n} to binary")
        return bin(n)

    @function_tool
    async def convert_to_hex(self, context: RunContext, n: int):
        """Convert an integer to hexadecimal."""
        print(f"Converting {n} to hexadecimal")
        return hex(n)

    @function_tool
    async def convert_to_octal(self, context: RunContext, n: int):
        """Convert an integer to octal."""
        print(f"Converting {n} to octal")
        return oct(n)

    @function_tool
    async def absolute_value(self, context: RunContext, n: float):
        """Return the absolute value of ``n``."""
        print(f"Calculating the absolute value of {n}")
        return str(abs(n))

    @function_tool
    async def even_or_odd(self, context: RunContext, n: int):
        """Return whether ``n`` is even or odd."""
        print(f"Checking if {n} is even or odd")
        return 'even' if n % 2 == 0 else 'odd'

    @function_tool
    async def generate_random_password(self, context: RunContext, length: int = 8):
        """Generate a random alphanumeric password of ``length`` characters."""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        print(f"Generating a random alphanumeric password of {length} characters")
        return ''.join(random.choice(chars) for _ in range(max(1, length)))

    @function_tool
    async def replace_substring(self, context: RunContext, text: str, old: str, new: str):
        """Replace ``old`` with ``new`` in ``text``."""
        print(f"Replacing {old} with {new} in {text}")
        return text.replace(old, new)

    @function_tool
    async def word_in_string(self, context: RunContext, text: str, word: str):
        """Check whether ``word`` exists in ``text``."""
        print(f"Checking if {word} exists in {text}")
        return str(word in text)

    @function_tool
    async def repeat_string(self, context: RunContext, text: str, times: int):
        """Repeat ``text`` ``times`` times."""
        print(f"Repeating {text} {times} times")
        return text * max(0, times)

    @function_tool
    async def anagram_check(self, context: RunContext, first: str, second: str):
        """Check if two strings are anagrams."""
        print(f"Checking if {first} and {second} are anagrams")
        return str(sorted(first) == sorted(second))

    @function_tool
    async def generate_random_color(self, context: RunContext):
        """Return a random hex color code."""
        print("Generating a random hex color code")
        return '#%06x' % random.randint(0, 0xFFFFFF)

    @function_tool
    async def sort_words_alphabetically(self, context: RunContext, words: list[str]):
        """Sort a list of words alphabetically."""
        print(f"Sorting the list of words {words}")
        return str(sorted(words))

    @function_tool
    async def get_string_length(self, context: RunContext, text: str):
        """Return the length of ``text``."""
        print(f"Calculating the length of {text}")
        return str(len(text))

    @function_tool
    async def round_number(self, context: RunContext, n: float, digits: int = 0):
        """Round ``n`` to ``digits`` decimal places."""
        print(f"Rounding {n} to {digits} decimal places")
        return str(round(n, digits))

    @function_tool
    async def calculate_percentage(self, context: RunContext, part: float, whole: float):
        """Return what percentage ``part`` is of ``whole``."""
        if whole == 0:
            print(f"Calculating the percentage of {part} of {whole}")
            return '0'
        return str((part / whole) * 100)

    @function_tool
    async def to_ascii_codes(self, context: RunContext, text: str):
        """Convert each character in ``text`` to its ASCII code."""
        print(f"Converting each character in {text} to its ASCII code")
        return str([ord(c) for c in text])

    @function_tool
    async def from_ascii_codes(self, context: RunContext, codes: list[int]):
        """Convert a list of ASCII codes back into a string."""
        print(f"Converting a list of ASCII codes {codes} back into a string")
        return ''.join(chr(c) for c in codes)

    @function_tool
    async def convert_celsius_to_fahrenheit(self, context: RunContext, celsius: float):
        """Convert a temperature from Celsius to Fahrenheit."""
        print(f"Converting {celsius} Celsius to Fahrenheit")
        return str(celsius * 9 / 5 + 32)

    @function_tool
    async def convert_fahrenheit_to_celsius(self, context: RunContext, fahrenheit: float):
        """Convert a temperature from Fahrenheit to Celsius."""
        print(f"Converting {fahrenheit} Fahrenheit to Celsius")
        return str((fahrenheit - 32) * 5 / 9)

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-realtime-preview-2025-06-03"
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel()
    )

    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

    await session.generate_reply()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))