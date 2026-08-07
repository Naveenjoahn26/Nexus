import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Copy, Check, ChevronRight, Target, Key, Link as LinkIcon, BookMarked, Lightbulb } from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────
interface Reference {
  title: string;
  authors?: string[] | null;
  year?: number | null;
  url?: string | null;
}

interface KeyTerm {
  term: string;
  definition: string;
  related_terms?: string[] | null;
}

interface LectureSubsection {
  heading: string;
  content: string;
  bullet_points?: string[] | null;
}

interface LectureSection {
  section_number: number;
  heading: string;
  content: string;
  subsections?: LectureSubsection[] | null;
  key_takeaway: string;
  examples?: string[] | null;
}

export interface LectureData {
  title: string;
  course_name: string;
  lecture_number?: number | null;
  learning_objectives: string[];
  sections: LectureSection[];
  key_terms: KeyTerm[];
  summary: string;
  further_reading?: Reference[] | null;
  metadata: any;
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

function CopyButton({ text }: { text: string }) {
  const { copied, copy } = useCopy(text);
  return (
    <button
      onClick={copy}
      className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-muted-foreground transition hover:bg-white/10 hover:text-foreground"
      title="Copy"
    >
      {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

// ── Main Renderer ──────────────────────────────────────────────────────────
export function LectureRenderer({
  data,
  searchQuery = "",
}: {
  data: LectureData;
  searchQuery?: string;
}) {
  const [activeSection, setActiveSection] = useState<number | null>(null);

  const filteredSections = data.sections.filter(
    (s) =>
      s.heading.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 md:flex-row">
      {/* ── Table of Contents (Sidebar) ─────────────────────────────────── */}
      <div className="md:w-64 shrink-0">
        <div className="sticky top-24 glass-strong rounded-2xl p-4">
          <h4 className="mb-3 flex items-center gap-2 font-semibold text-foreground">
            <BookOpen className="h-4 w-4 text-primary" />
            Contents
          </h4>
          <nav className="flex flex-col gap-1">
            <a href="#summary" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition hover:bg-white/5 hover:text-foreground">
              Summary & Objectives
            </a>
            {data.sections.map((s) => (
              <a
                key={s.section_number}
                href={`#section-${s.section_number}`}
                className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition hover:bg-white/5 hover:text-foreground truncate"
              >
                {s.section_number}. {s.heading}
              </a>
            ))}
            <a href="#key-terms" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition hover:bg-white/5 hover:text-foreground">
              Glossary & Terms
            </a>
            {data.further_reading && data.further_reading.length > 0 && (
              <a href="#references" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition hover:bg-white/5 hover:text-foreground">
                References
              </a>
            )}
          </nav>
        </div>
      </div>

      {/* ── Content Area ─────────────────────────────────────────────────── */}
      <div className="flex-1 space-y-12 pb-24">
        
        {/* Course Info & Summary */}
        <section id="summary" className="space-y-6 scroll-mt-24">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <span>{data.course_name}</span>
              {data.lecture_number && (
                <>
                  <span>•</span>
                  <span>Lecture {data.lecture_number}</span>
                </>
              )}
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">{data.title}</h1>
          </div>

          <div className="glass-strong rounded-2xl p-6 relative">
             <div className="absolute top-0 right-0 p-4">
               <CopyButton text={data.summary} />
             </div>
             <p className="text-base leading-relaxed text-foreground/90 pr-16">{data.summary}</p>
          </div>

          <div className="glass rounded-xl p-5 border-cyan-500/20">
            <h3 className="mb-3 flex items-center gap-2 font-semibold text-cyan-300">
              <Target className="h-4 w-4" /> Learning Objectives
            </h3>
            <ul className="space-y-2">
              {data.learning_objectives.map((obj, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <span className="mt-1.5 block h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400/50" />
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Sections */}
        {filteredSections.map((section, idx) => (
          <motion.section
            key={section.section_number}
            id={`section-${section.section_number}`}
            className="scroll-mt-24 space-y-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <div className="group relative">
              <h2 className="flex items-center gap-3 text-2xl font-semibold text-foreground">
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/20 text-sm text-primary">
                  {section.section_number}
                </span>
                {section.heading}
              </h2>
            </div>

            <div className="prose prose-invert max-w-none prose-p:leading-relaxed text-muted-foreground">
              <p>{section.content}</p>
            </div>

            {/* Subsections */}
            {section.subsections && section.subsections.length > 0 && (
              <div className="ml-4 space-y-6 border-l-2 border-border/50 pl-6">
                {section.subsections.map((sub, i) => (
                  <div key={i} className="space-y-3">
                    <h3 className="text-lg font-medium text-foreground">{sub.heading}</h3>
                    <p className="text-sm leading-relaxed text-muted-foreground">{sub.content}</p>
                    {sub.bullet_points && sub.bullet_points.length > 0 && (
                      <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
                        {sub.bullet_points.map((bp, j) => (
                          <li key={j}>{bp}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Callouts */}
            <div className="grid gap-4 sm:grid-cols-2">
              {section.examples && section.examples.length > 0 && (
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                  <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-emerald-400">
                    <Lightbulb className="h-4 w-4" /> Examples
                  </h4>
                  <ul className="space-y-2">
                    {section.examples.map((ex, i) => (
                      <li key={i} className="text-sm text-emerald-200/70">{ex}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 sm:col-span-1">
                <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-400">
                  <Target className="h-4 w-4" /> Key Takeaway
                </h4>
                <p className="text-sm text-amber-200/70">{section.key_takeaway}</p>
              </div>
            </div>
          </motion.section>
        ))}

        {/* Glossary */}
        {data.key_terms.length > 0 && (
          <section id="key-terms" className="scroll-mt-24 space-y-4 pt-8">
            <h2 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
              <Key className="h-5 w-5 text-purple-400" /> Glossary
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {data.key_terms.map((term, i) => (
                <div key={i} className="glass rounded-xl p-4 transition hover:bg-white/5">
                  <h4 className="font-semibold text-purple-300">{term.term}</h4>
                  <p className="mt-1 text-sm text-muted-foreground">{term.definition}</p>
                  {term.related_terms && term.related_terms.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {term.related_terms.map(rt => (
                        <span key={rt} className="rounded-md bg-white/5 px-2 py-0.5 text-[10px] text-muted-foreground">
                          {rt}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* References */}
        {data.further_reading && data.further_reading.length > 0 && (
          <section id="references" className="scroll-mt-24 space-y-4 pt-8 border-t border-border/40">
            <h2 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
              <BookMarked className="h-5 w-5 text-blue-400" /> Further Reading
            </h2>
            <div className="space-y-2">
              {data.further_reading.map((ref, i) => (
                <div key={i} className="flex items-start gap-3 rounded-xl p-3 hover:bg-white/5">
                  <LinkIcon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                  <div>
                    <h4 className="font-medium text-foreground">
                      {ref.url ? (
                        <a href={ref.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-400 hover:underline">
                          {ref.title}
                        </a>
                      ) : ref.title}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {ref.authors?.join(", ")} {ref.year ? `(${ref.year})` : ""}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
