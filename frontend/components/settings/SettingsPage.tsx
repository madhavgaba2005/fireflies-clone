"use client";

import { Bell, Plug, User, Users } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Tabs } from "radix-ui";

import { DEFAULT_USER } from "@/components/layout/TopBar";
import { Avatar } from "@/components/ui/Avatar";

const TABS = [
  { id: "profile", label: "Profile", icon: User },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "integrations", label: "Integrations", icon: Plug },
  { id: "team", label: "Team", icon: Users },
] as const;

const INTEGRATIONS = [
  { name: "Zoom", description: "Record and transcribe Zoom meetings automatically." },
  { name: "Google Meet", description: "Join Meet calls from your calendar." },
  { name: "Microsoft Teams", description: "Capture Teams meetings and webinars." },
  { name: "Google Calendar", description: "Auto-join meetings on your calendar." },
  { name: "Salesforce", description: "Log notes and action items to CRM records." },
  { name: "Slack", description: "Share meeting recaps to channels." },
];

function Soon() {
  return (
    <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[11px] font-semibold text-primary">
      Coming soon
    </span>
  );
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="mb-1 text-[12px] font-medium text-muted">{label}</p>
      <p className="rounded-lg border border-border bg-surface-muted px-3 py-2 text-[13px]">
        {value}
      </p>
    </div>
  );
}

export function SettingsPage() {
  const router = useRouter();
  const params = useSearchParams();
  const requested = params.get("tab");
  const tab = TABS.some((t) => t.id === requested) ? requested! : "profile";

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-8">
      <h1 className="text-[22px] font-semibold tracking-tight">Settings</h1>
      <p className="mt-0.5 text-[13px] text-muted">
        Manage your profile and workspace preferences.
      </p>

      <Tabs.Root
        value={tab}
        onValueChange={(value) => router.replace(`/settings?tab=${value}`, { scroll: false })}
        className="mt-6 flex flex-col gap-6 md:flex-row"
      >
        <Tabs.List
          aria-label="Settings sections"
          className="flex shrink-0 gap-1 md:w-48 md:flex-col"
        >
          {TABS.map(({ id, label, icon: Icon }) => (
            <Tabs.Trigger
              key={id}
              value={id}
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] font-medium text-muted hover:bg-surface-muted data-[state=active]:bg-primary-soft data-[state=active]:text-primary"
            >
              <Icon size={15} /> {label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <div className="min-w-0 flex-1 rounded-2xl border border-border bg-surface p-6">
          <Tabs.Content value="profile" className="outline-none">
            <div className="flex items-center gap-4">
              <Avatar
                id={DEFAULT_USER.id}
                name={DEFAULT_USER.name}
                size="md"
                className="h-14 w-14 text-lg"
              />
              <div>
                <p className="text-[15px] font-semibold">{DEFAULT_USER.name}</p>
                <p className="text-[13px] text-muted">{DEFAULT_USER.email}</p>
              </div>
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <ReadOnlyField label="Full name" value={DEFAULT_USER.name} />
              <ReadOnlyField label="Email" value={DEFAULT_USER.email} />
              <ReadOnlyField label="Workspace" value="Northwind" />
              <ReadOnlyField label="Role" value="Admin" />
            </div>
            <p className="mt-6 rounded-lg bg-surface-muted px-3 py-2 text-[12.5px] text-muted">
              Authentication is out of scope for this demo — everyone uses this default account.
              Profile editing is coming soon.
            </p>
          </Tabs.Content>

          <Tabs.Content value="notifications" className="outline-none">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-[15px] font-semibold">Notifications</h2>
              <Soon />
            </div>
            {[
              "Email me when notes are ready",
              "Weekly digest of action items",
              "Mentions in comments",
            ].map((label) => (
              <label
                key={label}
                className="flex items-center justify-between border-b border-border py-3 text-[13px] last:border-b-0"
              >
                {label}
                <input type="checkbox" disabled className="h-4 w-4" aria-label={label} />
              </label>
            ))}
          </Tabs.Content>

          <Tabs.Content value="integrations" className="outline-none">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-[15px] font-semibold">Integrations</h2>
              <Soon />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {INTEGRATIONS.map((integration) => (
                <div key={integration.name} className="rounded-xl border border-border p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-[13.5px] font-semibold">{integration.name}</p>
                    <span className="text-[11px] text-subtle">Not connected</span>
                  </div>
                  <p className="mt-1 text-[12.5px] text-muted">{integration.description}</p>
                </div>
              ))}
            </div>
          </Tabs.Content>

          <Tabs.Content value="team" className="outline-none">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-[15px] font-semibold">Team & sharing</h2>
              <Soon />
            </div>
            <p className="text-[13px] text-muted">
              Invite teammates, share meetings and manage permissions. Until then, everything in
              this workspace is visible to the default user.
            </p>
          </Tabs.Content>
        </div>
      </Tabs.Root>
    </div>
  );
}
