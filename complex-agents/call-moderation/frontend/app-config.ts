export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  // for LiveKit Cloud Sandbox
  sandboxId?: string;
  agentName?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Hail Ride',
  pageTitle: 'Hail Ride Dispatch',
  pageDescription: 'Coordinate riders and drivers in real-time with LiveKit.',

  supportsChatInput: false,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: false,

  logo: '/hail-ride-logo.svg',
  accent: '#23d3f6',
  logoDark: '/hail-ride-logo-dark.svg',
  accentDark: '#1fd5f9',
  startButtonText: 'Contact Driver',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: "devday-driver-agent",
};
