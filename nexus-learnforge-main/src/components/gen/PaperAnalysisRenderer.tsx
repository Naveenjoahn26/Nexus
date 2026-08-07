import { motion } from "framer-motion";
import {
  FileText, Users, Link as LinkIcon, Calendar, Microscope,
  Search, Flag, Target, ArrowRight, Lightbulb, TrendingUp, AlertTriangle, CheckCircle2
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────
interface MethodologyBlock {
  methodology_type: string;
  description: string;
  datasets_used?: string[] | null;
  evaluation_metrics?: string[] | null;
  tools_and_frameworks?: string[] | null;
}

interface Finding {
  finding_number: number;
  claim: string;
  evidence: string;
  significance: "high" | "medium" | "low";
  directly_quoted: boolean;
}

interface RelatedWork {
  title: string;
  authors?: string[] | null;
  relationship: "builds_upon" | "contradicts" | "extends" | "compares" | "uses";
  summary: string;
}

interface CriticalEvaluation {
  overall_quality: "excellent" | "good" | "fair" | "poor";
  novelty_score: number;
  methodological_rigor: number;
  reproducibility_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendation: "highly_recommend" | "recommend" | "neutral" | "not_recommend";
}

export interface PaperAnalysisData {
  paper_title: string;
  authors: string[];
  publication_year?: number | null;
  doi_or_url?: string | null;
  abstract_summary: string;
  research_problem: string;
  research_questions: string[];
  methodology: MethodologyBlock;
  key_findings: Finding[];
  contributions: string[];
  limitations: string[];
  future_work?: string[] | null;
  related_works?: RelatedWork[] | null;
  critical_evaluation: CriticalEvaluation;
  metadata: any;
}

// ── Config ─────────────────────────────────────────────────────────────────
const REC_COLORS = {
  highly_recommend: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  recommend: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  neutral: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  not_recommend: "bg-red-500/20 text-red-400 border-red-500/30",
};

const SIG_COLORS = {
  high: "bg-red-500/20 text-red-400 border-red-500/30",
  medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

const QUAL_COLORS = {
  excellent: "text-emerald-400",
  good: "text-blue-400",
  fair: "text-amber-400",
  poor: "text-red-400",
};

// ── Main Renderer ──────────────────────────────────────────────────────────
export function PaperAnalysisRenderer({
  data,
}: {
  data: PaperAnalysisData;
}) {
  const evalData = data.critical_evaluation;

  return (
    <div className="space-y-8">
      {/* ── Header Card ──────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass-strong rounded-2xl p-6 text-center">
        <h1 className="mb-4 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">{data.paper_title}</h1>
        
        <div className="mb-4 flex flex-wrap items-center justify-center gap-2">
          <Users className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">{data.authors.join(", ")}</span>
        </div>
        
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-muted-foreground">
          {data.publication_year && (
            <span className="flex items-center gap-1.5"><Calendar className="h-4 w-4" /> {data.publication_year}</span>
          )}
          {data.doi_or_url && (
            <span className="flex items-center gap-1.5">
              <LinkIcon className="h-4 w-4" />
              <a href={data.doi_or_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                {data.doi_or_url.startsWith("http") ? "Source Link" : data.doi_or_url}
              </a>
            </span>
          )}
        </div>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* ── Left Column ──────────────────────────────────────────────────── */}
        <div className="space-y-6 md:col-span-2">
          
          <section className="glass rounded-2xl p-6">
            <h3 className="mb-3 font-semibold text-foreground flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" /> Abstract Summary
            </h3>
            <p className="text-sm leading-relaxed text-muted-foreground">{data.abstract_summary}</p>
          </section>

          <section className="glass rounded-2xl p-6 border-amber-500/20">
            <h3 className="mb-3 font-semibold text-amber-400 flex items-center gap-2">
              <Target className="h-4 w-4" /> Research Problem & Questions
            </h3>
            <p className="mb-4 text-sm leading-relaxed text-amber-100/80">{data.research_problem}</p>
            <ul className="space-y-2">
              {data.research_questions.map((q, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-amber-200/70">
                  <span className="mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-400">{i + 1}</span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="glass rounded-2xl p-6">
            <h3 className="mb-4 font-semibold text-foreground flex items-center gap-2">
              <Microscope className="h-4 w-4 text-purple-400" /> Methodology
            </h3>
            <div className="mb-4">
              <span className="inline-flex rounded-full border border-purple-500/30 bg-purple-500/20 px-2.5 py-0.5 text-xs font-medium uppercase tracking-wider text-purple-300">
                {data.methodology.methodology_type.replace("_", " ")}
              </span>
            </div>
            <p className="mb-4 text-sm leading-relaxed text-muted-foreground">{data.methodology.description}</p>
            
            <div className="grid gap-4 sm:grid-cols-2">
              {data.methodology.datasets_used && data.methodology.datasets_used.length > 0 && (
                <div className="rounded-xl bg-white/5 p-3">
                  <span className="mb-2 block text-xs font-medium text-muted-foreground">Datasets</span>
                  <div className="flex flex-wrap gap-1">
                    {data.methodology.datasets_used.map(d => <span key={d} className="rounded-md bg-white/10 px-2 py-0.5 text-[11px] text-foreground">{d}</span>)}
                  </div>
                </div>
              )}
              {data.methodology.evaluation_metrics && data.methodology.evaluation_metrics.length > 0 && (
                <div className="rounded-xl bg-white/5 p-3">
                  <span className="mb-2 block text-xs font-medium text-muted-foreground">Metrics</span>
                  <div className="flex flex-wrap gap-1">
                    {data.methodology.evaluation_metrics.map(m => <span key={m} className="rounded-md bg-white/10 px-2 py-0.5 text-[11px] text-foreground">{m}</span>)}
                  </div>
                </div>
              )}
            </div>
          </section>

          <section className="space-y-4">
            <h3 className="font-semibold text-foreground flex items-center gap-2">
              <Search className="h-4 w-4 text-cyan-400" /> Key Findings
            </h3>
            {data.key_findings.map((finding) => {
              const sigCls = SIG_COLORS[finding.significance];
              return (
                <motion.div key={finding.finding_number} className="glass rounded-2xl p-5 relative overflow-hidden" whileHover={{ y: -2 }}>
                  {finding.directly_quoted && <div className="absolute top-0 right-0 rounded-bl-xl bg-blue-500/20 px-2 py-1 text-[10px] font-semibold text-blue-300">Direct Quote</div>}
                  <div className="mb-2 flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-500/20 text-[10px] font-bold text-cyan-400">{finding.finding_number}</span>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${sigCls}`}>
                      {finding.significance} Impact
                    </span>
                  </div>
                  <p className="mb-3 text-sm font-medium text-foreground">{finding.claim}</p>
                  <p className="text-xs text-muted-foreground border-l-2 border-border/50 pl-3"><span className="font-semibold text-foreground/70">Evidence:</span> {finding.evidence}</p>
                </motion.div>
              );
            })}
          </section>

        </div>

        {/* ── Right Column ─────────────────────────────────────────────────── */}
        <div className="space-y-6">

          <section className="glass-strong rounded-2xl p-5 border-t-4 border-t-emerald-500/50">
            <h3 className="mb-4 font-bold text-foreground">Critical Evaluation</h3>
            
            <div className="mb-6 space-y-4">
              <div>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-muted-foreground">Novelty</span>
                  <span className="font-bold text-emerald-400">{evalData.novelty_score}/10</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div className="h-full bg-emerald-400" style={{ width: `${evalData.novelty_score * 10}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-muted-foreground">Rigor</span>
                  <span className="font-bold text-blue-400">{evalData.methodological_rigor}/10</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div className="h-full bg-blue-400" style={{ width: `${evalData.methodological_rigor * 10}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-muted-foreground">Reproducibility</span>
                  <span className="font-bold text-purple-400">{evalData.reproducibility_score}/10</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div className="h-full bg-purple-400" style={{ width: `${evalData.reproducibility_score * 10}%` }} />
                </div>
              </div>
            </div>

            <div className="mb-4 text-center">
              <span className={`block text-lg font-bold ${QUAL_COLORS[evalData.overall_quality]}`}>
                {evalData.overall_quality.toUpperCase()}
              </span>
              <span className="text-xs text-muted-foreground">Overall Quality</span>
            </div>

            <div className={`mt-6 rounded-xl border p-3 text-center ${REC_COLORS[evalData.recommendation]}`}>
              <div className="text-xs font-bold uppercase tracking-wider">Verdict</div>
              <div className="text-sm font-medium">{evalData.recommendation.replace("_", " ")}</div>
            </div>
          </section>

          <section className="glass rounded-2xl p-5 border-emerald-500/20">
            <h3 className="mb-3 font-semibold text-emerald-400 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> Contributions
            </h3>
            <ul className="space-y-2">
              {data.contributions.map((c, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-emerald-100/70">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500/50" />
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="glass rounded-2xl p-5 border-red-500/20">
            <h3 className="mb-3 font-semibold text-red-400 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" /> Limitations
            </h3>
            <ul className="space-y-2">
              {data.limitations.map((l, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-red-100/70">
                  <Flag className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-500/50" />
                  <span>{l}</span>
                </li>
              ))}
            </ul>
          </section>

          {data.future_work && data.future_work.length > 0 && (
            <section className="glass rounded-2xl p-5 border-blue-500/20">
              <h3 className="mb-3 font-semibold text-blue-400 flex items-center gap-2">
                <ArrowRight className="h-4 w-4" /> Future Work
              </h3>
              <ul className="space-y-2 text-sm text-blue-100/70 list-disc list-inside">
                {data.future_work.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </section>
          )}

        </div>
      </div>
    </div>
  );
}
