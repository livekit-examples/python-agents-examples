import { Public_Sans } from 'next/font/google';
import localFont from 'next/font/local';
import { headers } from 'next/headers';
import { ThemeProvider } from '@/components/app/theme-provider';
import { cn } from '@/lib/shadcn/utils';
import { getAppConfig, getStyles } from '@/lib/utils';
import '@/styles/globals.css';

const publicSans = Public_Sans({
  variable: '--font-public-sans',
  subsets: ['latin'],
});

const commitMono = localFont({
  display: 'swap',
  variable: '--font-commit-mono',
  src: [
    {
      path: '../fonts/CommitMono-400-Regular.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-700-Regular.otf',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-400-Italic.otf',
      weight: '400',
      style: 'italic',
    },
    {
      path: '../fonts/CommitMono-700-Italic.otf',
      weight: '700',
      style: 'italic',
    },
  ],
});

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);
  const styles = getStyles(appConfig);
  const { pageTitle, pageDescription, logo, logoDark } = appConfig;

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        publicSans.variable,
        commitMono.variable,
        'scroll-smooth font-sans antialiased'
      )}
    >
      <head>
        {styles && <style>{styles}</style>}
        <title>{pageTitle}</title>
        <meta name="description" content={pageDescription} />
      </head>
      <body className="overflow-x-hidden">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          forcedTheme="dark"
          disableTransitionOnChange
        >
          <header className="fixed top-0 left-0 z-50 hidden w-full p-6 md:flex">
            <div className="flex items-center gap-3 rounded-full border border-white/10 bg-black/50 px-4 py-2 backdrop-blur-md">
              <a
                target="_blank"
                rel="noopener noreferrer"
                href="https://livekit.io"
                aria-label="LiveKit"
                className="scale-100 transition-transform duration-300 hover:scale-110"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={logo} alt="LiveKit logo" className="block size-6 dark:hidden" />
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={logoDark ?? logo}
                  alt="LiveKit logo"
                  className="hidden size-6 dark:block"
                />
              </a>
              <span className="h-5 w-px bg-white/15" aria-hidden="true" />
              <span
                aria-label="Keyframe Labs"
                className="text-foreground font-sans text-lg font-medium tracking-[-0.035em]"
              >
                Keyframe Labs
              </span>
            </div>
          </header>

          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
