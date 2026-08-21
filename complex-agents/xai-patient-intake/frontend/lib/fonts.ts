import { Public_Sans, Space_Grotesk } from 'next/font/google';
import localFont from 'next/font/local';

/**
 * Public Sans
 *
 * @see {@link https://fonts.google.com/specimen/Public+Sans | Public Sans website}
 */
export const sansFont = Public_Sans({
  variable: '--font-lk-sans',
  subsets: ['latin'],
  preload: true,
});

/**
 * Commit Mono
 *
 * @see {@link https://commitmono.com/ | Commit Mono website}
 */
export const monoFont = localFont({
  src: '../fonts/commit-mono-variable-font.woff2',
  variable: '--font-lk-mono',
  preload: true,
});

/**
 * Space Grotesk
 *
 * A grotesque display face for headings, in place of the commercially licensed one the
 * LiveKit brand uses — this repo is public, so every font here has to be redistributable.
 * The variable axis covers 300-700, the weights `font-display` headings ask for. There is
 * no italic; nothing in this app sets one on a heading, so the browser would synthesize it.
 *
 * @see {@link https://fonts.google.com/specimen/Space+Grotesk | Space Grotesk website}
 */
export const displayFont = Space_Grotesk({
  variable: '--font-lk-display',
  subsets: ['latin'],
  preload: false,
});
