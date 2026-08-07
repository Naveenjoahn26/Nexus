import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ClipboardList, Clock, Hash, HelpCircle, AlertCircle, Eye, EyeOff,
  CheckCircle2, Target, Lightbulb
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────
interface MCQOption {
  label: "A" | "B" | "C" | "D";
  text: string;
  is_correct: boolean;
}

interface Question {
  question_number: number;
  question_text: string;
  question_type: "MCQ" | "SHORT_ANSWER" | "LONG_ANSWER" | "CASE_STUDY" | "NUMERICAL" | "TRUE_FALSE";
  marks: number;
  difficulty: "easy" | "medium" | "hard";
  bloom_level: string;
  topic: string;
  expected_word_count?: number | null;
  options?: MCQOption[] | null;
  hints?: string[] | null;
}

interface Section {
  section_label: string;
  section_title: string;
  instructions?: string | null;
  questions_to_attempt?: number | null;
  questions: Question[];
  section_marks: number;
}

export interface QuestionPaperData {
  title: string;
  course_name: string;
  subject_area: string;
  exam_duration_minutes: number;
  total_marks: number;
  instructions: string[];
  sections: Section[];
  metadata: any;
}

// ── Config ─────────────────────────────────────────────────────────────────
const DIFF_COLORS = {
  easy: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  hard: "bg-red-500/20 text-red-400 border-red-500/30",
};

const BLOOM_COLORS: Record<string, string> = {
  remember: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  understand: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  apply: "bg-teal-500/20 text-teal-400 border-teal-500/30",
  analyze: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  evaluate: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  create: "bg-rose-500/20 text-rose-400 border-rose-500/30",
};

// ── Sub-components ─────────────────────────────────────────────────────────
function AnswerReveal({ question }: { question: Question }) {
  const [open, setOpen] = useState(false);
  const hasOptions = question.options && question.options.length > 0;
  
  if (!hasOptions && (!question.hints || question.hints.length === 0)) return null;

  return (
    <div className="mt-4 border-t border-border/40 pt-4">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground transition"
      >
        {open ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        {open ? "Hide Details" : "Show Expected Answer / Hints"}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-4 rounded-xl bg-black/20 p-4">
              {hasOptions && (
                <div>
                  <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Expected Answer</h5>
                  <div className="space-y-2">
                    {question.options!.map((opt) => (
                      <div key={opt.label} className={`flex items-center gap-3 rounded-lg p-2 text-sm ${opt.is_correct ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'text-muted-foreground'}`}>
                        <div className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${opt.is_correct ? 'bg-emerald-500 text-white' : 'bg-white/10'}`}>
                          {opt.label}
                        </div>
                        <span>{opt.text}</span>
                        {opt.is_correct && <CheckCircle2 className="ml-auto h-4 w-4 text-emerald-400" />}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {question.hints && question.hints.length > 0 && (
                <div>
                  <h5 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-amber-400">
                    <Lightbulb className="h-3.5 w-3.5" /> Hints
                  </h5>
                  <ul className="list-inside list-disc space-y-1 text-sm text-amber-200/70">
                    {question.hints.map((hint, i) => <li key={i}>{hint}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function QuestionCard({ q, index }: { q: Question; index: number }) {
  const diffCls = DIFF_COLORS[q.difficulty] ?? DIFF_COLORS.medium;
  const bloomCls = BLOOM_COLORS[q.bloom_level] ?? "bg-white/10 text-muted-foreground border-white/20";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="glass rounded-2xl p-5"
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 font-bold text-primary">
            {q.question_number}
          </span>
          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${diffCls}`}>
            {q.difficulty}
          </span>
          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${bloomCls}`}>
            {q.bloom_level}
          </span>
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            {q.question_type.replace("_", " ")}
          </span>
        </div>
        <div className="font-semibold text-foreground">
          {q.marks} {q.marks === 1 ? "Mark" : "Marks"}
        </div>
      </div>

      <div className="mb-3 text-base leading-relaxed text-foreground/90">
        {q.question_text}
      </div>

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1"><Target className="h-3 w-3" /> Topic: {q.topic}</span>
        {q.expected_word_count && (
          <span className="flex items-center gap-1"><ClipboardList className="h-3 w-3" /> ~{q.expected_word_count} words</span>
        )}
      </div>

      <AnswerReveal question={q} />
    </motion.div>
  );
}

// ── Main Renderer ──────────────────────────────────────────────────────────
export function QuestionPaperRenderer({
  data,
  searchQuery = "",
}: {
  data: QuestionPaperData;
  searchQuery?: string;
}) {
  const totalQuestions = data.sections.reduce((acc, s) => acc + s.questions.length, 0);

  return (
    <div className="space-y-8">
      {/* ── Paper Info Header ────────────────────────────────────────────── */}
      <div className="glass-strong rounded-2xl p-6 text-center">
        <div className="mx-auto mb-2 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          <span>{data.course_name}</span>
          <span>•</span>
          <span>{data.subject_area}</span>
        </div>
        <h1 className="mb-4 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          {data.title}
        </h1>
        
        <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" /> {data.exam_duration_minutes} Minutes</span>
          <span className="flex items-center gap-1.5"><Target className="h-4 w-4" /> {data.total_marks} Total Marks</span>
          <span className="flex items-center gap-1.5"><Hash className="h-4 w-4" /> {totalQuestions} Questions</span>
        </div>
      </div>

      {/* ── Instructions ─────────────────────────────────────────────────── */}
      <div className="glass rounded-xl p-5 border-amber-500/20">
        <h3 className="mb-3 flex items-center gap-2 font-semibold text-amber-400">
          <AlertCircle className="h-4 w-4" /> General Instructions
        </h3>
        <ul className="list-inside list-decimal space-y-1 text-sm text-amber-200/80">
          {data.instructions.map((inst, i) => (
            <li key={i}>{inst}</li>
          ))}
        </ul>
      </div>

      {/* ── Sections ─────────────────────────────────────────────────────── */}
      <div className="space-y-10">
        {data.sections.map((section, sIdx) => {
          const filteredQ = section.questions.filter(q => 
            searchQuery ? 
              q.question_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
              q.topic.toLowerCase().includes(searchQuery.toLowerCase())
            : true
          );

          if (filteredQ.length === 0) return null;

          return (
            <section key={section.section_label} className="space-y-4">
              <div className="flex items-end justify-between border-b border-border/50 pb-2">
                <div>
                  <h2 className="text-xl font-bold text-foreground">
                    Section {section.section_label}: {section.section_title}
                  </h2>
                  {(section.instructions || section.questions_to_attempt) && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {section.instructions}
                      {section.questions_to_attempt && ` (Attempt any ${section.questions_to_attempt})`}
                    </p>
                  )}
                </div>
                <div className="font-semibold text-primary">
                  {section.section_marks} Marks
                </div>
              </div>

              <div className="space-y-4">
                {filteredQ.map((q, qIdx) => (
                  <QuestionCard key={q.question_number} q={q} index={qIdx} />
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
