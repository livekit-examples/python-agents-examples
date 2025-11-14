import { Button } from '@/components/ui/button';

interface WelcomeProps {
  disabled: boolean;
  startButtonText: string;
  onStartCall: () => void;
}

export const Welcome = ({
  disabled,
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeProps) => {
  return (
    <div
      ref={ref}
      inert={disabled}
      className="fixed inset-0 z-10 flex min-h-svh flex-col justify-between px-4 py-8 text-left sm:px-8 lg:px-12"
    >
      <header className="mx-auto w-full max-w-5xl">
        <div className="flex items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="flex size-14 items-center justify-center rounded-3xl bg-white/80 shadow-xl ring-1 ring-black/5 backdrop-blur dark:bg-slate-900/70 dark:ring-white/10">
              <svg
                viewBox="0 0 64 64"
                aria-hidden="true"
                className="size-10 text-sky-600 dark:text-sky-300"
              >
                <path
                  d="M15 24V40C15 40.7957 14.6839 41.5587 14.1213 42.1213C13.5587 42.6839 12.7956 43 12 43C11.2044 43 10.4413 42.6839 9.87868 42.1213C9.31607 41.5587 9 40.7957 9 40V24C9 23.2044 9.31607 22.4413 9.87868 21.8787C10.4413 21.3161 11.2044 21 12 21C12.7956 21 13.5587 21.3161 14.1213 21.8787C14.6839 22.4413 15 23.2044 15 24ZM22 5C21.2044 5 20.4413 5.31607 19.8787 5.87868C19.3161 6.44129 19 7.20435 19 8V56C19 56.7957 19.3161 57.5587 19.8787 58.1213C20.4413 58.6839 21.2044 59 22 59C22.7956 59 23.5587 58.6839 24.1213 58.1213C24.6839 57.5587 25 56.7957 25 56V8C25 7.20435 24.6839 6.44129 24.1213 5.87868C23.5587 5.31607 22.7956 5 22 5ZM32 13C31.2044 13 30.4413 13.3161 29.8787 13.8787C29.3161 14.4413 29 15.2044 29 16V48C29 48.7957 29.3161 49.5587 29.8787 50.1213C30.4413 50.6839 31.2044 51 32 51C32.7956 51 33.5587 50.6839 34.1213 50.1213C34.6839 49.5587 35 48.7957 35 48V16C35 15.2044 34.6839 14.4413 34.1213 13.8787C33.5587 13.3161 32.7956 13 32 13ZM42 21C41.2043 21 40.4413 21.3161 39.8787 21.8787C39.3161 22.4413 39 23.2044 39 24V40C39 40.7957 39.3161 41.5587 39.8787 42.1213C40.4413 42.6839 41.2043 43 42 43C42.7957 43 43.5587 42.6839 44.1213 42.1213C44.6839 41.5587 45 40.7957 45 40V24C45 23.2044 44.6839 22.4413 44.1213 21.8787C43.5587 21.3161 42.7957 21 42 21ZM52 17C51.2043 17 50.4413 17.3161 49.8787 17.8787C49.3161 18.4413 49 19.2044 49 20V44C49 44.7957 49.3161 45.5587 49.8787 46.1213C50.4413 46.6839 51.2043 47 52 47C52.7957 47 53.5587 46.6839 54.1213 46.1213C54.6839 45.5587 55 44.7957 55 44V20C55 19.2044 54.6839 18.4413 54.1213 17.8787C53.5587 17.3161 52.7957 17 52 17Z"
                  fill="currentColor"
                />
              </svg>
            </div>

            <div>
              <p className="text-sm font-semibold tracking-[0.24em] text-sky-600 uppercase dark:text-sky-200">
                PulseNote AI
              </p>
              <p className="mt-1 text-lg font-semibold text-slate-800 dark:text-white">
                Clinical documentation without the busywork
              </p>
            </div>
          </div>

          <div className="hidden shrink-0 items-center gap-2 rounded-full border border-white/80 bg-white/70 px-4 py-2 text-sm font-medium text-slate-600 shadow-lg backdrop-blur md:flex dark:border-slate-700/60 dark:bg-slate-900/60 dark:text-slate-200">
            <span className="inline-flex size-2 rounded-full bg-emerald-400" aria-hidden="true" />
            HIPAA-ready infrastructure
          </div>
        </div>
      </header>

      <main className="mx-auto mt-12 w-full max-w-5xl flex-1">
        <div className="grid gap-10 overflow-hidden rounded-[2.75rem] border border-white/70 bg-white/80 p-8 shadow-[0_40px_120px_-60px_rgba(15,23,42,0.75)] ring-1 ring-black/5 backdrop-blur-xl md:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)] md:p-12 dark:border-slate-700/60 dark:bg-slate-900/75 dark:ring-white/10">
          <div className="flex flex-col justify-center gap-6">
            <span className="inline-flex items-center gap-2 self-start rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold tracking-widest text-sky-700 uppercase ring-1 ring-sky-100 dark:bg-sky-500/10 dark:text-sky-200 dark:ring-sky-500/30">
              Live consultation workspace
            </span>
            <h1 className="text-3xl leading-tight font-semibold text-slate-900 sm:text-4xl dark:text-white">
              Medical Note Taking Assistant
            </h1>
            <p className="max-w-xl text-base leading-relaxed text-slate-600 dark:text-slate-300">
              Seamlessly capture conversations, generate structured notes, and hand off detailed
              summaries before the patient leaves the room.
            </p>

            <ul className="grid gap-4 text-base text-slate-700 dark:text-slate-200">
              <li className="flex items-start gap-3">
                <span className="mt-1 flex size-7 items-center justify-center rounded-full bg-sky-100 text-sky-600 shadow-sm dark:bg-sky-500/20 dark:text-sky-200">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="size-4"
                  >
                    <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <span>Real-time transcription with speaker-aware context.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="mt-1 flex size-7 items-center justify-center rounded-full bg-sky-100 text-sky-600 shadow-sm dark:bg-sky-500/20 dark:text-sky-200">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="size-4"
                  >
                    <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <span>AI-curated SOAP notes aligned with clinical best practices.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="mt-1 flex size-7 items-center justify-center rounded-full bg-sky-100 text-sky-600 shadow-sm dark:bg-sky-500/20 dark:text-sky-200">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="size-4"
                  >
                    <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <span>One-click diagnosis request powered by LiveKit voice agents.</span>
              </li>
            </ul>

            <Button
              size="lg"
              onClick={onStartCall}
              disabled={disabled}
              className="group mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-sky-500/30 transition-all hover:translate-y-px hover:from-sky-500 hover:via-blue-500 hover:to-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500 sm:w-auto"
            >
              {startButtonText}
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className="size-5 transition-transform group-hover:translate-x-1"
              >
                <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Button>
          </div>

          <aside className="relative overflow-hidden rounded-3xl border border-white/60 bg-gradient-to-br from-slate-900 via-slate-900/95 to-slate-900/70 p-8 text-slate-100 shadow-2xl ring-1 ring-white/10 dark:border-slate-700/70 dark:from-slate-900 dark:via-slate-900/90 dark:to-slate-900/60">
            <div
              className="absolute -top-24 right-0 size-56 rounded-full bg-sky-500/20 blur-3xl"
              aria-hidden="true"
            />
            <div
              className="absolute bottom-0 left-0 size-48 rounded-full bg-indigo-500/10 blur-3xl"
              aria-hidden="true"
            />
            <div className="relative flex flex-col gap-6">
              <div>
                <p className="text-xs font-semibold tracking-[0.3em] text-sky-300/80 uppercase">
                  Session snapshot
                </p>
                <h2 className="mt-2 text-2xl font-semibold">Agent environment</h2>
                <p className="mt-2 text-sm text-slate-300">
                  Your LiveKit workspace is ready. Launch the consultation to begin streaming audio
                  and collecting structured notes instantly.
                </p>
              </div>

              <dl className="grid gap-4 text-sm text-slate-200">
                <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <dt className="flex items-center gap-2 font-medium text-slate-200">
                    <span className="relative flex size-2 items-center justify-center">
                      <span className="absolute inline-flex size-2 animate-ping rounded-full bg-emerald-300/70" />
                      <span className="inline-flex size-2 rounded-full bg-emerald-300" />
                    </span>
                    Agent link
                  </dt>
                  <dd className="text-xs tracking-[0.2em] text-emerald-200 uppercase">Connected</dd>
                </div>
                <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <dt className="font-medium text-slate-200">STT model</dt>
                  <dd className="flex items-center gap-2 text-xs tracking-[0.2em] text-sky-200 uppercase">
                    <span className="size-2 rounded-full bg-sky-300" aria-hidden="true" />
                    Deepgram Flux
                  </dd>
                </div>
                <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <dt className="font-medium text-slate-200">LLM model</dt>
                  <dd className="flex items-center gap-2 text-xs tracking-[0.2em] text-indigo-200 uppercase">
                    <span className="size-2 rounded-full bg-indigo-300" aria-hidden="true" />
                    GPT-OSS-120B
                  </dd>
                </div>
              </dl>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-xs text-slate-300">
                <p className="font-semibold tracking-[0.3em] text-slate-200/80 uppercase">
                  Preview
                </p>
                <p className="mt-2 leading-relaxed text-slate-300">
                  “Patient reports intermittent chest tightness when climbing stairs. Recommending a
                  stress test and follow-up in two weeks. Note flagged for cardiology review.”
                </p>
              </div>
            </div>
          </aside>
        </div>
      </main>

      <footer className="mx-auto mt-10 w-full max-w-5xl text-sm text-slate-500 select-none dark:text-slate-300">
        <p className="leading-relaxed">
          This assistant transcribes each consultation, drafts SOAP-style medical notes, and keeps a
          secure audit trail for downstream EHR workflows.
        </p>
      </footer>
    </div>
  );
};
