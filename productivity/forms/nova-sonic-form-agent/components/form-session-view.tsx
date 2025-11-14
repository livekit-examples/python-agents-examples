'use client';

import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Room, RoomEvent, RpcInvocationData } from 'livekit-client';
import { useRoomContext, type ReceivedChatMessage } from '@livekit/components-react';
import { AgentControlBar } from '@/components/livekit/agent-control-bar/agent-control-bar';
import { MediaTiles } from '@/components/livekit/media-tiles';
import { ChatEntry } from '@/components/livekit/chat/chat-entry';
import useChatAndTranscription from '@/hooks/useChatAndTranscription';
import { useDebugMode } from '@/hooks/useDebug';
import { cn } from '@/lib/utils';
import { toastAlert } from '@/components/alert-toast';

interface SessionViewProps {
  disabled: boolean;
  capabilities: {
    supportsChatInput: boolean;
    supportsVideoInput: boolean;
    supportsScreenShare: boolean;
  };
  sessionStarted: boolean;
}

interface FormData {
  // Professional Experience
  currentRole: string;
  company: string;
  yearsExperience: string;
  keyAchievements: string;
  
  
  // Interview Questions
  whyInterested: string;
  strengths: string;
  challengeExample: string;
  careerGoals: string;
  questionsForUs: string;
}

const initialFormData: FormData = {
  currentRole: '',
  company: '',
  yearsExperience: '',
  keyAchievements: '',
  whyInterested: '',
  strengths: '',
  challengeExample: '',
  careerGoals: '',
  questionsForUs: '',
};

export const FormSessionView = ({
  disabled,
  capabilities,
  sessionStarted,
  ref,
}: React.ComponentProps<'div'> & SessionViewProps) => {
  const [chatOpen, setChatOpen] = useState(false);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [activeSection, setActiveSection] = useState<string>('personal');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const { messages, send } = useChatAndTranscription();
  const room = useRoomContext();

  useDebugMode();

  // Auto-scroll transcript container when new messages arrive
  useEffect(() => {
    const container = document.getElementById('transcript-container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages]);

  // Register RPC handlers
  useEffect(() => {
    if (!room || !room.localParticipant) return;

    const handleFormUpdate = async (rpcInvocation: RpcInvocationData): Promise<string> => {
      try {
        const payload = JSON.parse(rpcInvocation.payload);
        console.log('Received form update RPC:', payload);

        if (payload.action === 'updateField') {
          const { field, value } = payload;
          setFormData(prev => ({
            ...prev,
            [field]: value
          }));
          return JSON.stringify({ status: 'success', message: `Updated ${field}` });
        } else if (payload.action === 'updateMultipleFields') {
          const { fields } = payload;
          setFormData(prev => ({
            ...prev,
            ...fields
          }));
          return JSON.stringify({ status: 'success', message: 'Updated multiple fields' });
        } else if (payload.action === 'highlightSection') {
          setActiveSection(payload.section);
          // Scroll to the highlighted section
          setTimeout(() => {
            const sectionMap: Record<string, string> = {
              'personal': 'Basic Information',
              'experience': 'Professional Experience',
              'questions': 'Interview Questions'
            };
            const sectionTitle = sectionMap[payload.section];
            if (sectionTitle) {
              const elements = document.querySelectorAll('h2');
              const targetElement = Array.from(elements).find(el => el.textContent === sectionTitle);
              if (targetElement) {
                const container = targetElement.closest('.form-section');
                if (container) {
                  // Get the container element that has the scrollbar
                  const scrollContainer = document.querySelector('.overflow-y-auto');
                  if (scrollContainer) {
                    const containerTop = container.getBoundingClientRect().top;
                    const scrollContainerTop = scrollContainer.getBoundingClientRect().top;
                    const scrollTop = containerTop - scrollContainerTop + scrollContainer.scrollTop - 20; // 20px padding
                    scrollContainer.scrollTo({
                      top: scrollTop,
                      behavior: 'smooth'
                    });
                  }
                }
              }
            }
          }, 3000); // Wait 3 seconds before scrolling so user can see what they wrote
          return JSON.stringify({ status: 'success', message: `Highlighted ${payload.section}` });
        } else if (payload.action === 'submitForm') {
          const { formType, data } = payload;
          console.log(`Form ${formType} submitted with data:`, data);
          setIsSubmitted(true);
          return JSON.stringify({ status: 'success', message: 'Form submitted' });
        }

        return JSON.stringify({ status: 'error', message: 'Unknown action' });
      } catch (error) {
        console.error('Error processing form update RPC:', error);
        return JSON.stringify({ 
          status: 'error', 
          message: error instanceof Error ? error.message : String(error) 
        });
      }
    };

    console.log('Registering RPC method: client.updateForm');
    room.localParticipant.registerRpcMethod('client.updateForm', handleFormUpdate);

    return () => {
      if (room && room.localParticipant) {
        console.log('Unregistering RPC method: client.updateForm');
        room.localParticipant.unregisterRpcMethod('client.updateForm');
      }
    };
  }, [room]);

  async function handleSendMessage(message: string) {
    await send(message);
  }

  return (
    <main
      ref={ref}
      inert={disabled}
      className="h-screen flex flex-col lg:flex-row overflow-hidden"
    >
      {/* Left side - Form */}
      <div className="flex-1 lg:w-1/2 overflow-y-auto px-4 pt-20 pb-40 lg:border-r border-border">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: sessionStarted ? 1 : 0, y: sessionStarted ? 0 : 20 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="space-y-6 max-w-2xl mx-auto"
        >
          {isSubmitted ? (
            <div className="flex items-center justify-center h-full min-h-[60vh]">
              <h1 className="text-4xl font-bold text-cyan-500">Application Submitted!</h1>
            </div>
          ) : (
            <>
              <h1 className="text-3xl font-bold mb-8">Job Application Form</h1>
          
          {/* Professional Experience Section */}
          <div className={cn(
            "form-section",
            activeSection === 'experience' && "active"
          )}>
            <h2>Professional Experience</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Current Role</label>
                <input
                  type="text"
                  value={formData.currentRole}
                  readOnly
                  className="form-input"
                  placeholder="What's your current position?"
                />
              </div>
              <div>
                <label className="form-label">Company</label>
                <input
                  type="text"
                  value={formData.company}
                  readOnly
                  className="form-input"
                  placeholder="Where do you work?"
                />
              </div>
              <div>
                <label className="form-label">Years of Experience</label>
                <input
                  type="text"
                  value={formData.yearsExperience}
                  readOnly
                  className="form-input"
                  placeholder="How many years of experience?"
                />
              </div>
              <div className="md:col-span-2">
                <label className="form-label">Key Achievements</label>
                <textarea
                  value={formData.keyAchievements}
                  readOnly
                  className="form-input min-h-[100px]"
                  placeholder="Share your major accomplishments"
                />
              </div>
            </div>
          </div>


          {/* Interview Questions Section */}
          <div className={cn(
            "form-section",
            activeSection === 'questions' && "active"
          )}>
            <h2>Interview Questions</h2>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="form-label">Why are you interested in this position?</label>
                <textarea
                  value={formData.whyInterested}
                  readOnly
                  className="form-input min-h-[100px]"
                  placeholder="Share your motivation for applying"
                />
              </div>
              <div>
                <label className="form-label">What are your greatest strengths?</label>
                <textarea
                  value={formData.strengths}
                  readOnly
                  className="form-input min-h-[80px]"
                  placeholder="Describe your key strengths"
                />
              </div>
              <div>
                <label className="form-label">Describe a challenging situation and how you handled it</label>
                <textarea
                  value={formData.challengeExample}
                  readOnly
                  className="form-input min-h-[100px]"
                  placeholder="Share a specific example"
                />
              </div>
              <div>
                <label className="form-label">Where do you see yourself in 5 years?</label>
                <textarea
                  value={formData.careerGoals}
                  readOnly
                  className="form-input min-h-[80px]"
                  placeholder="Describe your career goals"
                />
              </div>
              <div>
                <label className="form-label">Do you have any questions for us?</label>
                <textarea
                  value={formData.questionsForUs}
                  readOnly
                  className="form-input min-h-[80px]"
                  placeholder="What would you like to know about the role or company?"
                />
              </div>
            </div>
          </div>

          {/* Status Indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{
              opacity: sessionStarted && messages.length === 0 ? 1 : 0,
              transition: {
                ease: 'easeIn',
                delay: messages.length > 0 ? 0 : 0.8,
                duration: messages.length > 0 ? 0.2 : 0.5,
              },
            }}
            className="text-center mt-8"
          >
            <p className="animate-text-shimmer inline-block !bg-clip-text text-sm font-semibold text-transparent">
              The interviewer is ready, please introduce yourself to begin the application
            </p>
          </motion.div>
            </>
          )}
        </motion.div>
      </div>

      {/* Right side - Agent Visualizer and Transcripts */}
      <div className="flex-1 lg:w-1/2 bg-muted relative h-[50vh] lg:h-full pb-24 flex flex-col">
        <div className="flex-shrink-0">
          <MediaTiles chatOpen={chatOpen} />
        </div>
        
        {/* Transcript Area */}
        <div className="flex-1 overflow-y-auto px-4 py-4 pb-32" id="transcript-container">
          <div className="space-y-3 max-w-2xl mx-auto">
            <AnimatePresence>
              {messages.map((message: ReceivedChatMessage) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 1, height: 'auto', translateY: 0.001 }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                >
                  <ChatEntry hideName key={message.id} entry={message} />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="bg-background fixed right-0 bottom-0 left-0 z-50 px-3 pt-2 pb-3 md:px-12 md:pb-12">
        <motion.div
          key="control-bar"
          initial={{ opacity: 0, translateY: '100%' }}
          animate={{
            opacity: sessionStarted ? 1 : 0,
            translateY: sessionStarted ? '0%' : '100%',
          }}
          transition={{ duration: 0.3, delay: sessionStarted ? 0.5 : 0, ease: 'easeOut' }}
        >
          <div className="relative z-10 mx-auto w-full max-w-4xl">
            <AgentControlBar
              capabilities={capabilities}
              onChatOpenChange={setChatOpen}
              onSendMessage={handleSendMessage}
            />
          </div>
          <div className="from-background border-background absolute top-0 left-0 h-12 w-full -translate-y-full bg-gradient-to-t to-transparent" />
        </motion.div>
      </div>
    </main>
  );
};