import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Presentation as PresentationIcon, Clock, Layers, ChevronDown, ChevronUp, Quote } from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────
interface TableData {
  headers: string[];
  rows: string[][];
}

interface ContentBlock {
  block_type: "bullet_points" | "paragraph" | "table" | "code_snippet" | "quote" | "key_concept";
  heading?: string | null;
  bullets?: string[] | null;
  paragraph?: string | null;
  table_data?: TableData | null;
  code?: string | null;
  quote_text?: string | null;
}

interface Slide {
  slide_number: number;
  slide_type: "title" | "content" | "image_placeholder" | "summary" | "quote" | "table" | "divider";
  title: string;
  content_blocks?: ContentBlock[] | null;
  speaker_notes: string;
  layout_hint: "full_text" | "two_column" | "title_only" | "bullets_right";
}

export interface PresentationData {
  title: string;
  subtitle?: string | null;
  course_name: string;
  author?: string | null;
  slide_count: number;
  slides: Slide[];
  theme_suggestion: string;
  metadata: any;
}

// ── Sub-components ─────────────────────────────────────────────────────────
function BlockRenderer({ block }: { block: ContentBlock }) {
  return (
    <div className="mb-4">
      {block.heading && <h4 className="mb-2 font-semibold text-foreground/90">{block.heading}</h4>}
      
      {block.block_type === "bullet_points" && block.bullets && (
        <ul className="list-inside list-disc space-y-1 text-[13px] text-muted-foreground/90 leading-relaxed">
          {block.bullets.map((b, i) => <li key={i}>{b}</li>)}
        </ul>
      )}

      {block.block_type === "paragraph" && block.paragraph && (
        <p className="text-[13px] leading-relaxed text-muted-foreground/90">{block.paragraph}</p>
      )}

      {block.block_type === "quote" && block.quote_text && (
        <div className="flex gap-3 border-l-2 border-primary/50 pl-4 py-2 italic text-muted-foreground">
          <Quote className="h-4 w-4 shrink-0 text-primary/40" />
          <p className="text-sm">"{block.quote_text}"</p>
        </div>
      )}

      {block.block_type === "key_concept" && block.quote_text && (
        <div className="rounded-lg bg-primary/10 border border-primary/20 p-3 text-center text-primary-foreground">
          <span className="font-semibold text-primary">{block.quote_text}</span>
        </div>
      )}

      {block.block_type === "code_snippet" && block.code && (
        <pre className="overflow-x-auto rounded-lg bg-black/40 p-3 text-xs text-blue-300 border border-white/5">
          <code>{block.code}</code>
        </pre>
      )}

      {block.block_type === "table" && block.table_data && (
        <div className="overflow-hidden rounded-lg border border-white/10">
          <table className="w-full text-left text-[11px]">
            <thead className="bg-white/5 text-muted-foreground">
              <tr>
                {block.table_data.headers.map((h, i) => (
                  <th key={i} className="px-3 py-2 font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {block.table_data.rows.map((row, i) => (
                <tr key={i} className="hover:bg-white/5">
                  {row.map((cell, j) => (
                    <td key={j} className="px-3 py-2 text-foreground/80">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SlideCard({ slide, index }: { slide: Slide; index: number }) {
  const [showNotes, setShowNotes] = useState(false);

  const isTitleSlide = slide.slide_type === "title";
  const isDivider = slide.slide_type === "divider";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="group relative"
    >
      <div className="absolute -left-12 top-4 hidden w-8 text-right text-xs font-bold text-muted-foreground/50 sm:block">
        {slide.slide_number}
      </div>

      <div className={`overflow-hidden rounded-xl border border-white/10 ${isTitleSlide ? 'bg-gradient-to-br from-primary/20 to-secondary/20' : isDivider ? 'bg-white/5' : 'glass'}`}>
        
        {/* Slide Aspect Ratio Container */}
        <div className="aspect-[16/9] w-full p-6 sm:p-8 flex flex-col justify-center relative">
          <span className="absolute top-4 right-4 text-[10px] font-bold tracking-widest text-muted-foreground/40 uppercase">
            {slide.slide_type}
          </span>
          
          <div className={`${(isTitleSlide || isDivider) ? 'text-center' : ''}`}>
            <h2 className={`${(isTitleSlide || isDivider) ? 'text-3xl sm:text-4xl' : 'text-xl sm:text-2xl mb-6'} font-bold tracking-tight text-foreground`}>
              {slide.title}
            </h2>

            {!isDivider && slide.content_blocks && (
              <div className={`mt-4 ${slide.layout_hint === 'two_column' ? 'grid grid-cols-2 gap-6' : ''}`}>
                {slide.content_blocks.map((b, i) => <BlockRenderer key={i} block={b} />)}
              </div>
            )}
          </div>
        </div>

        {/* Speaker Notes Toggle */}
        <div className="border-t border-white/10 bg-black/20">
          <button
            onClick={() => setShowNotes(!showNotes)}
            className="flex w-full items-center justify-between px-4 py-2.5 text-xs font-medium text-muted-foreground hover:bg-white/5 hover:text-foreground transition"
          >
            <span>Speaker Notes</span>
            {showNotes ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          
          <AnimatePresence>
            {showNotes && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="px-4 pb-4 pt-2 text-sm italic leading-relaxed text-muted-foreground border-t border-white/5">
                  {slide.speaker_notes}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

// ── Main Renderer ──────────────────────────────────────────────────────────
export function PresentationRenderer({ data }: { data: PresentationData }) {
  return (
    <div className="space-y-8">
      {/* ── Deck Info Header ────────────────────────────────────────────── */}
      <div className="glass-strong rounded-2xl p-6 flex flex-col items-center text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/20 text-primary mb-4">
          <PresentationIcon className="h-6 w-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl mb-2">{data.title}</h1>
        {data.subtitle && <p className="text-lg text-muted-foreground mb-4">{data.subtitle}</p>}
        
        <div className="flex flex-wrap justify-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5"><Layers className="h-4 w-4" /> {data.slide_count} Slides</span>
          <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" /> ~{data.metadata?.estimated_duration_minutes} min duration</span>
          {data.author && <span className="flex items-center gap-1.5 border-l border-white/10 pl-4">By {data.author}</span>}
        </div>
      </div>

      {/* ── Slide Deck ───────────────────────────────────────────────────── */}
      <div className="mx-auto max-w-4xl space-y-6 sm:pl-12">
        {data.slides.map((slide, i) => (
          <SlideCard key={slide.slide_number} slide={slide} index={i} />
        ))}
      </div>
    </div>
  );
}
