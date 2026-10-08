# ADR-001: Next.js (App Router) + TypeScript for the frontend

**Status:** Accepted (Phase 1)

## Context
The PDF mandates Next.js with TypeScript. Within that, we still choose a router, a styling approach, a data-fetching
strategy and how much state management to add. The UI is highly interactive (media player, synced transcript,
search highlighting, modals) and is graded on Fireflies similarity.

## Decision
- **App Router**, pages rendered as client components where interactivity is needed; a typed `lib/api.ts` client
  calls the Meeting Service directly (no Next.js API routes / BFF).
- **TypeScript `strict`**, with `lib/types.ts` mirroring the API's Pydantic response schemas.
- **Tailwind CSS** with CSS-variable design tokens (enables dark mode bonus with no rewrite).
- **Radix UI primitives** for accessible Dialog / DropdownMenu / Tabs (focus trap, Esc, ARIA) — styled by us.
- **TanStack Query** for server state (loading/error/caching/invalidation after mutations); plain React state for UI
  state. No Redux.
- **sonner** for toasts, **lucide-react** for icons.

## Alternatives
- **Pages Router:** still supported, but App Router is the current default and what reviewers expect.
- **Redux / Zustand:** global client state is tiny (player clock lives in one page); server state is better handled by a query cache.
- **Hand-written `useEffect` fetching:** fewer dependencies, but re-implements caching, refetch, and invalidation — more code to explain, more bugs.
- **Component library (MUI / Chakra):** fast, but its visual language fights the Fireflies look.
- **Server Components fetching from FastAPI:** good for SEO-heavy pages; here everything is behind a (mock) login and highly interactive, so the benefit is small and it complicates error/loading states.

## Trade-offs
+ Accessible primitives and a query cache let us spend time on Fireflies fidelity, not plumbing.
− Four small UI dependencies to justify; client-side fetching means a brief loading skeleton on first paint.

## Implementation notes (Phase 2)
- Scaffolded with `create-next-app` → **Next.js 16.4, React 19.3, Tailwind CSS v4** (CSS-first config; tokens in `app/globals.css`).
- Removed the generator's experimental `cacheComponents` / `partialPrefetching` flags: data is fetched client-side,
  so they add caching concepts with no benefit here.
- `@types/node` aligned to the Node 22 runtime (the generator pinned v20, which also conflicted with Vitest).
- **Vitest** added for unit tests of pure logic (`lib/`, later `hooks/`); Playwright stays for user workflows.
  Rejected: Jest (heavier TS/ESM setup), Node's built-in runner (TypeScript support still behind a flag on Node 22).
- Radix UI, TanStack Query, sonner and lucide-react are installed in Phase 7 with the first component that uses them,
  so no unused dependency is ever committed.

## Consequences
Complex logic (active-segment lookup, search splitting, transcript sync) lives in pure functions and hooks under
`lib/` and `hooks/`, so it is unit-testable and not buried in JSX.
