import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  BookOpen,
  Loader2,
  Filter,
  FileText,
  Send,
  Paperclip,
  History,
  MoreVertical,
  Sparkles,
  Zap,
} from "lucide-react";
import { toast } from "sonner";

import { dashboard as dashboardApi } from "@/api";
import { useAuth } from "@/lib/auth-context";

export const Route = createFileRoute("/_authenticated/dashboard")({
  component: Dashboard,
  head: () => ({
    meta: [
      { title: "Dashboard · NEXUS EDU" },
      { name: "description", content: "Course context, sources, and your NEXUS Assistant in one calm workspace." },
      { property: "og:title", content: "Dashboard · NEXUS EDU" },
      { property: "og:description", content: "Course context, sources, and your NEXUS Assistant in one calm workspace." },
    ],
  }),
});

function Dashboard() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const q = useQuery({ queryKey: ["courses"], queryFn: () => dashboardApi.listCourses() });

  const activeCourse = q.data?.[0];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Welcome back,</p>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {user?.full_name?.split(" ")[0] ?? "learner"}
            <span className="text-gradient">.</span>
          </h1>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-primary/80 to-secondary/80 px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-[0_8px_24px_-12px_oklch(0.72_0.11_295/0.5)] transition hover:brightness-110"
        >
          <Plus className="h-4 w-4" /> New workspace
        </button>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(320px,380px)_1fr]">
        <CourseContextPanel
          loading={q.isLoading}
          error={q.error as Error | null}
          courses={q.data ?? []}
        />
        <AssistantPreview courseName={activeCourse?.name} />
      </div>

      {open && (
        <CreateCourseModal
          onClose={() => setOpen(false)}
          onCreated={() => {
            qc.invalidateQueries({ queryKey: ["courses"] });
            setOpen(false);
          }}
        />
      )}
    </div>
  );
}

/* ---------------- Course Context ---------------- */

type CourseLike = {
  id: string | number;
  name: string;
  code?: string | null;
  subject_area?: string | null;
  academic_level?: string | null;
  description?: string | null;
};

function CourseContextPanel({
  loading,
  error,
  courses: list,
}: {
  loading: boolean;
  error: Error | null;
  courses: CourseLike[];
}) {
  const items = useMemo(() => list.slice(0, 6), [list]);

  return (
    <section className="glass-strong flex flex-col overflow-hidden p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Course</h2>
          <h2 className="text-xl font-semibold tracking-tight">Context</h2>
        </div>
        <button className="grid h-9 w-9 place-items-center rounded-full border border-white/10 text-muted-foreground transition hover:border-white/20 hover:text-foreground">
          <Filter className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {loading ? (
          <div className="grid h-32 place-items-center rounded-2xl border border-white/5 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        ) : error ? (
          <ErrorCard message={error.message} />
        ) : items.length === 0 ? (
          <EmptyState />
        ) : (
          items.map((c, i) => <SourceCard key={c.id} course={c} index={i} />)
        )}
      </div>

      <Link
        to="/documents"
        className="mt-4 inline-flex items-center justify-center gap-2 rounded-2xl border border-dashed border-white/15 px-4 py-3 text-sm text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
      >
        <FileText className="h-4 w-4" /> Ingest New Source
      </Link>
    </section>
  );
}

function SourceCard({ course, index }: { course: CourseLike; index: number }) {
  const statuses = [
    { label: "Indexed & Ready", tone: "text-emerald-300/90", dot: "bg-emerald-400/80" },
    { label: "Ingesting Data…", tone: "text-primary", dot: "bg-primary animate-pulse" },
    { label: "Indexed & Ready", tone: "text-emerald-300/90", dot: "bg-emerald-400/80" },
  ];
  const status = statuses[index % statuses.length];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="group flex items-start gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-3 transition hover:border-white/10 hover:bg-white/[0.04]"
    >
      <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-primary/15 to-secondary/15 text-primary">
        <FileText className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{course.name}</div>
        <div className="mt-0.5 truncate text-[11px] text-muted-foreground">
          {course.code ?? course.subject_area ?? "Course context"} · {course.academic_level ?? "All levels"}
        </div>
        <div className={`mt-2 inline-flex items-center gap-1.5 text-[11px] ${status.tone}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
          {status.label}
        </div>
      </div>
    </motion.div>
  );
}

function EmptyState() {
  return (
    <div className="grid place-items-center rounded-2xl border border-white/5 p-10 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-primary/50 to-secondary/50">
        <BookOpen className="h-5 w-5 text-primary-foreground" />
      </div>
      <h3 className="mt-3 text-sm font-semibold">No workspaces yet</h3>
      <p className="mt-1 max-w-[220px] text-xs text-muted-foreground">
        Create a workspace to start ingesting sources into NEXUS.
      </p>
    </div>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm">
      <div className="font-medium text-destructive">Backend unavailable</div>
      <div className="mt-1 text-xs text-muted-foreground">{message}</div>
      <div className="mt-2 text-[11px] text-muted-foreground">
        Tip: use the ⚙ gear (bottom-right) to point NEXUS at your FastAPI server.
      </div>
    </div>
  );
}

/* ---------------- Assistant Preview ---------------- */

function AssistantPreview({ courseName }: { courseName?: string }) {
  return (
    <section className="glass-strong flex min-h-[560px] flex-col p-5">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="relative grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-primary/70 to-secondary/70 text-primary-foreground">
            <Sparkles className="h-5 w-5" />
            <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[oklch(0.19_0.025_275)] bg-emerald-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Nexus Assistant</h2>
            <div className="mt-0.5 inline-flex items-center gap-1.5 text-xs text-primary">
              <Zap className="h-3 w-3" /> Active in Context
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <button className="grid h-9 w-9 place-items-center rounded-full border border-white/10 transition hover:border-white/20 hover:text-foreground">
            <History className="h-4 w-4" />
          </button>
          <button className="grid h-9 w-9 place-items-center rounded-full border border-white/10 transition hover:border-white/20 hover:text-foreground">
            <MoreVertical className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="mt-6 flex-1 space-y-5 overflow-y-auto pr-1">
        <div className="ml-auto max-w-[80%] rounded-2xl rounded-tr-md border border-white/[0.06] bg-white/[0.04] p-4 text-sm">
          Analyze the '{courseName ?? "current workspace"}'. What are the core prerequisites mentioned for Week 3?
          <div className="mt-2 text-right text-[10px] text-muted-foreground">10:42 AM</div>
        </div>

        <div>
          <div className="mb-2 inline-flex items-center gap-1.5 text-xs text-primary">
            <Sparkles className="h-3 w-3" /> Nexus Analyzing Context…
          </div>
          <div className="max-w-[80%] rounded-2xl rounded-tl-md border border-white/[0.06] bg-white/[0.02] p-4">
            <div className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] text-primary">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Referencing 1 Source
            </div>
            <div className="space-y-2">
              <div className="h-2.5 w-[70%] rounded-full bg-white/[0.06]" />
              <div className="h-2.5 w-[85%] rounded-full bg-white/[0.06]" />
              <div className="h-2.5 w-[60%] rounded-full bg-white/[0.06]" />
              <div className="h-2.5 w-[30%] rounded-full bg-white/[0.06]" />
            </div>
          </div>
        </div>
      </div>

      <Link
        to="/chat"
        className="mt-5 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-2 pl-4 transition hover:border-primary/30"
      >
        <Paperclip className="h-4 w-4 text-muted-foreground" />
        <span className="flex-1 truncate text-sm text-muted-foreground">
          Ask Nexus about your academic documents…
        </span>
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-primary/80 to-secondary/80 text-primary-foreground">
          <Send className="h-4 w-4" />
        </span>
      </Link>
    </section>
  );
}

/* ---------------- Modal ---------------- */

function CreateCourseModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [description, setDescription] = useState("");
  const [subject, setSubject] = useState("");
  const [level, setLevel] = useState("undergraduate");

  const m = useMutation({
    mutationFn: () =>
      dashboardApi.createCourse({ name, code, description, subject_area: subject, academic_level: level }),
    onSuccess: () => {
      toast.success("Workspace created.");
      onCreated();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-background/70 p-4 backdrop-blur" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        onClick={(e) => e.stopPropagation()}
        className="glass-strong w-full max-w-lg p-6"
      >
        <h3 className="text-lg font-semibold">New workspace</h3>
        <p className="mt-1 text-sm text-muted-foreground">Every course gets its own RAG context.</p>

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Text label="Course name" value={name} onChange={setName} full />
          <Text label="Code" value={code} onChange={setCode} />
          <Text label="Subject area" value={subject} onChange={setSubject} />
          <label className="block sm:col-span-2">
            <Label>Academic level</Label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="high_school">High school</option>
              <option value="undergraduate">Undergraduate</option>
              <option value="graduate">Graduate</option>
              <option value="professional">Professional</option>
            </select>
          </label>
          <label className="block sm:col-span-2">
            <Label>Description</Label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </label>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-xl px-3 py-2 text-sm text-muted-foreground hover:text-foreground">
            Cancel
          </button>
          <button
            disabled={!name || m.isPending}
            onClick={() => m.mutate()}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary/80 to-secondary/80 px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
          >
            {m.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Create
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <span className="mb-1.5 block text-xs uppercase tracking-wide text-muted-foreground">{children}</span>;
}
function Text({
  label,
  value,
  onChange,
  full,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  full?: boolean;
}) {
  return (
    <label className={`block ${full ? "sm:col-span-2" : ""}`}>
      <Label>{label}</Label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary"
      />
    </label>
  );
}
