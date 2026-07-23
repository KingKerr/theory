import type { ReactNode } from "react";
import Link from "next/link";

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <div className="grid min-h-screen grid-cols-[260px_1fr]">
        <aside className="border-r border-neutral-800 p-4">
          <div className="mb-6 text-sm uppercase tracking-[0.2em] text-neutral-500">
            Market World Model
          </div>

          <nav className="space-y-2 text-sm">
            <Link href="/" className="block rounded px-3 py-2 hover:bg-neutral-900">
              Workspace
            </Link>
            <Link href="/evaluations" className="block rounded px-3 py-2 hover:bg-neutral-900">
              Evaluations
            </Link>
          </nav>
        </aside>

        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}