import { useEffect } from 'react';
import { useRoomContext } from '@livekit/components-react';

export default function useTextStreamLogger() {
  const room = useRoomContext();

  useEffect(() => {
    if (!room) return;

    const handler = (reader: AsyncIterable<string>, participantInfo: any) => {
      const info = (reader as any).info;
      console.log(
        `Received text stream from ${participantInfo.identity}\n` +
        `  Topic: ${info.topic}\n` +
        `  Timestamp: ${info.timestamp}\n` +
        `  ID: ${info.id}\n` +
        `  Size: ${info.size || 'N/A'}\n` +
        `  Attributes: ${JSON.stringify(info.attributes || {}, null, 2)}`
      );

      // Process the stream incrementally
      (async () => {
        try {
          for await (const chunk of reader) {
            console.log(`Next chunk: ${chunk}`);
          }
          console.log('Text stream completed');
        } catch (error) {
          console.error('Error reading text stream:', error);
        }
      })();
    };

    // Register the handler for the specific topic
    room.registerTextStreamHandler('my-topic', handler);

    // Cleanup function to unregister the handler
    return () => {
      room.unregisterTextStreamHandler('my-topic', handler);
    };
  }, [room]);
}