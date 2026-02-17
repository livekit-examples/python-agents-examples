'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useAgent, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AvatarPanel } from '@/components/app/avatar-panel';
import { IntakeForm } from '@/components/app/intake-form';
import { useRpcHandlers } from '@/hooks/useRpcHandlers';
import { EMPTY_FORM_DATA, type IntakeFormData } from '@/lib/form-fields';

interface SessionViewProps {
  appConfig: AppConfig;
}

const POST_SUBMIT_FALLBACK_MS = 90_000;

export const SessionView = ({
  appConfig,
  ...props
}: React.ComponentProps<'section'> & SessionViewProps) => {
  void appConfig; // passed for type/API consistency; may be used later
  const { end, room, isConnected } = useSessionContext();
  const agent = useAgent();
  const [formData, setFormData] = useState<IntakeFormData>(EMPTY_FORM_DATA);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const hasSpokenRef = useRef(false);

  useEffect(() => {
    if (!isSubmitted) return;

    const fallbackTimer = setTimeout(() => {
      end();
    }, POST_SUBMIT_FALLBACK_MS);

    return () => clearTimeout(fallbackTimer);
  }, [isSubmitted, end]);

  useEffect(() => {
    if (!isSubmitted) return;

    if (agent.isFinished) {
      end();
      return;
    }

    if (agent.state === 'speaking') {
      hasSpokenRef.current = true;
    }

    if (hasSpokenRef.current && agent.state !== 'speaking') {
      end();
    }
  }, [isSubmitted, agent.state, agent.isFinished, end]);

  useRpcHandlers({
    room,
    isConnected,
    formData,
    setFormData,
    setIsSubmitted,
  });

  return (
    <section
      className="bg-background relative flex h-full w-full flex-col overflow-hidden"
      style={{ zIndex: 'var(--app-z-session)' }}
      {...props}
    >
      {/* Main content: avatar left, form right */}
      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        <div className="flex max-h-[45%] w-full min-w-0 shrink-0 flex-col border-b md:max-h-none md:w-[46%] md:border-b-0">
          <AvatarPanel className="flex-1" />
        </div>
        <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto">
          <IntakeForm
            formData={formData}
            onFormDataChange={setFormData}
            isSubmitted={isSubmitted}
            onSubmit={() => setIsSubmitted(true)}
            className="flex-1"
          />
        </div>
      </div>
    </section>
  );
};
