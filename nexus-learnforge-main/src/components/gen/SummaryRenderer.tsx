import { useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  Copy, Check, ChevronDown, ChevronUp, Tag, AlertCircle,
  BookOpen, Lightbulb, Brain, Clock, BarChart3, Layers
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────
interface KeyPoint {
  point_number: number;
  heading: string;
  detail: string;
  importance: "critical" | "important" | "supplementary";
  source_chunk_ids: string[];
}

interface SummaryMetadata {
  generated_at: string;
  source_document_ids: string[];
  word_count: number;
  compression_ratio: number;
  topics_covered: string[];
}

export interface SummaryData {
  title: string;
  summary_type: string;
  executive_summary: string;
  key_points: KeyPoint[];
  concepts_introduced: string[];
  concepts_prerequisite?: string[] | null;
  difficulty_level: "beginner" | "intermediate" | "advanced";
  estimated_read_time_minutes: number;
  tags: string[];
  metadata: SummaryMetadata;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function useCopy(text: string) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return { copied, copy };
}

const IMPORTANCE_CONFIG = {
  critical:      { label: "Critical",      cls: "bg-red-500/20 border-red-500/30 text-red-300",    dot: "bg-red-400" },
  important:     { label: "Important",     cls: "bg-orange-500/20 border-orange-500/30 text-orange-300", dot: "bg-orange-400" },
  supplementary: { label: "Supplementary", cls: "bg-blue-500/20 border-blue-500/30 text-blue-300",  dot: "bg-blue-400" },
};

const DIFFICULTY_CONFIG = {
  beginner:     { label: "Beginner",     cls: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
  intermediate: { label: "Intermediate", cls: "bg-amber-500/20 text-amber-300 border-amber-500/30" },
  advanced:     { label: "Advanced",     cls: "bg-red-500/20 text-red-300 border-red-500/30" },
};

// ── Sub-components ─────────────────────────────────────────────────────────
function CopyButton({ text, size = "sm" }: { text: string; size?: "sm" | "xs" }) {
  const { copied, copy } = useCopy(text);
  return (
    <button
      onClick={copy}
      className={`flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-muted-foreground transition hover:bg-white/10 hover:text-foreground ${size === "xs" ? "px-1.5 py-0.5" : ""}`}
      title="Copy"
    >
      {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function KeyPointCard({ point, index, searchQuery }: { point: KeyPoint; index: number; searchQuery: string }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const cfg = IMPORTANCE_CONFIG[point.importance] ?? IMPORTANCE_CONFIG.supplementary;

  // Filter highlight
  if (
    searchQuery &&
    !point.heading.toLowerCase().includes(searchQuery.toLowerCase()) &&
    !point.detail.toLowerCase().includes(searchQuery.toLowerCase())
  ) {
    return null;
  }

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 28 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.45, delay: index * 0.07, ease: "easeOut" }}
      className="glass-strong rounded-2xl p-5 transition hover:border-white/20"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/30 to-secondary/30 text-xs font-bold text-primary">
            {point.point_number}
          </span>
          <h4 className="font-semibold text-foreground">{point.heading}</h4>
        </div>
        <span className={`shrink-0 flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${cfg.cls}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
          {cfg.label}
        </span>
      </div>

      <p className="mb-3 text-sm leading-relaxed text-muted-foreground">{point.detail}</p>

      {point.source_chunk_ids?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {point.source_chunk_ids.map((id, i) => (
            <span key={id} className="rounded-md bg-white/5 px-2 py-0.5 text-[10px] text-muted-foreground">
              ✓ Source {i + 1}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// ── Main Renderer ──────────────────────────────────────────────────────────
export function SummaryRenderer({
  data,
  searchQuery = "",
}: {
  data: SummaryData;
  searchQuery?: string;
}) {
  const [showAllConcepts, setShowAllConcepts] = useState(false);
  const executiveText = data.executive_summary ?? "";
  const { copied: execCopied, copy: copyExec } = useCopy(executiveText);

  const diffCfg = DIFFICULTY_CONFIG[data.difficulty_level] ?? DIFFICULTY_CONFIG.intermediate;

  const allText = [data.title, data.executive_summary, ...data.key_points.map(k => k.heading + " " + k.detail)].join(" ");

  return (
    <div className="space-y-8">
      {/* ── Executive Summary ─────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-3 flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-primary" />
          <h3 className="font-semibold text-foreground">Executive Summary</h3>
        </div>

        <div className="glass-strong relative rounded-2xl p-6">
          {/* Gradient accent */}
          <div className="pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/5 to-secondary/5" />

          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${diffCfg.cls}`}>
                {diffCfg.label}
              </span>
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                ~{data.estimated_read_time_minutes} min read
              </span>
            </div>
            <CopyButton text={executiveText} />
          </div>

          <p className="relative text-base leading-8 text-foreground/90">
            {executiveText}
          </p>

          {/* Tags */}
          {data.tags?.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {data.tags.map((tag) => (
                <span key={tag} className="flex items-center gap-1 rounded-md bg-white/5 px-2 py-0.5 text-[11px] text-muted-foreground">
                  <Tag className="h-2.5 w-2.5" />
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </motion.section>

      {/* ── Quick Stats ────────────────────────────────────── */}
      <motion.div
        className="grid grid-cols-3 gap-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15 }}
      >
        {[
          { icon: <Layers className="h-4 w-4" />, label: "Key Points", value: data.key_points?.length ?? 0, color: "text-cyan-400" },
          { icon: <Brain className="h-4 w-4" />, label: "Concepts", value: data.concepts_introduced?.length ?? 0, color: "text-purple-400" },
          { icon: <BarChart3 className="h-4 w-4" />, label: "Compression", value: `${Math.round((data.metadata?.compression_ratio ?? 0) * 100)}%`, color: "text-emerald-400" },
        ].map((stat) => (
          <div key={stat.label} className="glass rounded-xl p-4 text-center">
            <div className={`mb-1 flex justify-center ${stat.color}`}>{stat.icon}</div>
            <div className="text-xl font-bold text-foreground">{stat.value}</div>
            <div className="text-xs text-muted-foreground">{stat.label}</div>
          </div>
        ))}
      </motion.div>

      {/* ── Key Insights ───────────────────────────────────── */}
      {data.key_points?.length > 0 && (
        <section>
          <div className="mb-4 flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            <h3 className="font-semibold text-foreground">Key Insights</h3>
            <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-muted-foreground">
              {data.key_points.length}
            </span>
          </div>
          <div className="space-y-3">
            {data.key_points.map((pt, i) => (
              <KeyPointCard key={pt.point_number} point={pt} index={i} searchQuery={searchQuery} />
            ))}
          </div>
        </section>
      )}

      {/* ── Concepts Introduced ─────────────────────────────── */}
      {data.concepts_introduced?.length > 0 && (
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="mb-3 flex items-center gap-2">
            <Brain className="h-4 w-4 text-purple-400" />
            <h3 className="font-semibold text-foreground">Concepts Introduced</h3>
          </div>
          <div className="glass rounded-xl p-4">
            <div className="flex flex-wrap gap-2">
              {(showAllConcepts ? data.concepts_introduced : data.concepts_introduced.slice(0, 8)).map((c) => (
                <span key={c} className="rounded-lg bg-purple-500/10 border border-purple-500/20 px-3 py-1 text-sm text-purple-200">
                  {c}
                </span>
              ))}
              {data.concepts_introduced.length > 8 && (
                <button
                  onClick={() => setShowAllConcepts(!showAllConcepts)}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 text-sm text-muted-foreground hover:text-foreground"
                >
                  {showAllConcepts ? "Show less" : `+${data.concepts_introduced.length - 8} more`}
                </button>
              )}
            </div>
          </div>
        </motion.section>
      )}

      {/* ── Topics Covered ───────────────────────────────────── */}
      {data.metadata?.topics_covered?.length > 0 && (
        <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
          <div className="mb-3 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-cyan-400" />
            <h3 className="font-semibold text-foreground">Topics Covered</h3>
          </div>
          <div className="glass rounded-xl p-4">
            <div className="flex flex-wrap gap-2">
              {data.metadata.topics_covered.map((t) => (
                <span key={t} className="rounded-lg bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 text-sm text-cyan-200">
                  {t}
                </span>
              ))}
            </div>
          </div>
        </motion.section>
      )}

      {/* ── Copy All ─────────────────────────────────────────── */}
      <div className="flex justify-end">
        <CopyButton text={allText} />
      </div>
    </div>
  );
}
