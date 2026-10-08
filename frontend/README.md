# Frontend

Next.js (App Router) + TypeScript (strict) + Tailwind CSS v4. Design: [docs/UI_DESIGN_SPEC.md](../docs/UI_DESIGN_SPEC.md),
decision record: [docs/adr/001-use-nextjs.md](../docs/adr/001-use-nextjs.md).

```
app/                 routes: / → /meetings, /meetings/[id], /settings (placeholders until Phases 7–9)
  globals.css        design tokens (CSS variables → Tailwind colours)
lib/
  config.ts          NEXT_PUBLIC_API_URL
  api.ts             typed fetch wrapper → ApiError from the backend error envelope
  *.test.ts          Vitest unit tests (pure logic)
tests/e2e/           Playwright critical-workflow tests
```
`components/` and `hooks/` are added with the features that need them (Phase 7+).

## Run locally
```bash
npm install
cp .env.example .env.local
npm run dev                      # http://localhost:3000
```

## Checks
```bash
npm run lint && npm run format:check && npm run typecheck
npm test                         # Vitest unit tests
npm run build
npx playwright install chromium  # once
npm run test:e2e                 # builds must exist: runs `next start`
```
