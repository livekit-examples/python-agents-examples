# Fonts

Everything in this directory has to be redistributable, because this repo is public.

| File | Family | License |
| --- | --- | --- |
| `commit-mono-variable-font.woff2` | [Commit Mono](https://commitmono.com/) by Eiríkr Ásheim | SIL Open Font License 1.1 |

The sans (Public Sans) and display (Space Grotesk) faces are fetched at build time by
`next/font/google` — see `lib/fonts.ts` — so no binary for them lives here.

Do not add a commercially licensed face. The LiveKit brand display font, TWK Everett, is
licensed per-seat from [weltkern](https://weltkern.com/typefaces/everett) and shipping the
binary here would redistribute it to everyone who clones the repo.
