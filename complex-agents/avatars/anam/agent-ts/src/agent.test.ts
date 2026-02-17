import { inference, initializeLogger, voice } from '@livekit/agents';
import dotenv from 'dotenv';
import { afterEach, beforeEach, describe, it } from 'vitest';
import { Agent } from './agent';

dotenv.config({ path: '.env.local' });

// Initialize logger for testing
initializeLogger({ pretty: false, level: 'debug' });

describe('agent evaluation', () => {
  let session: voice.AgentSession;
  let llmInstance: inference.LLM;

  beforeEach(async () => {
    llmInstance = new inference.LLM({ model: 'openai/gpt-5.1' });
    session = new voice.AgentSession({ llm: llmInstance });
    await session.start({ agent: new Agent() });
  });

  afterEach(async () => {
    await session?.close();
  });

  it('offers assistance', { timeout: 30000 }, async () => {
    // Run an agent turn following the user's greeting
    const result = await session.run({ userInput: 'Hello' }).wait();

    // Evaluate the agent's response for friendliness
    await result.expect
      .nextEvent()
      .isMessage({ role: 'assistant' })
      .judge(llmInstance, {
        intent: `\
Greets the user in a friendly manner.

Optional context that may or may not be included:
- Offer of assistance with any request the user may have
- Other small talk or chit chat is acceptable, so long as it is friendly and not too intrusive
`,
      });

    // Assert that there are no unexpected further events
    result.expect.noMoreEvents();
  });
});
