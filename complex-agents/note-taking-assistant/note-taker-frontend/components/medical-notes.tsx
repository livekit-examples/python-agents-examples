'use client';

import { useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AnimatePresence, motion } from 'motion/react';
import remarkGfm from 'remark-gfm';
import { useMaybeRoomContext } from '@livekit/components-react';
import { Button } from '@/components/ui/button';

export interface MedicalNotesProps {
  className?: string;
}

export function MedicalNotes({ className }: MedicalNotesProps) {
  const [notes, setNotes] = useState<string>('');
  const [recentTranscription, setRecentTranscription] = useState<string>('');
  const [diagnosis, setDiagnosis] = useState<string>('');
  const [isLoadingDiagnosis, setIsLoadingDiagnosis] = useState(false);
  const room = useMaybeRoomContext();

  // Register RPC handlers for receiving notes and transcription updates
  useEffect(() => {
    if (!room || !room.localParticipant) return;

    // Handler for receiving full notes updates
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleReceiveNotes = async (rpcInvocation: any): Promise<string> => {
      try {
        const payload = JSON.parse(rpcInvocation.payload);

        if (payload) {
          if (payload.notes) {
            setNotes(payload.notes);
          }
          return 'Success: Notes received';
        } else {
          return 'Error: Invalid notes data format';
        }
      } catch (error) {
        return 'Error: ' + (error instanceof Error ? error.message : String(error));
      }
    };

    // Handler for receiving individual transcription updates
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleReceiveTranscription = async (rpcInvocation: any): Promise<string> => {
      try {
        const payload = JSON.parse(rpcInvocation.payload);

        if (payload && payload.transcription) {
          // Just replace with the new transcription
          setRecentTranscription(payload.transcription);
          return 'Success: Transcription received';
        } else {
          return 'Error: Invalid transcription data format';
        }
      } catch (error) {
        return 'Error: ' + (error instanceof Error ? error.message : String(error));
      }
    };

    // Handler for diagnosis response
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleDiagnosisResponse = async (rpcInvocation: any): Promise<string> => {
      try {
        const payload = JSON.parse(rpcInvocation.payload);

        if (payload && payload.diagnosis) {
          setDiagnosis(payload.diagnosis);
          setIsLoadingDiagnosis(false);
          return 'Success: Diagnosis received';
        } else {
          setIsLoadingDiagnosis(false);
          return 'Error: Invalid diagnosis data format';
        }
      } catch (error) {
        setIsLoadingDiagnosis(false);
        return 'Error: ' + (error instanceof Error ? error.message : String(error));
      }
    };

    // Register all RPC methods
    room.localParticipant.registerRpcMethod('receive_notes', handleReceiveNotes);
    room.localParticipant.registerRpcMethod('receive_transcription', handleReceiveTranscription);
    room.localParticipant.registerRpcMethod('receive_diagnosis', handleDiagnosisResponse);

    return () => {
      if (room && room.localParticipant) {
        room.localParticipant.unregisterRpcMethod('receive_notes');
        room.localParticipant.unregisterRpcMethod('receive_transcription');
        room.localParticipant.unregisterRpcMethod('receive_diagnosis');
      }
    };
  }, [room]);

  // Handle diagnose button click
  const handleDiagnose = async () => {
    if (!room || !room.localParticipant || !notes) return;

    setIsLoadingDiagnosis(true);

    try {
      // Find the agent participant - agents typically have "agent" in their identity
      const agentParticipant = Array.from(room.remoteParticipants.values()).find((p) =>
        p.identity.includes('agent')
      );

      if (agentParticipant) {
        // Send RPC request to agent for diagnosis
        await room.localParticipant.performRpc({
          destinationIdentity: agentParticipant.identity,
          method: 'request_diagnosis',
          payload: JSON.stringify({ notes }),
        });

        // The response should trigger the receive_diagnosis RPC handler
        // which will update the diagnosis state
      } else {
        setIsLoadingDiagnosis(false);
        setDiagnosis('No agent connected to process diagnosis request.');
      }
    } catch (error) {
      setIsLoadingDiagnosis(false);
      setDiagnosis(
        'Error requesting diagnosis: ' + (error instanceof Error ? error.message : String(error))
      );
    }
  };

  const containerClasses = useMemo(
    () =>
      [
        'grid min-h-0 h-full items-stretch gap-6',
        '[grid-auto-rows:minmax(0,1fr)]',
        'lg:grid-cols-2',
        'xl:grid-cols-2',
        className || '',
      ]
        .join(' ')
        .trim(),
    [className]
  );

  const noteWordCount = useMemo(() => {
    if (!notes) return 0;
    return notes.trim().split(/\s+/).filter(Boolean).length;
  }, [notes]);

  const transcriptStatus = recentTranscription ? 'Streaming live' : 'Standing by';

  const diagnoseButtonLabel = isLoadingDiagnosis ? 'Processing…' : 'Diagnose';

  return (
    <div className={containerClasses}>
      <div className="flex min-h-0 flex-col gap-6">
        <div className="relative overflow-hidden rounded-3xl border border-white/70 bg-gradient-to-br from-sky-50 via-white to-white p-6 shadow-lg ring-1 ring-white/70 backdrop-blur-sm dark:border-slate-700/50 dark:from-slate-900/80 dark:via-slate-900/60 dark:to-slate-900/40 dark:ring-slate-700/50">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-xs font-semibold tracking-[0.3em] text-sky-700 uppercase dark:text-sky-200">
                Recent transcription
              </span>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">{transcriptStatus}</p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-slate-600 shadow-sm ring-1 ring-white/80 dark:bg-slate-800/60 dark:text-slate-200 dark:ring-slate-700/50">
              <span className="size-2 rounded-full bg-sky-400" aria-hidden="true" />
              Auto-sync
            </span>
          </div>

          <div className="mt-4 min-h-[4.5rem] rounded-2xl border border-white/80 bg-white/80 px-4 py-3 font-mono text-sm leading-relaxed text-slate-700 shadow-sm ring-1 ring-white/70 backdrop-blur dark:border-slate-700/50 dark:bg-slate-900/60 dark:text-slate-100 dark:ring-slate-700/40">
            {recentTranscription || 'Waiting for transcription…'}
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-hidden rounded-3xl border border-white/70 bg-white/80 p-0 shadow-xl ring-1 ring-black/5 backdrop-blur dark:border-slate-700/60 dark:bg-slate-900/70 dark:ring-slate-800/60">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200/70 px-6 py-5 dark:border-slate-700/60">
            <div>
              <span className="text-xs font-semibold tracking-[0.3em] text-slate-500 uppercase dark:text-slate-300">
                Structured medical notes
              </span>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
                Synced in real time as the consultation progresses
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs font-medium text-slate-500 dark:text-slate-300">
              <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 ring-1 ring-white/80 dark:bg-slate-800/60 dark:ring-slate-700/50">
                <span className="size-2 rounded-full bg-emerald-400" aria-hidden="true" />
                {noteWordCount} words
              </span>
              <span className="hidden items-center gap-2 rounded-full bg-slate-100 px-3 py-1 ring-1 ring-white/80 md:inline-flex dark:bg-slate-800/60 dark:ring-slate-700/50">
                <span className="size-2 rounded-full bg-indigo-400" aria-hidden="true" />
                Markdown enabled
              </span>
            </div>
          </div>

          <div className="custom-scrollbar-light dark:custom-scrollbar h-full overflow-y-auto px-6 pt-4 pb-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={notes}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="prose prose-sm dark:prose-invert max-w-none leading-relaxed text-slate-700"
              >
                {notes ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({ children }) => (
                        <h1 className="mb-2 text-xl font-semibold text-slate-900 dark:text-white">
                          {children}
                        </h1>
                      ),
                      h2: ({ children }) => (
                        <h2 className="mt-6 mb-2 text-lg font-semibold text-slate-900 dark:text-white">
                          {children}
                        </h2>
                      ),
                      h3: ({ children }) => (
                        <h3 className="mt-4 mb-1 text-base font-semibold text-slate-800 dark:text-slate-100">
                          {children}
                        </h3>
                      ),
                      p: ({ children }) => (
                        <p className="mb-3 text-slate-700 dark:text-slate-200">{children}</p>
                      ),
                      ul: ({ children }) => (
                        <ul className="mb-3 ml-5 list-disc text-slate-700 dark:text-slate-200">
                          {children}
                        </ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="mb-3 ml-5 list-decimal text-slate-700 dark:text-slate-200">
                          {children}
                        </ol>
                      ),
                      li: ({ children }) => <li className="mb-1 leading-relaxed">{children}</li>,
                      strong: ({ children }) => (
                        <strong className="font-semibold text-slate-900 dark:text-white">
                          {children}
                        </strong>
                      ),
                      em: ({ children }) => <em className="italic">{children}</em>,
                      table: ({ children }) => (
                        <div className="mb-4 w-full overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700">
                          <table className="w-full border-collapse">{children}</table>
                        </div>
                      ),
                      thead: ({ children }) => (
                        <thead className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                          {children}
                        </thead>
                      ),
                      tbody: ({ children }) => <tbody>{children}</tbody>,
                      tr: ({ children }) => (
                        <tr className="border-b border-slate-200 last:border-0 dark:border-slate-700">
                          {children}
                        </tr>
                      ),
                      th: ({ children }) => (
                        <th className="border border-slate-200 px-3 py-2 text-left text-sm font-semibold text-slate-800 dark:border-slate-700 dark:text-slate-100">
                          {children}
                        </th>
                      ),
                      td: ({ children }) => (
                        <td className="border border-slate-200 px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-200">
                          {children}
                        </td>
                      ),
                    }}
                  >
                    {notes}
                  </ReactMarkdown>
                ) : (
                  <p className="text-sm text-slate-400 italic dark:text-slate-500">
                    Notes will populate automatically once the consultation begins.
                  </p>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-3xl border border-white/70 bg-white/80 p-6 shadow-xl ring-1 ring-black/5 backdrop-blur sm:min-h-[26rem] lg:min-h-0 dark:border-slate-700/60 dark:bg-slate-900/70 dark:ring-slate-800/60">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200/70 pb-5 dark:border-slate-700/60">
          <div>
            <span className="text-xs font-semibold tracking-[0.3em] text-slate-500 uppercase dark:text-slate-300">
              Diagnosis assistant
            </span>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-300">
              Request a draft differential without leaving the consultation.
            </p>
          </div>
          <Button
            size="sm"
            onClick={handleDiagnose}
            disabled={!notes || isLoadingDiagnosis}
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/25 transition hover:from-sky-500 hover:via-blue-500 hover:to-indigo-500 disabled:opacity-60"
          >
            {diagnoseButtonLabel}
          </Button>
        </div>

        <div className="mt-5 space-y-5 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-emerald-400" aria-hidden="true" />
            LiveKit agent channel ready
          </div>
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-slate-400" aria-hidden="true" />
            {notes ? 'Notes synced • Prompt context available' : 'Awaiting notes to build context'}
          </div>
        </div>

        <div className="custom-scrollbar-light mt-6 min-h-0 flex-1 overflow-y-auto rounded-2xl border border-white/70 bg-white/80 px-5 py-4 shadow-inner ring-1 ring-white/70 dark:border-slate-700/60 dark:bg-slate-900/60 dark:ring-slate-800/60">
          <AnimatePresence mode="wait">
            <motion.div
              key={diagnosis}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="prose prose-sm dark:prose-invert max-w-none leading-relaxed text-slate-700"
            >
              {isLoadingDiagnosis ? (
                <p className="text-sm text-slate-400 italic dark:text-slate-500">
                  Analyzing notes for potential diagnoses…
                </p>
              ) : diagnosis ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="mb-2 text-xl font-semibold text-slate-900 dark:text-white">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="mt-6 mb-2 text-lg font-semibold text-slate-900 dark:text-white">
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="mt-4 mb-1 text-base font-semibold text-slate-800 dark:text-slate-100">
                        {children}
                      </h3>
                    ),
                    p: ({ children }) => (
                      <p className="mb-3 text-slate-700 dark:text-slate-200">{children}</p>
                    ),
                    ul: ({ children }) => (
                      <ul className="mb-3 ml-5 list-disc text-slate-700 dark:text-slate-200">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="mb-3 ml-5 list-decimal text-slate-700 dark:text-slate-200">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => <li className="mb-1 leading-relaxed">{children}</li>,
                    strong: ({ children }) => (
                      <strong className="font-semibold text-slate-900 dark:text-white">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => <em className="italic">{children}</em>,
                    table: ({ children }) => (
                      <div className="mb-4 w-full overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700">
                        <table className="w-full border-collapse">{children}</table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                        {children}
                      </thead>
                    ),
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => (
                      <tr className="border-b border-slate-200 last:border-0 dark:border-slate-700">
                        {children}
                      </tr>
                    ),
                    th: ({ children }) => (
                      <th className="border border-slate-200 px-3 py-2 text-left text-sm font-semibold text-slate-800 dark:border-slate-700 dark:text-slate-100">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-slate-200 px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-200">
                        {children}
                      </td>
                    ),
                  }}
                >
                  {diagnosis}
                </ReactMarkdown>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Click “Diagnose” once notes are ready to generate differential summaries for quick
                  review.
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
