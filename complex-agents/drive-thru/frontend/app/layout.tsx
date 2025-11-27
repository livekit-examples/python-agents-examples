import { Public_Sans } from 'next/font/google';
import { headers } from 'next/headers';
import { ApplyThemeScript } from '@/components/theme-toggle';
import { getAppConfig, getOrigin } from '@/lib/utils';
import './globals.css';

const publicSans = Public_Sans({
  variable: '--font-public-sans',
  subsets: ['latin'],
});

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  const hdrs = await headers();
  const origin = getOrigin(hdrs);
  const { accent, accentDark, pageTitle, pageDescription } = await getAppConfig(origin);

  const styles = [
    accent ? `:root { --primary: ${accent}; }` : '',
    accentDark ? `.dark { --primary: ${accentDark}; }` : '',
  ]
    .filter(Boolean)
    .join('\n');

  return (
    <html lang="en" suppressHydrationWarning className="scroll-smooth">
      <head>
        {styles && <style>{styles}</style>}
        <title>{pageTitle}</title>
        <meta name="description" content={pageDescription + '\n\nBuilt with LiveKit Agents.'} />
        <ApplyThemeScript />
      </head>
      <body
        className={`${publicSans.variable} bg-background text-foreground overflow-x-hidden antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
