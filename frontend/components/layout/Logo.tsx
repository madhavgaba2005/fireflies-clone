import Link from "next/link";

/** Original wordmark — the product is a Fireflies-style workspace, not a copy of its brand. */
export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link
      href="/meetings"
      className="flex items-center gap-2 font-semibold tracking-tight"
      aria-label="Lumen home"
    >
      <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden>
        <defs>
          <linearGradient id="lumen-logo" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#6d28d9" />
          </linearGradient>
        </defs>
        <rect width="28" height="28" rx="8" fill="url(#lumen-logo)" />
        <path d="M14 6l2.2 5.8L22 14l-5.8 2.2L14 22l-2.2-5.8L6 14l5.8-2.2z" fill="white" />
      </svg>
      {!compact && <span className="text-[17px]">Lumen</span>}
    </Link>
  );
}
