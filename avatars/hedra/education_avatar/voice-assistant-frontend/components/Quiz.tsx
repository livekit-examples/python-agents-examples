import { motion } from "framer-motion";

export interface QuizAnswer {
  id: string;
  text: string;
}

export interface QuizQuestion {
  id: string;
  text: string;
  answers: QuizAnswer[];
}

interface QuizProps {
  question: QuizQuestion;
  selectedAnswerId: string | undefined;
  onAnswerSelect: (answerId: string) => void;
}

export default function Quiz({ question, selectedAnswerId, onAnswerSelect }: QuizProps) {
  return (
    <div className="w-full bg-white text-black p-6 rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4">{question.text}</h3>
      
      <div className="space-y-3">
        {question.answers.map((answer) => (
          <div key={answer.id} className="flex items-center">
            <input
              type="radio"
              id={`answer-${answer.id}`}
              name={`question-${question.id}`}
              value={answer.id}
              checked={selectedAnswerId === answer.id}
              onChange={() => onAnswerSelect(answer.id)}
              className="mr-3 h-4 w-4"
            />
            <label 
              htmlFor={`answer-${answer.id}`}
              className="flex-1 cursor-pointer"
            >
              {answer.text}
            </label>
          </div>
        ))}
      </div>
    </div>
  );
}
