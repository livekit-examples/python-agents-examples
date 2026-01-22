export type BossType = 'easy' | 'medium' | 'hard';

export interface BossPersonality {
  id: BossType;
  name: string;
  difficulty: string;
  description: string;
  imageUrl: string;
  color: string;
  borderColor: string;
  bgColor: string;
  textColor: string;
}

export const BOSS_PERSONALITIES: Record<BossType, BossPersonality> = {
  easy: {
    id: 'easy',
    name: 'The Encourager',
    difficulty: 'Easy',
    description: 'Supportive and open to discussion. Good for building confidence.',
    imageUrl: '/img/boss_1.png',
    color: 'green',
    borderColor: 'border-green-500',
    bgColor: 'bg-green-500/10',
    textColor: 'text-green-500',
  },
  medium: {
    id: 'medium',
    name: 'The Skeptic',
    difficulty: 'Medium',
    description: 'Questions everything and pushes back on numbers. Prepares you for tough conversations.',
    imageUrl: '/img/boss_2.png',
    color: 'yellow',
    borderColor: 'border-yellow-500',
    bgColor: 'bg-yellow-500/10',
    textColor: 'text-yellow-500',
  },
  hard: {
    id: 'hard',
    name: 'The Busy Executive',
    difficulty: 'Hard',
    description: 'Impatient and time-constrained. Practice your elevator pitch.',
    imageUrl: '/img/boss_3.png',
    color: 'red',
    borderColor: 'border-red-500',
    bgColor: 'bg-red-500/10',
    textColor: 'text-red-500',
  },
};

export const MODE_COLORS = {
  roleplay: {
    borderColor: 'border-blue-500',
    bgColor: 'bg-blue-500/10',
    textColor: 'text-blue-500',
    label: 'Role-play mode',
  },
  coaching: {
    borderColor: 'border-green-500',
    bgColor: 'bg-green-500/10',
    textColor: 'text-green-500',
    label: 'Coaching mode',
  },
};
