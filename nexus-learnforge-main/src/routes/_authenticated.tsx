import { createFileRoute, Outlet, useNavigate, Link, useLocation } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LayoutDashboard, MessageSquare, FileText, Sparkles, LogOut, BookOpen, Plus, LifeBuoy, Archive } from "lucide-react";

import { AnimatedBackground } from "@/components/AnimatedBackground";
import { useAuth } from "@/lib/auth-context";
import { getToken } from "@/api";

export const Route = createFileRoute("/_authenticated")({
  component: AuthGate,
});

function AuthGate() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => setHydrated(true), []);

  useEffect(() => {
    if (!hydrated) return;
    if (!loading && !user && !getToken()) {
      navigate({ to: "/login" });
    }
  }, [hydrated, loading, user, navigate]);

  if (!hydrated || loading) {
    return (
      <div className="grid min-h-screen place-items-center">
        <AnimatedBackground />
        <div className="glass rounded-2xl px-6 py-4 text-sm text-muted-foreground">
          Establishing secure link…
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="grid min-h-screen place-items-center">
        <AnimatedBackground />
        <div className="glass rounded-2xl px-6 py-4 text-sm text-muted-foreground">Redirecting…</div>
      </div>
    );
  }

  return <Shell />;
}

function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const nav = [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/chat", label: "AI Workspace", icon: MessageSquare },
    { to: "/generate", label: "Gen Studio", icon: Sparkles },
    { to: "/documents", label: "Library", icon: FileText },
  ] as const;

  return (
    <div className="relative min-h-screen">
      <AnimatedBackground />
      <div className="mx-auto grid min-h-screen max-w-[1500px] grid-cols-1 gap-6 p-4 md:grid-cols-[260px_1fr] md:p-6">
        {/* Sidebar */}
        <aside className="glass-strong sticky top-6 flex h-[calc(100vh-3rem)] flex-col p-5">
          <div className="mb-6 flex items-center gap-3 px-1">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-primary/70 to-secondary/70">
              <BookOpen className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <div className="font-display text-lg font-semibold leading-tight text-gradient">NEXUS EDU</div>
              <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
                Academic Intelligence
              </div>
            </div>
          </div>

          <Link
            to="/dashboard"
            className="mb-6 inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-primary/80 to-secondary/80 px-4 py-3 text-sm font-semibold text-primary-foreground shadow-[0_8px_24px_-12px_oklch(0.72_0.11_295/0.6)] transition hover:brightness-110"
          >
            <Plus className="h-4 w-4" /> New Research
          </Link>

          <nav className="space-y-1">
            {nav.map((n) => {
              const active = location.pathname === n.to;
              return (
                <Link
                  key={n.to}
                  to={n.to}
                  className={`group flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm transition ${
                    active
                      ? "bg-white/5 text-foreground ring-1 ring-white/10"
                      : "text-muted-foreground hover:bg-white/[0.04] hover:text-foreground"
                  }`}
                >
                  <n.icon className="h-4 w-4" />
                  {n.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto space-y-1 border-t border-border/40 pt-4">
            <button className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm text-muted-foreground hover:bg-white/[0.04] hover:text-foreground">
              <LifeBuoy className="h-4 w-4" /> Support
            </button>
            <button className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm text-muted-foreground hover:bg-white/[0.04] hover:text-foreground">
              <Archive className="h-4 w-4" /> Archive
            </button>
            <button
              onClick={() => {
                logout();
                navigate({ to: "/" });
              }}
              className="mt-2 flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm text-muted-foreground hover:bg-white/[0.04] hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              <span className="truncate">Sign out · {user?.full_name?.split(" ")[0] ?? user?.email}</span>
            </button>
          </div>
        </aside>

        {/* Content */}
        <AnimatePresence mode="wait">
          <motion.main
            key={location.pathname}
            initial={{ opacity: 0, y: 12, filter: "blur(6px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -8, filter: "blur(4px)" }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="min-w-0"
          >
            <Outlet />
          </motion.main>
        </AnimatePresence>
      </div>
    </div>
  );
}
