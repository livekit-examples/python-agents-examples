import { useMemo } from 'react';
import { Room } from 'livekit-client';
import {
  type ReceivedChatMessage,
  type TextStreamData,
  useChat,
  useRoomContext,
  useTranscriptions,
} from '@livekit/components-react';

type ChatMessageSource = 'transcription' | 'chat';

export type LivekitMessage = ReceivedChatMessage & {
  source: ChatMessageSource;
  streamTopic?: string;
};

function transcriptionToChatMessage(textStream: TextStreamData, room: Room): LivekitMessage {
  return {
    id: textStream.streamInfo.id,
    timestamp: textStream.streamInfo.timestamp,
    message: textStream.text,
    streamTopic: textStream.streamInfo.topic,
    source: 'transcription',
    from:
      textStream.participantInfo.identity === room.localParticipant.identity
        ? room.localParticipant
        : Array.from(room.remoteParticipants.values()).find(
            (p) => p.identity === textStream.participantInfo.identity
          ),
  };
}

function chatMessageWithSource(message: ReceivedChatMessage): LivekitMessage {
  return {
    ...message,
    source: 'chat',
  };
}

export function useChatMessages(): LivekitMessage[] {
  const chat = useChat();
  const room = useRoomContext();
  const transcriptions: TextStreamData[] = useTranscriptions();

  const mergedTranscriptions = useMemo(() => {
    const merged: LivekitMessage[] = [
      ...transcriptions.map((transcription) => transcriptionToChatMessage(transcription, room)),
      ...chat.chatMessages.map(chatMessageWithSource),
    ];
    return merged.sort((a, b) => a.timestamp - b.timestamp);
  }, [transcriptions, chat.chatMessages, room]);

  return mergedTranscriptions;
}
