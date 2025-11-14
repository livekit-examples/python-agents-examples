"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import { motion } from "framer-motion";
import { ConnectionState } from "livekit-client";
import { useTranscriber } from "@/hooks/use-transcriber";

export interface TypewriterProps {
  typingSpeed?: number;
}

const emptyText =
  "Voice transcription will appear after you connect and start talking";

export function Typewriter({ typingSpeed = 50 }: TypewriterProps) {
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const { state, transcriptions } = useTranscriber();
  const [displayedText, setDisplayedText] = useState<string>("");
  const [currentIndex, setCurrentIndex] = useState<number>(0);

  const transcriptionEndRef = useRef<HTMLDivElement>(null);
  const text = useMemo(() =>
    Object.values(transcriptions)
      .toSorted((a, b) => a.firstReceivedTime - b.firstReceivedTime)
      .map((t) => t.text.trim())
      .join("\n"),
    [transcriptions],
  );

  useEffect(() => {
    if (text.length === 0) {
      setDisplayedText("");
      setCurrentIndex(0);
      return;
    }

    if (currentIndex < text.length) {
      if (!isTyping) {
        setIsTyping(true);
      }
      const timeout = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex) + text[currentIndex]);
        setCurrentIndex((prev) => prev + 1);
        transcriptionEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, typingSpeed);
      return () => clearTimeout(timeout);
    } else {
      setIsTyping(false);
    }
  }, [currentIndex, text, typingSpeed, isTyping]);

  const emptyTextIntro = useMemo(() => {
    return emptyText.split("").map((word, index) => {
      return (
        <motion.span
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            duration: 0.2,
            delay: index * 0.015,
          }}
          key={index}
        >
          {word}
        </motion.span>
      );
    });
  }, []);

  return (
    <div className="relative h-full text-lg font-mono pl-3 relative pt-2 pb-16">
      <div className="pointer-events-none h-1/4 absolute top-0 left-0 w-full bg-gradient-to-b from-accent-bg to-transparent"></div>
      {state === ConnectionState.Disconnected && (
        <div className="text-white/40 h-full items-center pb-16 max-w-md flex">
          <p>{emptyTextIntro}</p>
        </div>
      )}
      {state !== ConnectionState.Disconnected && (
        <div className="h-full overflow-y-auto">
          <div className="h-48" />
          <motion.p
            className="mr-2 whitespace-pre-wrap"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
          >
            {displayedText}{" "}
            <motion.span
              animate={!isTyping && { opacity: [1, 0, 1] }}
              transition={{ duration: 0.5, delay: 0.2, repeat: Infinity }}
              className="relative inline-block w-3 h-3 rounded-full bg-white"
            />
          </motion.p>
          <div ref={transcriptionEndRef} className="h-1/2" />
        </div>
      )}
    </div>
  );
}
