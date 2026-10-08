// Public runtime configuration. NEXT_PUBLIC_* values are inlined at build time.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);
