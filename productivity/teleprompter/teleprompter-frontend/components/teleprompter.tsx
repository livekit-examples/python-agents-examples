"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ConnectionState, RpcInvocationData } from "livekit-client";
import { useConnectionState, useMaybeRoomContext } from "@livekit/components-react";
import { Button } from "@/components/ui/button";

export interface TeleprompterProps {
  typingSpeed?: number;
}

const DEFAULT_SCRIPT = `Welcome to the teleprompter demo!

This is where you can type your script. When you switch to teleprompter mode and start speaking, the text will automatically scroll based on what you say.

Try reading this text aloud and watch as the teleprompter follows along with your speech. The system will match your spoken words to the text and automatically scroll to keep up with your pace.

You can edit this text in edit mode, then switch to teleprompter mode to use it as your script.`;

export function Teleprompter({ typingSpeed = 50 }: TeleprompterProps) {
  const [isEditMode, setIsEditMode] = useState<boolean>(true);
  const [scriptText, setScriptText] = useState<string>(DEFAULT_SCRIPT);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState<number>(0);
  const [sentences, setSentences] = useState<string[]>([]);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const highlightedSentenceRef = useRef<HTMLDivElement>(null);
  const state = useConnectionState();
  const room = useMaybeRoomContext();

  // Split text into sentences when script changes
  useEffect(() => {
    // Split by sentence endings but preserve the structure
    const parts: Array<{text: string, isSentence: boolean}> = [];
    let lastIndex = 0;
    
    // Match sentences but keep track of positions
    const sentenceRegex = /[^.!?\n]+[.!?]+/g;
    let match;
    
    while ((match = sentenceRegex.exec(scriptText)) !== null) {
      // Add any non-sentence content before this sentence (like newlines)
      if (match.index > lastIndex) {
        const betweenText = scriptText.substring(lastIndex, match.index);
        if (betweenText.trim() || betweenText.includes('\n')) {
          parts.push({ text: betweenText, isSentence: false });
        }
      }
      
      // Add the sentence
      parts.push({ text: match[0].trim(), isSentence: true });
      lastIndex = match.index + match[0].length;
    }
    
    // Add any remaining content
    if (lastIndex < scriptText.length) {
      const remaining = scriptText.substring(lastIndex);
      if (remaining.trim() || remaining.includes('\n')) {
        parts.push({ text: remaining, isSentence: false });
      }
    }
    
    // Extract just the sentences for matching, but keep the parts for rendering
    const sentenceTexts = parts.filter(p => p.isSentence).map(p => p.text);
    setSentences(sentenceTexts);
    
    // Store the full parts structure for rendering
    (window as any).__teleprompterParts = parts;
  }, [scriptText]);

  // Scroll to current sentence when it changes or when entering teleprompter mode
  useEffect(() => {
    if (!isEditMode && currentSentenceIndex >= 0) {
      // Add a small delay when first entering teleprompter mode
      const timeoutId = setTimeout(() => {
        scrollToSentence(currentSentenceIndex);
      }, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [currentSentenceIndex, isEditMode]);

  // Register RPC handler for receiving transcripts
  useEffect(() => {
    if (!room || !room.localParticipant) return;

    const handleReceiveTranscript = async (rpcInvocation: RpcInvocationData): Promise<string> => {
      try {
        // Parse the payload (it comes as a JSON string from Python)
        const payload = JSON.parse(rpcInvocation.payload);
        
        if (payload && payload.transcript) {
          // Find which sentence matches the transcript
          const matchingSentenceIndex = findMatchingSentence(sentences, payload.transcript, currentSentenceIndex);
          if (matchingSentenceIndex >= 0) {
            // Move to the NEXT sentence after the one that was spoken
            const nextSentenceIndex = matchingSentenceIndex + 1;
            if (nextSentenceIndex < sentences.length && nextSentenceIndex !== currentSentenceIndex) {
              setCurrentSentenceIndex(nextSentenceIndex);
              scrollToSentence(nextSentenceIndex);
            }
          }
          return "Success: Transcript processed";
        } else {
          return "Error: Invalid transcript data format";
        }
      } catch (error) {
        return "Error: " + (error instanceof Error ? error.message : String(error));
      }
    };

    room.localParticipant.registerRpcMethod("receive_transcript", handleReceiveTranscript);

    return () => {
      if (room && room.localParticipant) {
        room.localParticipant.unregisterRpcMethod("receive_transcript");
      }
    };
  }, [room, sentences, currentSentenceIndex]);

  const findMatchingSentence = (sentences: string[], transcript: string, currentIndex: number): number => {
    const lowerTranscript = transcript.toLowerCase().trim();
    
    // First check if we're still in the current sentence
    if (currentIndex < sentences.length) {
      const currentSentence = sentences[currentIndex].toLowerCase();
      if (currentSentence.includes(lowerTranscript) || lowerTranscript.includes(currentSentence)) {
        return currentIndex;
      }
    }
    
    // Check the next sentence
    if (currentIndex + 1 < sentences.length) {
      const nextSentence = sentences[currentIndex + 1].toLowerCase();
      // Check if transcript contains significant portion of next sentence
      const words = nextSentence.split(/\s+/).filter(w => w.length > 2);
      const matchingWords = words.filter(word => lowerTranscript.includes(word));
      
      if (matchingWords.length >= Math.min(3, words.length * 0.5)) {
        return currentIndex + 1;
      }
    }
    
    // Fallback: search all sentences for best match
    let bestMatch = -1;
    let bestScore = 0;
    
    sentences.forEach((sentence, index) => {
      const lowerSentence = sentence.toLowerCase();
      const words = lowerSentence.split(/\s+/).filter(w => w.length > 2);
      const matchingWords = words.filter(word => lowerTranscript.includes(word));
      const score = matchingWords.length / words.length;
      
      if (score > bestScore && score > 0.5) {
        bestScore = score;
        bestMatch = index;
      }
    });
    
    return bestMatch;
  };

  const scrollToSentence = (sentenceIndex: number) => {
    // Use setTimeout to ensure DOM has updated
    setTimeout(() => {
      if (highlightedSentenceRef.current && containerRef.current) {
        const container = containerRef.current;
        const highlighted = highlightedSentenceRef.current;
        
        // Get the container's visible height and the highlighted element's position
        const containerHeight = container.clientHeight;
        const containerScrollTop = container.scrollTop;
        const highlightedOffsetTop = highlighted.offsetTop;
        const highlightedHeight = highlighted.clientHeight;
        
        // Calculate the center position of the container
        const containerCenter = containerHeight / 2;
        
        // Calculate where to scroll so the highlighted element is centered
        const targetScrollTop = highlightedOffsetTop - containerCenter + (highlightedHeight / 2);
        
        container.scrollTo({
          top: Math.max(0, targetScrollTop),
          behavior: 'smooth'
        });
      }
    }, 50); // Slightly longer delay to ensure DOM is ready
  };

  const handleModeToggle = () => {
    setIsEditMode(!isEditMode);
    if (isEditMode) {
      // When entering teleprompter mode, reset to first sentence
      setCurrentSentenceIndex(0);
      // The useEffect will handle scrolling automatically
    }
  };

  const renderHighlightedText = () => {
    const parts = (window as any).__teleprompterParts || [];
    let sentenceIndex = 0;
    
    return (
      <div className="whitespace-pre-wrap font-mono text-lg leading-8 p-3 relative">
        {/* Add padding to allow first sentence to be centered */}
        <div className="h-[18vh]" />
        {parts.map((part: {text: string, isSentence: boolean}, index: number) => {
          if (part.isSentence) {
            const currentIdx = sentenceIndex;
            sentenceIndex++;
            return (
              <span
                key={index}
                ref={currentIdx === currentSentenceIndex ? highlightedSentenceRef : null}
                className={`inline-block ${currentIdx === currentSentenceIndex ? 'bg-white/10 text-white px-2 py-1 rounded' : 'text-white/50'} transition-all duration-300`}
              >
                {part.text}
              </span>
            );
          } else {
            // Render non-sentence content (like newlines) as-is
            return (
              <span key={index} className="text-white/50">
                {part.text}
              </span>
            );
          }
        })}
        {/* Add padding to allow last sentences to be centered */}
        <div className="h-[18vh]" />
      </div>
    );
  };

  return (
    <div className="relative h-full flex flex-col">
      <div className="flex justify-between items-center p-3 border-b border-white/20">
        <h2 className="text-lg font-semibold">
          {isEditMode ? "Edit Mode" : "Teleprompter Mode"}
        </h2>
        <Button
          onClick={handleModeToggle}
          className="px-4 py-2"
          state={state === ConnectionState.Connected || isEditMode ? "primary" : "default"}
          disabled={state !== ConnectionState.Connected && !isEditMode}
        >
          {isEditMode ? "Switch to Teleprompter" : "Switch to Edit"}
        </Button>
      </div>
      
      <div className="flex-1 overflow-hidden relative">
        <AnimatePresence mode="wait">
          {isEditMode ? (
            <motion.div
              key="edit"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full"
            >
              <textarea
                ref={textAreaRef}
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                className="w-full h-full p-3 bg-transparent text-white font-mono text-lg leading-7 resize-none focus:outline-none"
                placeholder="Type your script here..."
              />
            </motion.div>
          ) : (
            <motion.div
              key="teleprompter"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full relative"
            >
              <div className="h-full overflow-y-auto" ref={containerRef}>
                {renderHighlightedText()}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {!isEditMode && state !== ConnectionState.Connected && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <p className="text-white/60 text-center max-w-md">
              Connect to start using the teleprompter. Your speech will be matched to the script and it will auto-scroll.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}