# Multi-Domain Voice Agent

A LiveKit voice agent that maintains conversation continuity as users navigate across pages and domains. The agent stays alive between page loads, so when a user reconnects from a different page (or a completely different domain), they pick up exactly where they left off.

This is designed for the common pattern of an embeddable voice widget (like Intercom or Drift, but for voice AI) that works across a customer's entire web presence without losing context.

## How It Works

### The Problem

When a user navigates between pages, the browser tears down the WebRTC connection. A typical voice agent would shut down, and the next page would start a fresh session with no memory of the previous conversation.

This gets worse across domains. If your widget is embedded on `support.example.com` and `products.example.com`, the agent needs to survive transitions between completely unrelated origins.

### The Solution

Three mechanisms work together:

**1. Persistent agent sessions (server-side)**

The agent uses `close_on_disconnect=False` when starting its session. When the user's browser disconnects (page navigation, tab close, network blip), the agent stays in the LiveKit room instead of shutting down. The room stays alive, and the agent retains its full conversation history in memory.

```python
await session.start(
    agent=Assistant(),
    room=ctx.room,
    room_options=room_io.RoomOptions(
        close_on_disconnect=False,  # agent survives user disconnect
    ),
)
```

An idle timeout (5 minutes) ensures abandoned sessions get cleaned up. If the user reconnects before the timeout, the timer is cancelled.

**2. Deterministic room naming**

The token server maps each user to a predictable room name: `user-{user_id}`. No matter which page or domain the user connects from, the same user ID always routes to the same room. If the agent is already there, the user rejoins the existing conversation.

```
User connects from Page A  -->  room: user-abc123  (agent dispatched)
User navigates to Page B   -->  room: user-abc123  (agent already there)
```

**3. Embeddable widget with server-side state check**

The widget is designed to be embedded on any site via a single script tag. Instead of relying on localStorage (which breaks across domains due to third-party storage restrictions), the widget checks with the server on every load: "does this user have an active room?" If yes, it auto-connects.

## Architecture

```
                         +-----------------+
                         |  LiveKit Cloud  |
                         |  (room: user-x) |
                         +--------+--------+
                                  |
               +------------------+------------------+
               |                                     |
      +--------+--------+                   +--------+--------+
      |  Voice Agent    |                   |  Token Server   |
      |  (agent.py)     |                   |  (token_server) |
      |                 |                   |                 |
      |  - Stays alive  |                   |  - /api/token   |
      |    in room      |                   |  - /api/room-   |
      |  - 5min idle    |                   |    status       |
      |    timeout      |                   |  - HMAC verify  |
      +-----------------+                   |  - Serves       |
                                            |    static files |
                                            +--------+--------+
                                                     |
                          +------------- HTTP --------+
                          |                           |
               +----------+----------+     +----------+----------+
               | support.example.com |     | products.other.com  |
               |                     |     |                     |
               |  <script embed.js>  |     |  <script embed.js>  |
               |  +-iframe---------+ |     |  +-iframe---------+ |
               |  | widget.html    | |     |  | widget.html    | |
               |  | ?user_id=abc   | |     |  | ?user_id=abc   | |
               |  +----------------+ |     |  +----------------+ |
               +---------------------+     +---------------------+
```

### Components

**`src/agent.py`** - The voice agent. Registers with LiveKit as `multi-domain-agent`. Uses Deepgram STT, OpenAI gpt-4.1-mini, and Cartesia TTS. Listens for participant connect/disconnect events to manage the idle timeout.

**`src/token_server.py`** - FastAPI server that:
- `POST /api/token` - Generates a LiveKit access token with deterministic room name and agent dispatch. Verifies HMAC identity if `WIDGET_SECRET` is configured.
- `GET /api/room-status` - Checks if a user's room exists on LiveKit (used for auto-reconnect).
- Serves the frontend static files.

**`frontend/embed.js`** - The script customers add to their sites. Reads the user ID from the parent page's localStorage or cookies, creates the widget iframe, and passes the user ID (and optional HMAC hash) via URL params.

**`frontend/widget.html`** + **`frontend/shared.js`** - The widget UI that lives inside the iframe. On load, checks room status and auto-connects if a session is active. Handles connect/disconnect and audio track management.

## The Reconnection Flow

```
1. User visits support.example.com
   embed.js reads user_id from localStorage -> "abc123"
   Creates iframe: widget.html?user_id=abc123
   Widget calls GET /api/room-status?user_id=abc123 -> { active: false }
   User clicks Connect
   Token server creates token for room "user-abc123"
   Agent is dispatched into the room
   User talks to the agent

2. User clicks a link to products.other.com
   Browser navigates, WebRTC connection drops
   Agent stays in room (close_on_disconnect=False)
   Idle timeout starts (5 minutes)

3. products.other.com loads
   embed.js reads user_id from localStorage -> "abc123"
   Creates iframe: widget.html?user_id=abc123
   Widget calls GET /api/room-status?user_id=abc123 -> { active: true }
   Widget auto-connects to room "user-abc123"
   Agent is already there with full conversation context
   Idle timeout is cancelled
   Conversation continues seamlessly

4. If user never returns
   5 minute idle timeout fires
   Agent shuts down, room closes
```

## Embedding on Customer Sites

### Basic (development / trusted environments)

The simplest integration. The customer adds one script tag:

```html
<script src="https://your-widget-server.com/embed.js"
  data-user-key="user_id">
</script>
```

`data-user-key` tells the script which localStorage key (or cookie name) contains the user's identity. The script reads it and creates the widget iframe.

### With Identity Verification (production)

To prevent someone from impersonating another user by guessing their ID, add HMAC verification.

**Customer's backend** computes an HMAC of the user ID using a shared secret:

```python
import hmac, hashlib
user_hash = hmac.new(WIDGET_SECRET.encode(), user_id.encode(), hashlib.sha256).hexdigest()
```

```ruby
user_hash = OpenSSL::HMAC.hexdigest("sha256", WIDGET_SECRET, user_id)
```

```javascript
const crypto = require("crypto");
const userHash = crypto.createHmac("sha256", WIDGET_SECRET).update(userId).digest("hex");
```

**Customer's page template** includes the hash:

```html
<script src="https://your-widget-server.com/embed.js"
  data-user-key="user_id"
  data-user-hash="{{user_hash}}">
</script>
```

**Token server** verifies the hash before issuing tokens. Set `WIDGET_SECRET` in `.env.local` to enable verification. Without it, verification is skipped (dev mode).

### Why This Works Across Domains

The widget avoids all cross-origin storage issues:

- **No third-party localStorage** - The iframe never reads or writes localStorage. It gets the user ID from its URL params.
- **No third-party cookies** - All API calls from the iframe go to the widget server's own origin.
- **Parent page reads its own storage** - `embed.js` runs as a first-party script on the customer's page, so it has full access to that page's localStorage and cookies.
- **Server is the source of truth** - Instead of storing "was I connected?" in the browser, the widget asks the server "does my room exist?" on every load.

The same `embed.js` works on every site. Customers only need to add the script tag once to their page template.

## Running the Demo

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A [LiveKit Cloud](https://cloud.livekit.io/) account

### Setup

```bash
cd multi-domain
uv sync
```

Copy `.env.example` to `.env.local` and add your LiveKit credentials:

```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

Optionally set `WIDGET_SECRET` to enable HMAC verification (leave unset for dev mode).

Download required models:

```bash
uv run python src/agent.py download-files
```

### Run

In two terminals:

```bash
# Terminal 1: Agent
uv run python src/agent.py dev

# Terminal 2: Token server
uv run uvicorn src.token_server:app --port 3000
```

Open `http://localhost:3000/page-a.html`. Click Connect in the bottom-right widget, talk to the agent, then click the "Products" nav link. The widget on the new page auto-connects and the conversation continues.

### Demo Pages

The demo includes two pages that simulate different sites:

- **Page A** (`/page-a.html`) - Blue "Support Center" with FAQ content
- **Page B** (`/page-b.html`) - Green "Product Catalog" with pricing cards

Both pages include `embed.js` with a simulated `user_id` in localStorage. In production, this would come from the customer's real auth system.

## Key Design Decisions

**Keep the agent alive instead of persisting history.** Rather than saving conversation history to a database and restoring it on reconnect, we just keep the agent running in the room. This is simpler, has zero latency overhead, and preserves the full LLM context window. The trade-off is that if the agent process restarts, context is lost (you'd need persistence for that case).

**Server-side room check instead of client-side flags.** The widget asks the server "is my room active?" rather than tracking connection state in localStorage. This is more reliable (no stale flags) and works across domains without any storage access.

**HMAC identity verification.** The standard pattern for embeddable widgets (Intercom, Drift, etc.). Each customer computes a hash of the user ID on their backend using a shared secret. The widget server verifies the hash before issuing tokens. This prevents user impersonation without requiring customer-specific backend endpoints.

**Single embed script.** Customers add one `<script>` tag. The script handles iframe creation, user ID extraction, and hash forwarding. Updating the script on the widget server updates all customer integrations at once.

## Stack

- **Agent**: [LiveKit Agents SDK](https://docs.livekit.io/agents/) (Python)
- **STT**: Deepgram nova-3 (via LiveKit Inference)
- **LLM**: OpenAI gpt-4.1-mini (via LiveKit Inference)
- **TTS**: Cartesia sonic-3 (via LiveKit Inference)
- **VAD**: Silero
- **Turn detection**: LiveKit multilingual turn detector
- **Token server**: FastAPI + uvicorn
- **Frontend**: Vanilla HTML/JS, LiveKit client SDK from CDN
