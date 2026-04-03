# Freshness Rules for LiveKit Development

This document provides detailed guidance on maintaining accuracy when building with LiveKit Agents. These rules exist because model training data becomes outdated immediately, and LiveKit's SDK evolves rapidly.

## The Core Problem

Coding agents (Claude, GPT, etc.) are trained on historical data. This training includes:
- Old versions of LiveKit documentation
- Outdated code examples from blogs and tutorials
- Previous SDK versions with different APIs
- Community answers that may no longer be accurate

When an agent "knows" something about LiveKit, that knowledge may be months or years out of date.

## Verification Requirements

### Before Writing Any LiveKit Code

1. **Identify what needs verification**
   - Method names and signatures
   - Configuration options and their types
   - Import paths and module structure
   - Default values and behaviors

2. **Query the documentation**
   - Use MCP to search for the specific feature
   - Read the current documentation, not cached knowledge
   - Look for version notes or recent changes

3. **Cite your source**
   - Note which documentation page informed the implementation
   - If something cannot be verified, explicitly state this

### During Implementation

When writing code, verify:

| Element | Why It Changes | How to Verify |
|---------|----------------|---------------|
| Import statements | Module restructuring | Search docs for current import paths |
| Method signatures | API evolution | Look up method in API reference |
| Configuration keys | Naming conventions change | Check configuration documentation |
| Default behaviors | Defaults are tuned over time | Read parameter documentation |
| Event names | Event systems evolve | Check events/callbacks documentation |

### After Implementation

Before presenting code to the user:
- Confirm all APIs used are documented
- Verify example patterns match current best practices
- Check for deprecation warnings in documentation

## What Cannot Be Verified

Some things legitimately cannot be verified against documentation:
- User's specific environment or configuration
- Integration with user's existing codebase
- Business logic and application requirements

When providing guidance on these topics, clearly distinguish between:
- "According to LiveKit documentation..." (verified)
- "Based on your requirements..." (application-specific)
- "This may need adjustment..." (uncertain)

## Red Flags: When to Stop and Verify

Pause and verify against documentation when:

1. **Writing from memory** - If you're typing an API call without having just looked it up, verify it
2. **"I think" or "I believe"** - Uncertainty about LiveKit APIs requires verification
3. **Complex configurations** - Multi-option configurations are likely to have evolved
4. **Error handling** - Exception types and error formats change
5. **Newer features** - Recently added features have the highest drift risk

## Communication with Users

### When Verified

```
According to the LiveKit Agents documentation, the correct approach is...
[implementation]
```

### When Partially Verified

```
The workflow structure follows LiveKit's documented patterns. However, I could not
verify [specific detail] against current documentation. Please confirm this matches
your SDK version.
```

### When Unverified

```
I cannot verify this implementation against current LiveKit documentation. This is
based on general patterns and may require adjustment. I recommend:
1. Checking the official documentation at [link]
2. Testing this implementation before relying on it
```

## MCP Server Unavailable

If the LiveKit MCP server is not installed or accessible:

1. **Inform the user immediately** - They should know verification isn't possible
2. **Recommend installation** - Point to https://docs.livekit.io/mcp
3. **Proceed with caution** - Clearly mark all LiveKit-specific code as unverified
4. **Suggest manual verification** - User should check docs before using the code

Do not pretend to have verified something when MCP access was unavailable.

## Version Awareness

LiveKit Agents has distinct versions with potentially different APIs:
- Python SDK (`livekit-agents`)
- Node.js/TypeScript SDK (`@livekit/agents`)

Each has its own release cycle and API surface. When working with LiveKit:
- Determine which SDK the user is using
- Search documentation specific to that SDK
- Do not assume API parity between Python and Node.js versions

## Examples of Drift

These examples illustrate why verification matters:

### Configuration Changes
Old tutorials might show:
```python
agent = VoiceAgent(config={"model": "gpt-4"})
```

Current API might be:
```python
agent = VoiceAgent(llm=SomeLLMClass(...))
```

### Method Renames
What was once:
```python
agent.start_session()
```

Might now be:
```python
agent.start()
```

### Import Restructuring
Previous:
```python
from livekit.agents.voice import VoiceAgent
```

Current:
```python
from livekit.agents import VoiceAgent
```

None of these changes are predictable from training data. Only live documentation reflects current state.

## Summary

1. **Default to distrust** - Assume any LiveKit knowledge from memory is outdated
2. **Verify actively** - Use MCP to check documentation before implementation
3. **Communicate uncertainty** - Tell users when something cannot be verified
4. **Cite sources** - Reference documentation when providing verified information
5. **Recommend MCP** - If unavailable, make installation a priority
