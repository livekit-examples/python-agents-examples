import type { AppConfig } from './lib/types';

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'LiveKit',
  pageTitle: 'Roman Empire Study Partner',
  pageDescription: 'An interactive AI tutor specializing in the Fall of the Roman Empire',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: false,

  logo: '/lk-logo.svg',
  accent: '#002cf2',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#1fd5f9',
  startButtonText: 'Start learning session',
};
