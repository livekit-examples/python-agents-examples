'use client';

import { cn } from '@/lib/utils';

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
}

interface AgentChatAreaProps {
  messages?: ChatMessage[];
  className?: string;
}

export function AgentChatArea({ messages = [], className }: AgentChatAreaProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {messages.length === 0 ? (
        <div className="text-fg4 py-8 text-center text-sm">No messages yet</div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'max-w-[80%] rounded-lg px-4 py-2',
              message.isUser
                ? 'bg-fgAccent1 text-bg0 self-end rounded-br-none'
                : 'bg-bg2 text-fg0 self-start rounded-bl-none'
            )}
          >
            <p className="text-sm">{message.text}</p>
          </div>
        ))
      )}
    </div>
  );
}
