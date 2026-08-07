import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen, FileText, Presentation, ClipboardList, Microscope, Loader2,
  Sparkles, Download, Search, AlertCircle, RefreshCw
} from "lucide-react";
import { toast } from "sonner";

import { notes as notesApi, quiz as quizApi, getApiBase } from "@/api";

// Renderers
import { ResultHeader } from "@/components/gen/ResultHeader";
import { SummaryRenderer, SummaryData } from "@/components/gen/SummaryRenderer";
import { LectureRenderer, LectureData } from "@/components/gen/LectureRenderer";
import { QuestionPaperRenderer, QuestionPaperData } from "@/components/gen/QuestionPaperRenderer";
import { PaperAnalysisRenderer, PaperAnalysisData } from "@/components/gen/PaperAnalysisRenderer";
import { PresentationRenderer, PresentationData } from "@/components/gen/PresentationRenderer";

export const Route = createFileRoute("/_authenticated/generate")({
  component: GeneratePage,
  head: () => ({
    meta: [
      { title: "Gen Studio · NEXUS EDU" },
      { name: "description", content: "Generate lectures, question papers, slides, summaries, and paper analyses." },
    ],
  }),
});

type Kind = "lecture" | "question-paper" | "presentation" | "summary" | "analysis";

const ACTIONS: {
  id: Kind;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  desc: string;
}[] = [
  { id: "lecture", label: "Lecture notes", icon: BookOpen, desc: "Comprehensive, structured lecture content." },
  { id: "question-paper", label: "Question paper", icon: ClipboardList, desc: "MCQs + short answers grounded in docs." },
  { id: "presentation", label: "Presentation", icon: Presentation, desc: "Slide deck with a downloadable .pptx." },
  { id: "summary", label: "Summary", icon: FileText, desc: "Structured summary of your documents." },
  { id: "analysis", label: "Paper analysis", icon: Microscope, desc: "Deep analysis of academic papers." },
];

function GeneratePage() {
  const [kind, setKind] = useState<Kind>("lecture");
  const [topic, setTopic] = useState("");
  const [notes, setNotes] = useState("");
  const [numSlides, setNumSlides] = useState(10);
  
  // Viewer states
  const [result, setResult] = useState<{ data: Record<string, unknown>; downloadUrl?: string; kind: string; topic: string } | null>(null);
  const [generationMs, setGenerationMs] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"rendered" | "json">("rendered");

  const m = useMutation({
    mutationFn: async () => {
      const payload = { topic, additional_instructions: notes };
      const start = Date.now();
      let res;
      switch (kind) {
        case "lecture":
          res = { data: await notesApi.lecture(payload) };
          break;
        case "question-paper":
          res = { data: await quizApi.questionPaper(payload) };
          break;
        case "summary":
          res = { data: await notesApi.summary(payload) };
          break;
        case "analysis":
          res = { data: await notesApi.analysis(payload) };
          break;
        case "presentation": {
          const r = await quizApi.presentation({ ...payload, num_slides: numSlides });
          res = { data: r, downloadUrl: r.download_url };
          break;
        }
      }
      return { ...res, ms: Date.now() - start };
    },
    onSuccess: (r) => {
      setGenerationMs(r.ms);
      setResult({ ...r, kind, topic });
      setViewMode("rendered");
      toast.success("Generation complete.");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-8 pb-20">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Gen Studio</h1>
        <p className="mt-1 text-muted-foreground">
          Pick an artifact type and let NEXUS synthesize from your workspace context.
        </p>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {ACTIONS.map((a) => {
          const active = a.id === kind;
          return (
            <motion.button
              key={a.id}
              onClick={() => setKind(a.id)}
              whileHover={{ y: -3 }}
              className={`glass-strong rounded-2xl p-4 text-left transition ${
                active ? "ring-2 ring-primary glow-cyan" : ""
              }`}
            >
              <a.icon className={`h-5 w-5 ${active ? "text-primary" : "text-muted-foreground"}`} />
              <div className="mt-2 text-sm font-semibold">{a.label}</div>
              <div className="mt-1 text-xs text-muted-foreground">{a.desc}</div>
            </motion.button>
          );
        })}
      </div>

      <div className="glass-strong grid grid-cols-1 gap-4 rounded-2xl p-6">
        <label className="block">
          <Label>Topic</Label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Support Vector Machines"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary"
          />
        </label>
        <label className="block">
          <Label>Additional instructions (optional)</Label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Tone, depth, audience, formatting preferences…"
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary"
          />
        </label>
        {kind === "presentation" && (
          <label className="block">
            <Label>Number of slides</Label>
            <input
              type="number"
              min={3}
              max={40}
              value={numSlides}
              onChange={(e) => setNumSlides(parseInt(e.target.value || "10", 10))}
              className="w-32 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </label>
        )}

        <div>
          <button
            disabled={!topic || m.isPending}
            onClick={() => m.mutate()}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-5 py-2.5 text-sm font-semibold text-primary-foreground glow-cyan disabled:opacity-60"
          >
            {m.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {m.isPending ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>

      {/* ── Results Area ─────────────────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        {m.isPending && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="glass-strong rounded-2xl p-12 text-center"
          >
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
            <h3 className="text-xl font-semibold text-foreground">AI is generating...</h3>
            <p className="mt-2 text-sm text-muted-foreground">Synthesizing documents and formatting output.</p>
          </motion.div>
        )}

        {m.isError && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-strong rounded-2xl p-8 border-destructive/30"
          >
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-destructive/20 text-destructive">
                <AlertCircle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-destructive">Generation Failed</h3>
                <p className="text-sm text-destructive/80">{m.error?.message}</p>
              </div>
              <button
                onClick={() => m.mutate()}
                className="ml-auto inline-flex items-center gap-2 rounded-xl bg-destructive/10 px-4 py-2 text-sm font-semibold text-destructive hover:bg-destructive/20"
              >
                <RefreshCw className="h-4 w-4" /> Retry
              </button>
            </div>
          </motion.div>
        )}

        {!m.isPending && !m.isError && !result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-strong rounded-2xl p-16 text-center"
          >
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-primary/10 to-secondary/10">
              <Sparkles className="h-10 w-10 text-primary/50" />
            </div>
            <h3 className="text-xl font-semibold text-foreground">Ready to Generate</h3>
            <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
              Select an artifact type above, enter a topic, and NEXUS will generate a structured response from your library.
            </p>
          </motion.div>
        )}

        {result && !m.isPending && (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="glass-strong rounded-2xl p-6 sm:p-8"
          >
            <ResultHeader kind={result.kind} generationMs={generationMs} topic={result.topic} />

            {/* Toolbar */}
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
              <div className="flex items-center gap-2 rounded-lg bg-black/20 p-1">
                <button
                  onClick={() => setViewMode("rendered")}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${viewMode === "rendered" ? "bg-white/10 text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                >
                  View Rendered
                </button>
                <button
                  onClick={() => setViewMode("json")}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${viewMode === "json" ? "bg-white/10 text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                >
                  View JSON
                </button>
              </div>

              <div className="flex flex-1 items-center justify-end gap-3">
                {viewMode === "rendered" && (
                  <div className="relative w-full max-w-xs">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search within result..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full rounded-full border border-white/10 bg-white/5 py-1.5 pl-9 pr-4 text-sm text-foreground outline-none transition focus:border-primary focus:bg-black/20"
                    />
                  </div>
                )}
                
                {result.downloadUrl && (
                  <a
                    href={result.downloadUrl.startsWith("http") ? result.downloadUrl : `${getApiBase()}${result.downloadUrl}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-1.5 text-xs font-medium text-primary-foreground transition hover:brightness-110"
                  >
                    <Download className="h-3.5 w-3.5" /> Download .pptx
                  </a>
                )}
              </div>
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
              {viewMode === "json" ? (
                <motion.pre
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="max-h-[800px] overflow-auto rounded-xl bg-black/40 p-4 text-xs leading-relaxed text-cyan-200 border border-white/5"
                >
                  {JSON.stringify(result.data, null, 2)}
                </motion.pre>
              ) : (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  {result.kind === "summary" && <SummaryRenderer data={result.data as any as SummaryData} searchQuery={searchQuery} />}
                  {result.kind === "lecture" && <LectureRenderer data={result.data as any as LectureData} searchQuery={searchQuery} />}
                  {result.kind === "question-paper" && <QuestionPaperRenderer data={result.data as any as QuestionPaperData} searchQuery={searchQuery} />}
                  {result.kind === "analysis" && <PaperAnalysisRenderer data={result.data as any as PaperAnalysisData} />}
                  {result.kind === "presentation" && <PresentationRenderer data={result.data as any as PresentationData} />}
                </motion.div>
              )}
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <span className="mb-1.5 block text-xs uppercase tracking-wide text-muted-foreground">{children}</span>;
}
