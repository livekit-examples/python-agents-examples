import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRoomContext, useVoiceAssistant } from "@livekit/components-react";
import Quiz, { QuizQuestion, QuizAnswer } from "./Quiz";

export interface SubmittedQuiz {
  id: string;
  questions: QuizQuestion[];
  answers: Record<string, string>;
}

export default function QuizContainer() {
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [quizId, setQuizId] = useState<string | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const room = useRoomContext();
  const { agent } = useVoiceAssistant();

  useEffect(() => {
    if (!room) return;

    // Register RPC method to receive quizzes
    const handleShowQuiz = async (data: any): Promise<string> => {
      try {
        console.log("Received quiz RPC data:", data);
        
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
          // Reset answers when showing a new quiz
          setSelectedAnswers({});
          setQuizId(payload.id);
          setQuestions(payload.questions);
          setCurrentQuestionIndex(0);
          setIsVisible(true);
        } else if (payload.action === "hide") {
          setIsVisible(false);
        }
        
        return "Success";
      } catch (error) {
        console.error("Error processing quiz data:", error);
        return "Error: " + (error instanceof Error ? error.message : String(error));
      }
    };

    room.localParticipant.registerRpcMethod(
      "client.quiz",
      handleShowQuiz
    );

    return () => {
      // Clean up RPC method when component unmounts
      room.localParticipant.unregisterRpcMethod("client.quiz");
    };
  }, [room]);

  const handleAnswerSelect = (questionId: string, answerId: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answerId
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!agent || !quizId) return;
    
    try {
      console.log(`Submitting quiz ${quizId} to agent ${agent.identity}`);
      
      const payload = {
        id: quizId,
        answers: selectedAnswers
      };
      
      const result = await room.localParticipant.performRpc({
        destinationIdentity: agent.identity,
        method: "agent.submitQuiz",
        payload: JSON.stringify(payload)
      });
      
      console.log(`Quiz submission result: ${result}`);
      
      // Hide the quiz after submission
      setIsVisible(false);
    } catch (error: unknown) {
      console.error("Error submitting quiz:", error);
      if (error instanceof Error) {
        console.error(error.stack);
      }
    }
  };

  const currentQuestion = currentQuestionIndex !== null && questions[currentQuestionIndex] 
    ? questions[currentQuestionIndex] 
    : null;

  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const allQuestionsAnswered = questions.length > 0 && 
    questions.every(q => selectedAnswers[q.id] !== undefined);

  return (
    <AnimatePresence>
      {isVisible && currentQuestion && (
        <motion.div
          initial={{ opacity: 0, x: -100 }} // Start from left
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -100 }}
          className="fixed left-8 top-1/4 w-80 bg-gray-900 p-4 rounded-lg shadow-lg"
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Quiz</h2>
            <button 
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>
          
          <Quiz 
            question={currentQuestion} 
            selectedAnswerId={selectedAnswers[currentQuestion.id]}
            onAnswerSelect={(answerId) => handleAnswerSelect(currentQuestion.id, answerId)}
          />
          
          <div className="flex justify-between mt-4">
            <button
              onClick={() => setCurrentQuestionIndex(prev => 
                prev !== null ? Math.max(0, prev - 1) : 0
              )}
              disabled={currentQuestionIndex === 0}
              className="px-3 py-1 bg-blue-600 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <span>{(currentQuestionIndex ?? 0) + 1} / {questions.length}</span>
            {!isLastQuestion ? (
              <button
                onClick={() => setCurrentQuestionIndex(prev => 
                  prev !== null ? Math.min(questions.length - 1, prev + 1) : 0
                )}
                className="px-3 py-1 bg-blue-600 rounded"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmitQuiz}
                disabled={!allQuestionsAnswered}
                className="px-3 py-1 bg-green-600 rounded disabled:opacity-50"
              >
                Submit Quiz
              </button>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
