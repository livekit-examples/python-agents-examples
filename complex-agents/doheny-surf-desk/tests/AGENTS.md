# Testing Guide for LLM Agents

This guide covers best practices for testing and debugging LLM-powered agents, based on real-world testing experience.

## Table of Contents

1. [Running Tests](#running-tests)
2. [Understanding Test Failures](#understanding-test-failures)
3. [Debugging Strategies](#debugging-strategies)
4. [Prompt Iteration Workflow](#prompt-iteration-workflow)
5. [Common Patterns](#common-patterns)
6. [Best Practices](#best-practices)

---

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run a specific test
pytest tests/test_agent.py::test_specific_test -v

# Run with verbose output (see what agent says)
pytest tests/test_agent.py::test_specific_test -v -s

# Run with short traceback for faster debugging
pytest tests/test_agent.py -v --tb=short

# Show only test names (no execution)
pytest tests/ --collect-only
```

### Environment Variables for Debugging

```bash
# Enable verbose eval output (see agent responses and events)
# Must use -s flag to disable pytest's stdout capture
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_agent.py::test_name -s -o log_cli=true

# Or with verbose pytest output
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_agent.py::test_name -v -s -o log_cli=true
```

**Verbose Output Example:**

```
+ RunResult(
   user_input=`My name is Alex Johnson`
   events:
     [0] FunctionCallEvent(item={'arguments': '{"name":"Alex Johnson"}', 'name': 'record_name'})
     [1] FunctionCallOutputEvent(item={'name': 'record_name', 'output': '', 'is_error': False})
)
```

This shows you exactly what events occurred and in what order, making it much easier to debug test failures.

### Running Tests One at a Time

**Important**: When debugging, run tests individually to:

- Focus on one failure at a time
- See clearer error messages
- Avoid cascading failures
- Iterate faster

```bash
# Test one, debug, then move to next
pytest tests/test_agent.py::test_first -v -s
# Fix issues...
pytest tests/test_agent.py::test_second -v -s
```

### CRITICAL: Always Use Full Output When Debugging

**NEVER use shortened output flags when debugging:**

- ❌ NEVER use `-q`, `--tb=no`, `tail`, `head`, or other output truncation
- ❌ NEVER run multiple tests at once when debugging
- ❌ NEVER skip verbose output when a test fails

**ALWAYS use full verbose output:**

```bash
# ✅ CORRECT: Full output with verbose events
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_agent.py::test_name -s -o log_cli=true -v

# ❌ WRONG: Shortened output
pytest tests/test_agent.py::test_name -q --tb=no
pytest tests/test_agent.py::test_name 2>&1 | tail -50
```

**Why this matters:**

- Shortened output hides critical error details
- You'll waste tokens re-running tests to see what you missed
- Full output shows the complete event sequence and error context
- One test at a time ensures you see the complete failure

**Debugging workflow:**

1. Run ONE test with full output: `LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_agent.py::test_name -s -o log_cli=true -v`
2. Read the COMPLETE error message and event sequence
3. Fix the prompt (not the test)
4. Re-run the SAME test with full output
5. Only move to next test after current one passes

---

## Understanding Test Failures

### Common Failure Types

#### 1. **AssertionError: Expected FunctionCallEvent**

The test expected a function call but got something else (usually a message).

**What to check:**

- Look at the "Context around failure" in the error
- See what event actually occurred
- Check if agent is asking questions instead of calling functions

**Example:**

```
Expected FunctionCallEvent
Context:
>>> [0] ChatMessageEvent(item={'role': 'assistant', 'content': ['Can you provide more details?']})
```

**Solution**: Fix the prompt to make the agent call the function directly, not ask questions first.

#### 2. **TypeError: object X can't be used in 'await' expression**

You're using `await` on something that doesn't need it.

**Common mistake:**

```python
# ❌ Wrong
await result.expect.next_event().is_function_call(name="my_function")

# ✅ Correct
result.expect.next_event().is_function_call(name="my_function")
```

**Rule**: `expect.next_event()` returns an assertion object, not an awaitable. Only use `await` for:

- `await session.run(...)`
- `await msg.judge(...)`

#### 3. **AssertionError: Expected another event, but none left**

The test tried to get an event that doesn't exist.

**Causes:**

- Skipped an event that should have been checked
- Agent didn't produce the expected event
- Wrong event order

**Solution**: Check the event sequence. Use `-s` flag to see all events.

---

## Debugging Strategies

### 1. See What the Agent Actually Does

Always run tests with `-v -s` to see:

- Agent's actual responses
- Function calls made
- Event sequence

```bash
# Basic verbose output
pytest tests/test_agent.py::test_name -v -s

# With LIVEKIT_EVALS_VERBOSE for detailed event information
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_agent.py::test_name -s -o log_cli=true
```

The `LIVEKIT_EVALS_VERBOSE=1` environment variable provides detailed output showing:

- Exact event sequence
- Function call arguments
- Function outputs
- Event types and order

This is especially useful when debugging why a test expects one event but gets another.

### 2. Understand the Event Sequence

Agent interactions produce events in this order:

1. `ChatMessageEvent` (user input)
2. `FunctionCallEvent` (agent calls function)
3. `FunctionCallOutputEvent` (function returns)
4. `ChatMessageEvent` (agent responds)

**Important**: When checking for messages after function calls, skip the function output:

```python
# After function call
result.expect.next_event().is_function_call(name="my_function")

# Skip function output
result.expect.skip_next_event_if(type="function_call_output")

# Now get the message
msg = result.expect.next_event().is_message(role="assistant")
```

### 3. Check Function Return Values

Function return values are agent-facing instructions, not user-facing messages.

**Correct pattern:**

```python
# Function returns agent-facing content
return f"RECOMMEND_TO_USER: {board}. {reason}"
```

**Wrong pattern:**

```python
# Function returns user-facing message
return f"I recommend the {board}. {reason}!"
```

Functions should return status/instructions for the agent, not direct user messages.

### 4. Inspect the Full Event Stream

When a test fails, look at the full event sequence in the error message:

```
Context around failure:
>>> [0] FunctionCallEvent(item={'name': 'check_availability', ...})
>>> [1] FunctionCallOutputEvent(item={'output': '...', ...})
>>> [2] ChatMessageEvent(item={'content': ['...']})
```

This shows you exactly what happened and in what order.

---

## Prompt Iteration Workflow

### The Golden Rule: **Fix Prompts, Not Tests**

When an agent doesn't behave as expected, **fix the prompt**, don't rewrite the test to work around bad behavior.

### Step-by-Step Process

#### 1. Identify the Problem

Run the test with FULL OUTPUT and see what the agent actually does:

```bash
# ✅ ALWAYS use this format for debugging
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_agent.py::test_name -s -o log_cli=true -v

# ❌ NEVER use shortened output
# pytest tests/test_agent.py::test_name -q --tb=no
# pytest tests/test_agent.py::test_name 2>&1 | tail -50
```

**Read the COMPLETE output** - don't truncate it. You need to see:

- Full event sequence
- Complete error message
- All function calls and outputs
- Complete context around failure

**Example output:**

```
Expected FunctionCallEvent 'transfer_to_scheduler'
Got: ChatMessageEvent asking for email
```

#### 2. Understand Why

Look at the agent's response:

- Is it asking unnecessary questions?
- Is it checking things it shouldn't?
- Is it missing key instructions?

#### 3. Fix the Prompt

Update the prompt file (e.g., `prompts/agent_prompt.yaml`) to be more explicit:

**Before (vague):**

```yaml
Once you have the information, transfer to the next agent.
```

**After (explicit):**

```yaml
TRANSFER TO NEXT AGENT:
Once you have collected all required information (name, email, age, experience),
and the customer asks to proceed or says they're ready,
you MUST immediately call transfer_to_next_agent().
Do NOT ask additional clarifying questions -
if the profile is complete and they want to proceed, transfer right away.
```

#### 4. Verify the Fix

Run the test again:

```bash
pytest tests/test_agent.py::test_name -v -s
```

#### 5. Iterate

If it still fails:

- Make the prompt even more explicit
- Add examples
- Use stronger language ("MUST", "DO NOT", "IMMEDIATELY")
- Break down complex instructions into numbered steps

### Prompt Writing Tips

1. **Be Explicit**: Don't assume the LLM will infer behavior
2. **Use Imperatives**: "Call X function", "Do NOT ask questions"
3. **Provide Examples**: Show what good behavior looks like
4. **Use Conditional Logic**: "If X, then Y, otherwise Z"
5. **Prioritize**: Put most important instructions first
6. **Be Specific**: Name exact functions, exact conditions

---

## Common Patterns

### Pattern 1: Function Call Then Message

```python
# Agent calls function, then responds
result = await session.run(user_input="...")

# Check function was called
result.expect.next_event().is_function_call(name="function_name")

# Skip function output
result.expect.skip_next_event_if(type="function_call_output")

# Get agent's response
msg = result.expect.next_event().is_message(role="assistant")
await msg.judge(llm_judge, intent="...")
```

### Pattern 2: Multiple Function Calls

```python
result = await session.run(user_input="...")

# First function
result.expect.next_event().is_function_call(name="first_function")
result.expect.skip_next_event_if(type="function_call_output")

# Second function
result.expect.next_event().is_function_call(name="second_function")
```

### Pattern 3: Skip Messages

```python
result = await session.run(user_input="...")

# Skip initial message, look for function call
result.expect.skip_next_event_if(type="message", role="assistant")
result.expect.next_event().is_function_call(name="function_name")
```

### Pattern 4: Conditional Behavior

```python
result = await session.run(user_input="...")

first_event = result.expect.next_event()

# Try as function call
try:
    first_event.is_function_call(name="expected_function")
except AssertionError:
    # It was a message, handle it
    msg = first_event.is_message(role="assistant")
    # Respond and try again
    result = await session.run(user_input="...")
```

---

## Best Practices

### 1. Test Setup

Always properly initialize test fixtures:

```python
@pytest.mark.asyncio
async def test_example() -> None:
    # ✅ Good: Create local variables
    llm_string = "openai/gpt-4o-mini"
    userdata = MyData()

    async with AgentSession(llm=llm_string, userdata=userdata) as session:
        # test code
```

```python
# ❌ Bad: Using undefined fixtures
async def test_example(llm, userdata):  # These don't exist!
    async with AgentSession(llm=llm, userdata=userdata) as session:
        # test code
```

### 2. Test Isolation

Each test should be independent:

- Set up its own data
- Don't rely on previous test state
- Clean state between tests

### 3. Test One Thing

Each test should verify one specific behavior:

- ✅ "Test that agent calls transfer function when profile complete"
- ❌ "Test entire booking flow" (use integration test for that)

### 4. Use Descriptive Assertions

```python
# ✅ Good: Clear what we're checking
assert session.userdata.is_profile_complete()
assert session.userdata.booking_id is not None

# ❌ Bad: Vague assertion
assert session.userdata  # What about it?
```

### 5. Debug Output

When debugging, add print statements:

```python
result = await session.run(user_input="...")
print(f"Events: {[e.type for e in result.events()]}")  # See all events
```

### 6. LLM Judge Usage

Use LLM judges for intent verification:

```python
async with _llm_judge() as llm_judge:
    msg = result.expect.next_event().is_message(role="assistant")
    await msg.judge(
        llm_judge,
        intent="Explains that booking is confirmed and provides details"
    )
```

This verifies the agent's response matches the expected intent, not just exact wording.

---

## Debugging Checklist

When a test fails:

- [ ] Run ONE test with FULL output: `LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_agent.py::test_name -s -o log_cli=true -v`
- [ ] NEVER use `-q`, `--tb=no`, `tail`, `head` - you'll miss critical details
- [ ] Read the COMPLETE error message and event sequence (don't truncate)
- [ ] Use `LIVEKIT_EVALS_VERBOSE=1` for detailed event information
- [ ] Check the event sequence in the error message
- [ ] Verify test setup (variables, fixtures initialized)
- [ ] Check if `await` is used correctly
- [ ] Verify function outputs are skipped before checking messages
- [ ] Read the agent's actual response - does it make sense?
- [ ] If agent behavior is wrong, fix the prompt (not the test)
- [ ] Re-run the SAME test with full output to verify fix
- [ ] Only move to next test after current one passes

---

## Common Mistakes

### Mistake 1: Rewriting Tests to Work Around Bad Behavior

**❌ Wrong:**

```python
# Agent asks questions, so test handles that
for i in range(3):
    result = await session.run(user_input="...")
    if "question" in response:
        result = await session.run(user_input="answer")
```

**✅ Right:**

```python
# Fix prompt to make agent call function directly
# Then test simply:
result.expect.next_event().is_function_call(name="function")
```

### Mistake 2: Using await on Non-Awaitables

**❌ Wrong:**

```python
await result.expect.next_event().is_function_call(...)
```

**✅ Right:**

```python
result.expect.next_event().is_function_call(...)
```

### Mistake 3: Not Skipping Function Outputs

**❌ Wrong:**

```python
result.expect.next_event().is_function_call(name="func")
msg = result.expect.next_event().is_message(...)  # Gets function output!
```

**✅ Right:**

```python
result.expect.next_event().is_function_call(name="func")
result.expect.skip_next_event_if(type="function_call_output")
msg = result.expect.next_event().is_message(...)  # Gets actual message
```

### Mistake 4: Undefined Variables

**❌ Wrong:**

```python
async def test_example(llm, userdata):  # These aren't fixtures!
    async with AgentSession(llm=llm, userdata=userdata) as session:
```

**✅ Right:**

```python
async def test_example():
    llm_string = "openai/gpt-4o-mini"
    userdata = MyData()
    async with AgentSession(llm=llm_string, userdata=userdata) as session:
```

---

## Summary

**Key Principles:**

1. **Run tests one at a time** when debugging
2. **ALWAYS use full output** - never use `-q`, `--tb=no`, `tail`, `head` when debugging
3. **Use `LIVEKIT_EVALS_VERBOSE=1 -s -o log_cli=true -v`** for complete debugging information
4. **Read the complete error** - don't truncate output, you'll waste tokens re-running
5. **Fix prompts, not tests** when behavior is wrong
6. **Understand the event sequence** (function call → output → message)
7. **Be explicit in prompts** - LLMs need clear instructions
8. **Test setup correctly** - initialize all variables locally
9. **Skip function outputs** before checking messages
10. **One test at a time** - fix one completely before moving to the next

**Remember**: The test describes what _should_ happen. If the agent doesn't do it, make the prompt more explicit about what to do, don't work around it in the test.
