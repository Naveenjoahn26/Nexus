import { lazy, Suspense, useEffect, useState } from "react";
import { CanvasParticleHead } from "./CanvasParticleHead";
import { detectWebGLSupport } from "./WebGLSupportDetector";

// Lazy-load the Three.js bundle so it's only fetched when WebGL is available.
const ThreeParticleHead = lazy(() => import("./ThreeParticleHead"));

/**
 * Error boundary that swaps to the Canvas fallback if the Three.js
 * renderer throws at any point (e.g. shader compile failure, context lost
 * during init, chunk load error).
 */
import { Component, type ReactNode } from "react";

class ThreeErrorBoundary extends Component<
  { fallback: ReactNode; onError?: () => void; children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch() {
    this.props.onError?.();
  }
  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

type Mode = "detecting" | "webgl" | "canvas";

/**
 * HeroRenderer — production architecture.
 *
 *   HeroRenderer
 *     ├── WebGLSupportDetector  (detectWebGLSupport)
 *     ├── ThreeParticleHead     (lazy, primary)
 *     └── CanvasParticleHead    (graceful degradation)
 *
 * Flow:
 *   1. On mount, detect WebGL support on the client.
 *   2. If supported → mount lazy Three.js renderer inside Suspense +
 *      ErrorBoundary. The Canvas renderer is the Suspense fallback so the
 *      user never sees a white screen while the Three chunk loads.
 *   3. If unsupported, or Three throws, or the WebGL context is lost at
 *      runtime → render CanvasParticleHead permanently for this session.
 */
export function HeroRenderer() {
  const [mode, setMode] = useState<Mode>("detecting");
  const wrapRef = useState<{ el: HTMLDivElement | null }>({ el: null })[0];

  useEffect(() => {
    setMode(detectWebGLSupport() ? "webgl" : "canvas");
  }, []);

  // Runtime health check: if the Three canvas doesn't produce any pixels
  // within ~2s (silent shader/postprocess failure, driver reset, etc.),
  // downgrade to the Canvas 2D renderer so the hero is never blank.
  useEffect(() => {
    if (mode !== "webgl") return;
    let cancelled = false;
    const check = () => {
      if (cancelled) return;
      const canvas = wrapRef.el?.querySelector("canvas") as HTMLCanvasElement | null;
      if (!canvas) return;
      const gl =
        (canvas.getContext("webgl2") as WebGL2RenderingContext | null) ||
        (canvas.getContext("webgl") as WebGLRenderingContext | null);
      if (!gl || gl.isContextLost()) {
        setMode("canvas");
        return;
      }
      const px = new Uint8Array(4);
      try {
        gl.readPixels(
          Math.floor(canvas.width / 2),
          Math.floor(canvas.height / 2),
          1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px,
        );
      } catch {
        setMode("canvas");
        return;
      }
      // Fully transparent means nothing was drawn.
      if (px[3] === 0 && px[0] === 0 && px[1] === 0 && px[2] === 0) {
        setMode("canvas");
      }
    };
    const t = window.setTimeout(check, 2000);
    return () => { cancelled = true; window.clearTimeout(t); };
  }, [mode, wrapRef]);

  if (mode === "canvas") return <CanvasParticleHead />;

  if (mode === "webgl") {
    return (
      <div ref={(el) => { wrapRef.el = el; }} className="h-full w-full">
        <ThreeErrorBoundary
          fallback={<CanvasParticleHead />}
          onError={() => setMode("canvas")}
        >
          <Suspense fallback={<CanvasParticleHead />}>
            <ThreeParticleHead onContextLost={() => setMode("canvas")} />
          </Suspense>
        </ThreeErrorBoundary>
      </div>
    );
  }

  // "detecting" — show canvas fallback so there's no blank frame pre-hydration.
  return <CanvasParticleHead />;
}

