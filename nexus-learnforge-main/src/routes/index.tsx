import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { ArrowRight, Sparkles, Cpu, Layers } from "lucide-react";

import { AnimatedBackground } from "@/components/AnimatedBackground";
import { ClientOnly } from "@/components/ClientOnly";
import { ParticleHead } from "@/components/ParticleHead";

export const Route = createFileRoute("/")({
  component: Landing,
});

const GREETING = [
  "Hello.",
  "Welcome to NEXUS EDU.",
  "I'm delighted to welcome you.",
  "Your AI-powered educational operating system is now ready.",
  "Everything you need for smarter learning is just one step away.",
  "Please click the Explore More button to continue.",
  "I hope you enjoy your learning journey.",
].join(" ");

function useWelcomeVoice() {
  const spoken = useRef(false);
  useEffect(() => {
    if (spoken.current) return;
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    const speak = () => {
      if (spoken.current) return;
      spoken.current = true;
      try {
        const u = new SpeechSynthesisUtterance(GREETING);
        // Pick the warmest available English voice.
        const voices = window.speechSynthesis.getVoices();
        const pref =
          voices.find((v) => /Samantha|Google US English|Jenny|Aria|Zira/i.test(v.name)) ||
          voices.find((v) => v.lang?.startsWith("en"));
        if (pref) u.voice = pref;
        u.rate = 0.98;
        u.pitch = 1.05;
        u.volume = 0.95;
        window.speechSynthesis.speak(u);
      } catch {
        /* ignore */
      }
    };

    // Ensure voices are loaded, then wait 2.5s after hero-ready.
    const trigger = () => setTimeout(speak, 2500);
    if (window.speechSynthesis.getVoices().length) {
      trigger();
    } else {
      window.speechSynthesis.onvoiceschanged = () => trigger();
    }
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);
}

function Landing() {
  useWelcomeVoice();
  const navigate = useNavigate();
  const [magnet, setMagnet] = useState({ x: 0, y: 0 });

  const onMagnet = (e: React.MouseEvent<HTMLButtonElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    setMagnet({ x: (e.clientX - r.left - r.width / 2) * 0.3, y: (e.clientY - r.top - r.height / 2) * 0.3 });
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <AnimatedBackground />

      {/* Nav */}
      <header className="relative z-20 mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2"
        >
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-primary to-secondary glow-cyan">
            <Sparkles className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="font-display text-lg font-semibold tracking-tight">NEXUS EDU</span>
        </motion.div>
        <motion.nav
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="hidden items-center gap-6 text-sm text-muted-foreground md:flex"
        >
          <span className="hover:text-foreground transition">Features</span>
          <span className="hover:text-foreground transition">RAG Pipeline</span>
          <span className="hover:text-foreground transition">Generate</span>
          <Link to="/login" className="rounded-lg border border-border/60 px-3 py-1.5 text-foreground hover:bg-white/5">
            Sign in
          </Link>
        </motion.nav>
      </header>

      {/* Hero */}
      <main className="relative z-10 mx-auto grid max-w-7xl grid-cols-1 items-center gap-10 px-6 pb-24 pt-6 lg:grid-cols-2 lg:pt-14">
        <div>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="inline-flex items-center gap-2 rounded-full glass px-3 py-1 text-xs text-primary"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            AI Consciousness · Online
          </motion.p>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.7 }}
            className="mt-5 text-5xl font-semibold leading-[1.05] tracking-tight md:text-6xl lg:text-7xl"
          >
            The educational
            <br />
            <span className="text-gradient">operating system</span>
            <br />
            for a smarter mind.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
            className="mt-6 max-w-lg text-lg text-muted-foreground"
          >
            Upload your course material. Ask anything. Generate lectures, question papers, and
            slide decks — grounded in your own documents.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.65 }}
            className="mt-9 flex flex-wrap items-center gap-4"
          >
            <button
              onMouseMove={onMagnet}
              onMouseLeave={() => setMagnet({ x: 0, y: 0 })}
              onClick={() => navigate({ to: "/login" })}
              style={{ transform: `translate(${magnet.x}px, ${magnet.y}px)` }}
              className="group relative inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-secondary px-7 py-3.5 text-sm font-semibold text-primary-foreground shadow-lg transition-all duration-200 animate-pulse-glow"
            >
              <span className="absolute -inset-px rounded-full bg-gradient-to-r from-primary to-secondary opacity-70 blur-md" />
              <span className="relative">Explore More</span>
              <ArrowRight className="relative h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
            <Link
              to="/register"
              className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
            >
              Create an account →
            </Link>
          </motion.div>

          {/* Feature bullets */}
          <motion.div
            initial="hidden"
            animate="show"
            variants={{ hidden: {}, show: { transition: { staggerChildren: 0.1, delayChildren: 0.9 } } }}
            className="mt-12 grid grid-cols-1 gap-3 sm:grid-cols-3"
          >
            {[
              { icon: Layers, label: "RAG on your docs" },
              { icon: Cpu, label: "Groq-powered LLM" },
              { icon: Sparkles, label: "Slide & paper synthesis" },
            ].map((f, i) => (
              <motion.div
                key={i}
                variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}
                className="glass flex items-center gap-3 rounded-xl px-4 py-3 text-sm"
              >
                <f.icon className="h-4 w-4 text-primary" />
                <span>{f.label}</span>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* 3D Head */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.4, ease: "easeOut" }}
          className="relative h-[520px] lg:h-[640px]"
        >
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 blur-3xl" />
          <ClientOnly
            fallback={
              <div className="grid h-full w-full place-items-center text-sm text-muted-foreground">
                Initializing neural mesh…
              </div>
            }
          >
            <ParticleHead />
          </ClientOnly>
        </motion.div>
      </main>
    </div>
  );
}
