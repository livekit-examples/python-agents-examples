import { RoomServiceClient } from 'livekit-server-sdk';

let roomServiceClient: RoomServiceClient | null = null;

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function normalizeLiveKitHost(url: string): string {
  if (url.startsWith('wss://')) {
    return `https://${url.slice('wss://'.length)}`;
  }
  if (url.startsWith('ws://')) {
    return `http://${url.slice('ws://'.length)}`;
  }
  return url;
}

export function getRoomServiceClient(): RoomServiceClient {
  if (roomServiceClient) {
    return roomServiceClient;
  }

  const livekitHost = normalizeLiveKitHost(requiredEnv('LIVEKIT_URL'));
  const apiKey = requiredEnv('LIVEKIT_API_KEY');
  const apiSecret = requiredEnv('LIVEKIT_API_SECRET');

  roomServiceClient = new RoomServiceClient(livekitHost, apiKey, apiSecret);
  return roomServiceClient;
}
