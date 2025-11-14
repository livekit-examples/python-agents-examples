import type { AppConfig } from './lib/types';

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Dungeons & Agents',
  pageTitle: 'Dungeons & Agents - AI Tabletop RPG',
  pageDescription: 'An AI-powered tabletop RPG adventure with Inworld voices',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#002cf2',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#1fd5f9',
  startButtonText: 'Begin Your Adventure',
};
