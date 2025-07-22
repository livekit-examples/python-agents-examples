import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import FlashCard, { FlashCardData } from "./FlashCard";
import { useRoomContext, useVoiceAssistant } from "@livekit/components-react";

export default function FlashCardContainer() {
  const [flashCards, setFlashCards] = useState<FlashCardData[]>([]);
  const [currentCardIndex, setCurrentCardIndex] = useState<number | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const room = useRoomContext();
  const { agent } = useVoiceAssistant();

  useEffect(() => {
    if (!room) return;

    // Register RPC method to receive flash cards
    const handleShowFlashCard = async (data: any): Promise<string> => {
      try {
        console.log("Received flashcard RPC data:", data);
        
        // Check for the correct property in the RPC data
        if (!data || data.payload === undefined) {
          console.error("Invalid RPC data received:", data);
          return "Error: Invalid RPC data format";
        }
        
        console.log("Parsing payload:", data.payload);
        
        // Parse the payload string into a JSON object
        const payload = typeof data.payload === 'string' 
          ? JSON.parse(data.payload) 
          : data.payload;
        
        if (payload.action === "show") {
          const newCard: FlashCardData = {
            id: payload.id,
            question: payload.question,
            answer: payload.answer,
            isFlipped: false
          };
          
          setFlashCards(prev => {
            // Check if card with same ID already exists
            const exists = prev.some(card => card.id === newCard.id);
            if (exists) {
              return prev.map(card => 
                card.id === newCard.id ? newCard : card
              );
            } else {
              return [...prev, newCard];
            }
          });
          
          setCurrentCardIndex(payload.index !== undefined ? payload.index : flashCards.length);
          setIsVisible(true);
        } else if (payload.action === "flip") {
          setFlashCards(prev => 
            prev.map(card => 
              card.id === payload.id 
                ? { ...card, isFlipped: !card.isFlipped } 
                : card
            )
          );
        } else if (payload.action === "hide") {
          setIsVisible(false);
        }
        
        return "Success";
      } catch (error) {
        console.error("Error processing flash card data:", error);
        return "Error: " + (error instanceof Error ? error.message : String(error));
      }
    };

    room.localParticipant.registerRpcMethod(
      "client.flashcard",
      handleShowFlashCard
    );

    return () => {
      // Clean up RPC method when component unmounts
      room.localParticipant.unregisterRpcMethod("client.flashcard");
    };
  }, [room, flashCards.length]);

  const handleFlip = async (id: string) => {
    try {
      // Use the agent from the voice assistant hook
      if (agent) {
        console.log(`Sending flip request to agent ${agent.identity} for card ID: ${id}`);
        
        // Use the correct RPC pattern and ensure proper payload formatting
        const result = await room.localParticipant.performRpc({
          destinationIdentity: agent.identity,
          method: "agent.flipFlashCard",
          payload: JSON.stringify({ id })
        });
        
        console.log(`RPC call result: ${result}`);
        
        // Also update the local state for immediate feedback
        setFlashCards(prev => 
          prev.map(card => 
            card.id === id 
              ? { ...card, isFlipped: !card.isFlipped } 
              : card
          )
        );
      } else {
        console.error("Agent not found in the room");
      }
    } catch (error: unknown) {
      console.error("Error flipping card:", error);
      if (error instanceof Error) {
        console.error(error.stack);
      }
    }
  };

  const currentCard = currentCardIndex !== null && flashCards[currentCardIndex] 
    ? flashCards[currentCardIndex] 
    : null;

  return (
    <AnimatePresence>
      {isVisible && currentCard && (
        <motion.div
          initial={{ opacity: 0, x: 100 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 100 }}
          className="fixed right-8 top-1/4 w-80 bg-gray-900 p-4 rounded-lg shadow-lg"
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Flash Card</h2>
            <button 
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>
          
          <FlashCard card={currentCard} onFlip={handleFlip} />
          
          {flashCards.length > 1 && (
            <div className="flex justify-between mt-4">
              <button
                onClick={() => setCurrentCardIndex(prev => 
                  prev !== null ? Math.max(0, prev - 1) : 0
                )}
                disabled={currentCardIndex === 0}
                className="px-3 py-1 bg-blue-600 rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span>{(currentCardIndex ?? 0) + 1} / {flashCards.length}</span>
              <button
                onClick={() => setCurrentCardIndex(prev => 
                  prev !== null ? Math.min(flashCards.length - 1, prev + 1) : 0
                )}
                disabled={currentCardIndex === flashCards.length - 1}
                className="px-3 py-1 bg-blue-600 rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
