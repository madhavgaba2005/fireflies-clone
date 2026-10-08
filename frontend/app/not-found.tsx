import { FileQuestion } from "lucide-react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary-soft text-primary">
        <FileQuestion size={22} />
      </div>
      <h1 className="text-lg font-semibold">Page not found</h1>
      <p className="mt-1 text-[13px] text-muted">The page you’re looking for doesn’t exist.</p>
      <Link
        href="/meetings"
        className="mt-4 text-[13px] font-semibold text-primary hover:underline"
      >
        Back to meetings
      </Link>
    </div>
  );
}
