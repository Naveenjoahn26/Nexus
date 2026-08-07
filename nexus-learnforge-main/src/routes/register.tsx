import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { AnimatedBackground } from "@/components/AnimatedBackground";
import { useAuth } from "@/lib/auth-context";

export const Route = createFileRoute("/register")({
  component: RegisterPage,
  head: () => ({
    meta: [
      { title: "Create account · NEXUS EDU" },
      { name: "description", content: "Create your NEXUS EDU workspace and start learning smarter." },
      { property: "og:title", content: "Create account · NEXUS EDU" },
      { property: "og:description", content: "Create your NEXUS EDU workspace." },
    ],
  }),
});

function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // #region agent log
    fetch("http://127.0.0.1:7777/ingest/e89b92b7-5bea-457e-bc00-e666afa6c6eb", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "74d681" },
      body: JSON.stringify({
        sessionId: "74d681",
        hypothesisId: "D",
        location: "register.tsx:onSubmit:entry",
        message: "frontend register submit",
        data: { email, passwordLen: password.length, apiBase: typeof window !== "undefined" ? window.localStorage.getItem("nexus_api_base") : null },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    try {
      await register({ email, full_name: fullName, password });
      // #region agent log
      fetch("http://127.0.0.1:7777/ingest/e89b92b7-5bea-457e-bc00-e666afa6c6eb", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "74d681" },
        body: JSON.stringify({
          sessionId: "74d681",
          hypothesisId: "E",
          location: "register.tsx:onSubmit:success",
          message: "register and auto-login succeeded",
          data: { email },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      toast.success("Account created — welcome.");
      navigate({ to: "/dashboard" });
    } catch (err) {
      // #region agent log
      fetch("http://127.0.0.1:7777/ingest/e89b92b7-5bea-457e-bc00-e666afa6c6eb", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "74d681" },
        body: JSON.stringify({
          sessionId: "74d681",
          hypothesisId: "D",
          location: "register.tsx:onSubmit:error",
          message: "register failed on frontend",
          data: { email, passwordLen: password.length, error: (err as Error).message },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4">
      <AnimatedBackground />
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.97, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
        transition={{ duration: 0.7, ease: "easeOut" }}
        className="glass-strong relative w-full max-w-md rounded-3xl p-8 shadow-2xl"
      >
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-primary to-secondary glow-cyan">
            <Sparkles className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Create your account</h1>
            <p className="text-xs text-muted-foreground">Boot up a new NEXUS workspace</p>
          </div>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Full name">
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input"
              placeholder="Ada Lovelace"
            />
          </Field>
          <Field label="Email">
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="you@university.edu"
            />
          </Field>
          <Field label="Password">
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="At least 8 characters"
            />
          </Field>

          <button
            type="submit"
            disabled={loading}
            className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary py-3 text-sm font-semibold text-primary-foreground glow-cyan transition disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
            {loading ? "Creating…" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </motion.div>

      <style>{`
        .input {
          width: 100%;
          border-radius: 0.75rem;
          border: 1px solid oklch(1 0 0 / 0.1);
          background: oklch(1 0 0 / 0.04);
          padding: 0.7rem 0.9rem;
          font-size: 0.875rem;
          color: var(--color-foreground);
          outline: none;
          transition: border-color .2s, box-shadow .2s;
        }
        .input:focus {
          border-color: var(--color-primary);
          box-shadow: 0 0 0 3px oklch(0.78 0.18 210 / 0.25);
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}
