"use client";

import {
  BarChart3,
  type LucideIcon,
  Plug,
  Settings,
  Upload,
  Users,
  Video,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useComingSoon } from "@/components/ui/ComingSoon";
import { cn } from "@/lib/colors";

import { useOpenCreateMeeting } from "./CreateMeetingContext";
import { Logo } from "./Logo";

interface NavLinkProps {
  icon: LucideIcon;
  label: string;
  href?: string;
  onClick?: () => void;
  active?: boolean;
  badge?: string;
}

function NavItem({ icon: Icon, label, href, onClick, active, badge }: NavLinkProps) {
  const className = cn(
    "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[13.5px] font-medium transition-colors",
    active ? "bg-primary-soft text-primary" : "text-muted hover:bg-surface-muted hover:text-text",
  );
  const content = (
    <>
      <Icon size={18} strokeWidth={active ? 2.2 : 1.8} />
      <span className="flex-1 text-left">{label}</span>
      {badge && (
        <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] text-subtle">
          {badge}
        </span>
      )}
    </>
  );
  return href ? (
    <Link href={href} className={className} aria-current={active ? "page" : undefined}>
      {content}
    </Link>
  ) : (
    <button type="button" onClick={onClick} className={className}>
      {content}
    </button>
  );
}

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const comingSoon = useComingSoon();
  const openCreate = useOpenCreateMeeting();

  const soon = (name: string, description: string) => () => {
    onNavigate?.();
    comingSoon({ name, description });
  };

  return (
    <nav
      aria-label="Main"
      className="flex h-full w-60 flex-col border-r border-border bg-surface px-3 py-4"
    >
      <div className="px-2 pb-5">
        <Logo />
      </div>
      <div className="flex flex-col gap-0.5" onClick={onNavigate}>
        <NavItem
          icon={Video}
          label="Meetings"
          href="/meetings"
          active={pathname.startsWith("/meetings")}
        />
        <NavItem icon={Upload} label="Uploads" onClick={() => openCreate("upload")} />
      </div>
      <p className="mt-6 px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-subtle">
        Workspace
      </p>
      <div className="flex flex-col gap-0.5">
        <NavItem
          icon={Plug}
          label="Integrations"
          badge="Soon"
          onClick={soon(
            "Integrations",
            "Connect Zoom, Google Meet, your calendar and CRM to capture meetings automatically.",
          )}
        />
        <NavItem
          icon={BarChart3}
          label="Analytics"
          badge="Soon"
          onClick={soon(
            "Analytics",
            "Talk-time trends, topic trackers and meeting insights across your team.",
          )}
        />
        <NavItem
          icon={Users}
          label="Team"
          badge="Soon"
          onClick={soon(
            "Team & sharing",
            "Invite teammates and share meeting notes and soundbites.",
          )}
        />
        <div onClick={onNavigate}>
          <NavItem
            icon={Settings}
            label="Settings"
            href="/settings"
            active={pathname.startsWith("/settings")}
          />
        </div>
      </div>
      <div className="mt-auto rounded-xl border border-border bg-gradient-to-br from-primary-soft to-surface p-3">
        <div className="flex items-center gap-2 text-[13px] font-semibold">
          <Zap size={15} className="text-primary" /> Live meeting assistant
        </div>
        <p className="mt-1 text-[12px] text-muted">
          Let Lumen join your calls and take notes automatically.
        </p>
        <button
          type="button"
          onClick={soon(
            "Live meeting bot",
            "A notetaker that joins Zoom, Meet and Teams calls in real time.",
          )}
          className="mt-2 text-[12px] font-semibold text-primary hover:underline"
        >
          Learn more
        </button>
      </div>
    </nav>
  );
}
