import { motion } from "framer-motion";
import { CheckCircle2, Clock, FileText, Bot, Zap } from "lucide-react";

interface ResultHeaderProps {
  kind: string;
  generationMs: number;
  topic: string;
}

const KIND_LABELS: Record<string, string> = {
  lecture: "Lecture Notes",
  "question-paper": "Question Paper",
  summary: "Summary",
  analysis: "Paper Analysis",
  presentation: "Presentation",
};

const KIND_COLORS: Record<string, string> = {
  lecture: "from-blue-500/20 to-cyan-500/20 border-blue-500/30 text-blue-300",
  "question-paper": "from-purple-500/20 to-pink-500/20 border-purple-500/30 text-purple-300",
  summary: "from-emerald-500/20 to-teal-500/20 border-emerald-500/30 text-emerald-300",
  analysis: "from-amber-500/20 to-orange-500/20 border-amber-500/30 text-amber-300",
  presentation: "from-rose-500/20 to-pink-500/20 border-rose-500/30 text-rose-300",
};

export function ResultHeader({ kind, generationMs, topic }: ResultHeaderProps) {
  const sec = (generationMs / 1000).toFixed(1);
  const label = KIND_LABELS[kind] ?? kind;
  const colorClass = KIND_COLORS[kind] ?? "from-primary/20 to-secondary/20 border-primary/30 text-primary";

  const badges = [
    {
      icon: <CheckCircle2 className="h-3.5 w-3.5" />,
      label: "Generated",
      value: label,
      cls: colorClass,
    },
    {
      icon: <Zap className="h-3.5 w-3.5" />,
      label: "Time",
      value: `${sec}s`,
      cls: "from-cyan-500/20 to-blue-500/20 border-cyan-500/30 text-cyan-300",
    },
    {
      icon: <Bot className="h-3.5 w-3.5" />,
      label: "Model",
      value: "Gemini",
      cls: "from-violet-500/20 to-purple-500/20 border-violet-500/30 text-violet-300",
    },
  ];

  return (
    <div className="mb-6">
      {/* Heading row */}
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-primary/30 to-secondary/30">
          <Zap className="h-4 w-4 text-primary" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
              ✨ AI Generated Content
            </span>
          </div>
          <h2 className="text-lg font-semibold leading-tight">
            {topic || "Generated Result"}
          </h2>
        </div>
      </div>

      {/* Badge row */}
      <motion.div
        className="flex flex-wrap gap-2"
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
      >
        {badges.map((b) => (
          <motion.div
            key={b.label}
            variants={{ hidden: { opacity: 0, scale: 0.85 }, visible: { opacity: 1, scale: 1 } }}
            className={`flex items-center gap-1.5 rounded-full border bg-gradient-to-r px-3 py-1 text-xs font-medium ${b.cls}`}
          >
            {b.icon}
            <span className="text-muted-foreground">{b.label}:</span>
            <span>{b.value}</span>
          </motion.div>
        ))}

        {/* Topic badge */}
        {topic && (
          <motion.div
            variants={{ hidden: { opacity: 0, scale: 0.85 }, visible: { opacity: 1, scale: 1 } }}
            className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-muted-foreground"
          >
            <FileText className="h-3.5 w-3.5" />
            <span className="truncate max-w-[200px]">{topic}</span>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
