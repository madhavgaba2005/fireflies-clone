"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { Toaster } from "sonner";

import { ApiError } from "@/lib/api";
import { useTheme } from "@/hooks/useTheme";

function shouldRetry(failureCount: number, error: unknown): boolean {
  // Retrying a 4xx can't help (e.g. "meeting not found"); network blips get one retry.
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false;
  return failureCount < 1;
}

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: shouldRetry, refetchOnWindowFocus: false, staleTime: 5_000 },
        },
      }),
  );
  const theme = useTheme();
  return (
    <QueryClientProvider client={client}>
      {children}
      <Toaster theme={theme} position="bottom-right" richColors closeButton duration={3500} />
    </QueryClientProvider>
  );
}
