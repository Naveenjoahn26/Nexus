import { useEffect, useRef } from "react";

/**
 * Full-viewport animated backdrop: aurora gradient, drifting orbs,
 * grid lines, and a subtle mouse-reactive light.
 * Pure CSS/DOM — cheap enough to layer under Three.js scenes.
 */
export function AnimatedBackground() {
  const spot = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const el = spot.current;
      if (!el) return;
      el.style.transform = `translate3d(${e.clientX - 300}px, ${e.clientY - 300}px, 0)`;
    };
    window.addEventListener("pointermove", onMove);
    return () => window.removeEventListener("pointermove", onMove);
  }, []);

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-background">
      {/* Aurora */}
      <div className="absolute inset-0 bg-aurora animate-aurora opacity-90" />
      {/* Grid lines */}
      <div className="absolute inset-0 grid-lines opacity-40" />
      {/* Floating orbs */}
      <div className="absolute -top-32 -left-32 h-[420px] w-[420px] rounded-full bg-primary/25 blur-3xl animate-float-slow" />
      <div
        className="absolute top-1/3 -right-40 h-[520px] w-[520px] rounded-full bg-secondary/25 blur-3xl animate-float-slow"
        style={{ animationDelay: "-3s" }}
      />
      <div
        className="absolute bottom-0 left-1/3 h-[360px] w-[360px] rounded-full bg-primary/15 blur-3xl animate-float-slow"
        style={{ animationDelay: "-1.5s" }}
      />
      {/* Mouse spotlight */}
      <div
        ref={spot}
        className="absolute h-[600px] w-[600px] rounded-full opacity-40 blur-3xl transition-transform duration-300 ease-out"
        style={{
          background:
            "radial-gradient(closest-side, oklch(0.85 0.19 200 / 0.35), transparent 70%)",
        }}
      />
      {/* Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,oklch(0.10_0.03_265/0.8))]" />
    </div>
  );
}
