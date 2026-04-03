const TOKEN_URL = "/api/token";
const ROOM_STATUS_URL = "/api/room-status";

let room = null;
let userId = null;
let userHash = null;

function getParams() {
  if (!userId) {
    const params = new URLSearchParams(window.location.search);
    userId = params.get("user_id");
    userHash = params.get("user_hash") || "";
  }
  return { userId, userHash };
}

function getUserId() {
  return getParams().userId;
}

function updateStatus(status) {
  document.getElementById("status").textContent = status;
}

async function connect() {
  const id = getUserId();
  if (!id) return;
  updateStatus("Connecting...");

  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: id, user_hash: userHash || "" }),
  });
  const { server_url, participant_token } = await res.json();

  room = new LivekitClient.Room();

  room.on(LivekitClient.RoomEvent.Connected, () => {
    updateStatus("Connected");
    // Tell parent frame we're connected (for cross-page auto-reconnect)
    window.parent.postMessage("voice-connected", "*");
  });

  room.on(LivekitClient.RoomEvent.Disconnected, () => {
    updateStatus("Disconnected");
    room = null;
    // Don't signal parent here — this fires on page unload too,
    // which would clear the flag and break auto-reconnect.
  });

  room.on(LivekitClient.RoomEvent.TrackSubscribed, (track) => {
    if (track.kind === "audio") {
      const el = track.attach();
      el.id = "agent-audio";
      document.body.appendChild(el);
    }
  });

  room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track) => {
    if (track.kind === "audio") {
      track.detach().forEach((el) => el.remove());
    }
  });

  await room.connect(server_url, participant_token);
  try {
    await room.localParticipant.setMicrophoneEnabled(true);
  } catch {
    // Mic enable can fail without a user gesture (auto-reconnect).
    // Room is still connected and can receive agent audio.
  }
}

async function disconnect() {
  if (room) {
    await room.disconnect();
    room = null;
  }
  // Explicit disconnect — tell parent to clear the flag
  window.parent.postMessage("voice-disconnected", "*");
}

function toggleConnection() {
  if (room) {
    disconnect();
  } else {
    connect();
  }
}

async function checkAndAutoConnect() {
  const params = new URLSearchParams(window.location.search);
  const id = getUserId();
  if (!id) return;

  // Method 1: Parent told us we were connected (same-origin, instant)
  if (params.get("auto_connect") === "true") {
    console.log("[widget] auto_connect flag set by parent, connecting...");
    try {
      await connect();
    } catch (err) {
      console.error("[widget] auto-connect failed:", err);
    }
    return;
  }

  // Method 2: Check server for active room (cross-domain fallback)
  try {
    let url = ROOM_STATUS_URL + "?user_id=" + encodeURIComponent(id);
    if (userHash) url += "&user_hash=" + encodeURIComponent(userHash);
    const res = await fetch(url);
    const { active } = await res.json();
    console.log("[widget] room-status check:", active ? "active" : "inactive");
    if (active) {
      await connect();
    }
  } catch (err) {
    console.error("[widget] room-status check failed:", err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("userId").textContent = getUserId() || "—";
  document.getElementById("connectBtn").addEventListener("click", toggleConnection);
  checkAndAutoConnect();
});
