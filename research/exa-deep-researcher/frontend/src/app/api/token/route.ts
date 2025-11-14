import { NextRequest, NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";
import { RoomConfiguration, RoomAgentDispatch } from "@livekit/protocol";

function generateRoomName(): string {
  return `exa-research-${Math.random().toString(36).substring(2, 11)}`;
}

function getAgentName(): string {
  return process.env.DEV ? "exa-deep-researcher-dev" : "exa-deep-researcher";
}

export async function POST(request: NextRequest) {
  try {
    const { identity } = await request.json();

    const livekitUrl = process.env.LIVEKIT_URL;
    const livekitApiKey = process.env.LIVEKIT_API_KEY;
    const livekitApiSecret = process.env.LIVEKIT_API_SECRET;

    if (!livekitUrl || !livekitApiKey || !livekitApiSecret) {
      return NextResponse.json(
        {
          error:
            "LiveKit credentials not configured. Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in your environment variables.",
        },
        { status: 500 }
      );
    }

    const roomName = generateRoomName();
    const agentName = getAgentName();

    console.log(
      `[Token API] Using agent name: ${agentName} (DEV=${
        process.env.DEV || "not set"
      })`
    );

    const at = new AccessToken(livekitApiKey, livekitApiSecret, {
      identity: identity || "user",
    });

    const roomConfig = new RoomConfiguration({
      agents: [
        new RoomAgentDispatch({
          agentName: agentName,
        }),
      ],
    });

    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    });

    // Set room configuration for agent dispatch
    at.roomConfig = roomConfig;

    const token = await at.toJwt();

    return NextResponse.json({
      token,
      serverUrl: livekitUrl,
      room: roomName,
    });
  } catch (error) {
    console.error("Token generation error:", error);
    return NextResponse.json(
      {
        error:
          "Failed to generate token: " +
          (error instanceof Error ? error.message : String(error)),
      },
      { status: 500 }
    );
  }
}
