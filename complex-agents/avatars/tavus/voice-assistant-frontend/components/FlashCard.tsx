import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";

export interface FlashCardData {
  id: string;
  question: string;
  answer: string;
  isFlipped?: boolean;
}

interface FlashCardProps {
  card: FlashCardData;
  onFlip?: (id: string) => void;
}

export default function FlashCard({ card, onFlip }: FlashCardProps) {
  const [isFlipped, setIsFlipped] = useState(card.isFlipped || false);

  // Update local state when card prop changes
  useEffect(() => {
    setIsFlipped(card.isFlipped || false);
  }, [card.isFlipped]);

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
    if (onFlip) {
      onFlip(card.id);
    }
  };

  return (
    <div 
      className="w-full max-w-md mx-auto cursor-pointer"
      onClick={handleFlip}
    >
      <AnimatePresence mode="wait" initial={false}>
        {!isFlipped ? (
          <motion.div
            key="front"
            className="bg-white text-black p-6 rounded-lg shadow-lg"
            initial={{ rotateY: 90 }}
            animate={{ rotateY: 0 }}
            exit={{ rotateY: 90 }}
            transition={{ duration: 0.3 }}
          >
            <h3 className="text-lg font-semibold mb-2">Question</h3>
            <p>{card.question}</p>
          </motion.div>
        ) : (
          <motion.div
            key="back"
            className="bg-blue-100 text-black p-6 rounded-lg shadow-lg"
            initial={{ rotateY: 90 }}
            animate={{ rotateY: 0 }}
            exit={{ rotateY: 90 }}
            transition={{ duration: 0.3 }}
          >
            <h3 className="text-lg font-semibold mb-2">Answer</h3>
            <p>{card.answer}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
