'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AnimatePresence, motion } from 'motion/react';
import remarkGfm from 'remark-gfm';
import { useMaybeRoomContext } from '@livekit/components-react';

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
        const response = await room.localParticipant.performRpc({
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

  return (
    <div className={`flex h-full gap-6 ${className || ''}`}>
      {/* Left side - Original content */}
      <div className="flex flex-1 flex-col gap-6">
        {/* Recent Transcription Section */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-lg">
          <h3 className="mb-3 text-lg font-semibold text-gray-900">Recent Transcription</h3>
          <AnimatePresence mode="wait">
            <motion.div
              key={recentTranscription}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="min-h-[4rem] font-mono leading-relaxed text-gray-600"
            >
              {recentTranscription || 'Waiting for transcription...'}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Medical Notes Section */}
        <div className="flex-1 overflow-hidden rounded-xl border border-gray-200 bg-white p-6 shadow-lg">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Medical Notes</h3>
          <div className="custom-scrollbar-light h-full overflow-y-auto pr-2">
            <AnimatePresence mode="wait">
              <motion.div
                key={notes}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="prose prose-sm max-w-none leading-relaxed text-gray-700"
              >
                {notes ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({ children }) => (
                        <h1 className="mb-2 text-xl font-bold text-gray-900">{children}</h1>
                      ),
                      h2: ({ children }) => (
                        <h2 className="mt-4 mb-2 text-lg font-semibold text-gray-900">
                          {children}
                        </h2>
                      ),
                      h3: ({ children }) => (
                        <h3 className="mt-3 mb-1 text-base font-semibold text-gray-800">
                          {children}
                        </h3>
                      ),
                      p: ({ children }) => <p className="mb-2 text-gray-700">{children}</p>,
                      ul: ({ children }) => (
                        <ul className="mb-2 ml-5 list-disc text-gray-700">{children}</ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="mb-2 ml-5 list-decimal text-gray-700">{children}</ol>
                      ),
                      li: ({ children }) => <li className="mb-1">{children}</li>,
                      strong: ({ children }) => (
                        <strong className="font-semibold text-gray-900">{children}</strong>
                      ),
                      em: ({ children }) => <em className="italic">{children}</em>,
                      table: ({ children }) => (
                        <table className="mb-4 w-full border-collapse">
                          <tbody>{children}</tbody>
                        </table>
                      ),
                      thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
                      tbody: ({ children }) => <tbody>{children}</tbody>,
                      tr: ({ children }) => (
                        <tr className="border-b border-gray-200">{children}</tr>
                      ),
                      th: ({ children }) => (
                        <th className="border border-gray-300 px-3 py-2 text-left font-semibold text-gray-900">
                          {children}
                        </th>
                      ),
                      td: ({ children }) => (
                        <td className="border border-gray-300 px-3 py-2 text-gray-700">
                          {children}
                        </td>
                      ),
                    }}
                  >
                    {notes}
                  </ReactMarkdown>
                ) : (
                  <p className="text-gray-500 italic">
                    No notes yet. Start speaking to generate medical notes...
                  </p>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Right side - Diagnosis Section */}
      <div className="flex flex-1 flex-col rounded-xl border border-gray-200 bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Diagnosis Assistant</h3>
          <button
            onClick={handleDiagnose}
            disabled={!notes || isLoadingDiagnosis}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            {isLoadingDiagnosis ? 'Processing...' : 'Diagnose'}
          </button>
        </div>

        <div className="custom-scrollbar-light flex-1 overflow-y-auto pr-2">
          <AnimatePresence mode="wait">
            <motion.div
              key={diagnosis}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="prose prose-sm max-w-none leading-relaxed text-gray-700"
            >
              {isLoadingDiagnosis ? (
                <p className="text-gray-500 italic">Analyzing notes for potential diagnoses...</p>
              ) : diagnosis ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="mb-2 text-xl font-bold text-gray-900">{children}</h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="mt-4 mb-2 text-lg font-semibold text-gray-900">{children}</h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="mt-3 mb-1 text-base font-semibold text-gray-800">
                        {children}
                      </h3>
                    ),
                    p: ({ children }) => <p className="mb-2 text-gray-700">{children}</p>,
                    ul: ({ children }) => (
                      <ul className="mb-2 ml-5 list-disc text-gray-700">{children}</ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="mb-2 ml-5 list-decimal text-gray-700">{children}</ol>
                    ),
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                    strong: ({ children }) => (
                      <strong className="font-semibold text-gray-900">{children}</strong>
                    ),
                    em: ({ children }) => <em className="italic">{children}</em>,
                    table: ({ children }) => (
                      <table className="mb-4 w-full border-collapse">
                        <tbody>{children}</tbody>
                      </table>
                    ),
                    thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => <tr className="border-b border-gray-200">{children}</tr>,
                    th: ({ children }) => (
                      <th className="border border-gray-300 px-3 py-2 text-left font-semibold text-gray-900">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-gray-300 px-3 py-2 text-gray-700">{children}</td>
                    ),
                  }}
                >
                  {diagnosis}
                </ReactMarkdown>
              ) : (
                <p className="text-gray-500 italic">
                  Click &quot;Diagnose&quot; to analyze the medical notes and generate potential
                  diagnoses based on the symptoms and history discussed.
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
