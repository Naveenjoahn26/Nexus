import { useEffect, useRef } from "react";

/**
 * Premium Canvas-2D fallback: dense glowing particle sphere with neural
 * connections, drifting dust, breathing scale, slow rotation, and mouse
 * parallax. Cinematic AI consciousness feel.
 */
export function CanvasParticleHead() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let W = 0, H = 0;
    const DPR = Math.min(window.devicePixelRatio || 1, 2);
    const resize = () => {
      const r = wrap.getBoundingClientRect();
      W = Math.max(320, r.width);
      H = Math.max(320, r.height);
      canvas.width = Math.floor(W * DPR);
      canvas.height = Math.floor(H * DPR);
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(wrap);

    type P = { x: number; y: number; z: number; r: number; seed: number; hue: number };
    const core: P[] = [];
    // Surface shell — most particles
    for (let i = 0; i < 1200; i++) {
      const u = Math.random(), v = Math.random();
      const th = 2 * Math.PI * u;
      const ph = Math.acos(2 * v - 1);
      const rad = 0.85 + Math.random() * 0.15;
      core.push({
        x: rad * Math.sin(ph) * Math.cos(th),
        y: rad * Math.sin(ph) * Math.sin(th),
        z: rad * Math.cos(ph),
        r: 1.2 + Math.random() * 1.6,
        seed: Math.random() * Math.PI * 2,
        hue: 180 + Math.random() * 90,
      });
    }
    // Inner scatter
    for (let i = 0; i < 500; i++) {
      const u = Math.random(), v = Math.random();
      const th = 2 * Math.PI * u;
      const ph = Math.acos(2 * v - 1);
      const rad = Math.random() * 0.75;
      core.push({
        x: rad * Math.sin(ph) * Math.cos(th),
        y: rad * Math.sin(ph) * Math.sin(th),
        z: rad * Math.cos(ph),
        r: 0.8 + Math.random() * 1.2,
        seed: Math.random() * Math.PI * 2,
        hue: 195 + Math.random() * 80,
      });
    }

    // Neural nodes
    const nodes: P[] = [];
    for (let i = 0; i < 22; i++) {
      const u = Math.random(), v = Math.random();
      const th = 2 * Math.PI * u;
      const ph = Math.acos(2 * v - 1);
      nodes.push({
        x: Math.sin(ph) * Math.cos(th),
        y: Math.sin(ph) * Math.sin(th),
        z: Math.cos(ph),
        r: 3,
        seed: Math.random() * Math.PI * 2,
        hue: 200 + Math.random() * 70,
      });
    }
    const conns: [number, number][] = [];
    for (let i = 0; i < nodes.length; i++) {
      const d = nodes
        .map((n, j) => ({ j, d: (n.x - nodes[i].x) ** 2 + (n.y - nodes[i].y) ** 2 + (n.z - nodes[i].z) ** 2 }))
        .sort((a, b) => a.d - b.d);
      if (d[1]?.d < 1.1) conns.push([i, d[1].j]);
    }

    // Floating dust around sphere
    const dust: { x: number; y: number; z: number; r: number; vx: number; vy: number; seed: number; hue: number }[] = [];
    for (let i = 0; i < 90; i++) {
      const rd = 1.35 + Math.random() * 1.2;
      const th = Math.random() * Math.PI * 2;
      const ph = Math.acos(2 * Math.random() - 1);
      dust.push({
        x: rd * Math.sin(ph) * Math.cos(th),
        y: rd * Math.sin(ph) * Math.sin(th),
        z: rd * Math.cos(ph),
        r: 0.8 + Math.random() * 1.2,
        vx: (Math.random() - 0.5) * 0.001,
        vy: (Math.random() - 0.5) * 0.001,
        seed: Math.random() * Math.PI * 2,
        hue: 200 + Math.random() * 70,
      });
    }

    const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
    const onMove = (e: MouseEvent) => {
      const r = wrap.getBoundingClientRect();
      mouse.tx = ((e.clientX - r.left) / r.width - 0.5) * 2;
      mouse.ty = ((e.clientY - r.top) / r.height - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMove);

    const project = (x: number, y: number, z: number, cx: number, cy: number, s: number) => {
      const persp = 2.6 / (2.6 - z);
      return { sx: cx + x * s * persp, sy: cy + y * s * persp, depth: z, persp };
    };

    let raf = 0;
    const t0 = performance.now();

    const draw = () => {
      const t = (performance.now() - t0) / 1000;

      mouse.x += (mouse.tx - mouse.x) * 0.06;
      mouse.y += (mouse.ty - mouse.y) * 0.06;

      ctx.globalCompositeOperation = "source-over";
      ctx.clearRect(0, 0, W, H);

      const cx = W / 2 + mouse.x * 22;
      const cy = H / 2 + mouse.y * 16;
      const breath = 1 + Math.sin(t * 1.0) * 0.04;
      const baseScale = Math.min(W, H) * 0.32 * breath;

      const ry = t * 0.28 + mouse.x * 0.5;
      const rx = Math.sin(t * 0.35) * 0.18 + mouse.y * -0.4;
      const cY = Math.cos(ry), sY = Math.sin(ry);
      const cX = Math.cos(rx), sX = Math.sin(rx);
      const rot = (p: { x: number; y: number; z: number }) => {
        const x = p.x * cY + p.z * sY;
        const z = -p.x * sY + p.z * cY;
        const y2 = p.y * cX - z * sX;
        const z2 = p.y * sX + z * cX;
        return { x, y: y2, z: z2 };
      };

      // === Additive layer (glows, halo, particles) ===
      ctx.globalCompositeOperation = "lighter";

      // Soft halo behind — dimmed
      const halo = ctx.createRadialGradient(cx, cy, baseScale * 0.4, cx, cy, baseScale * 2.2);
      halo.addColorStop(0, "rgba(90, 170, 210, 0.14)");
      halo.addColorStop(0.5, "rgba(120, 90, 190, 0.09)");
      halo.addColorStop(1, "rgba(10, 12, 24, 0)");
      ctx.fillStyle = halo;
      ctx.beginPath();
      ctx.arc(cx, cy, baseScale * 2.2, 0, Math.PI * 2);
      ctx.fill();

      // Dust — softer
      for (const d of dust) {
        d.x += d.vx;
        d.y += d.vy;
        const rp = rot(d);
        const pr = project(rp.x, rp.y, rp.z, cx, cy, baseScale);
        const twk = 0.6 + 0.4 * Math.sin(t * 2.3 + d.seed);
        const size = d.r * pr.persp * 1.3 * twk;
        ctx.fillStyle = `hsla(${d.hue}, 55%, 68%, ${0.45 * twk})`;
        ctx.beginPath();
        ctx.arc(pr.sx, pr.sy, size, 0, Math.PI * 2);
        ctx.fill();
      }

      // Core particles — depth-sorted, muted
      const rendered = core.map((p) => {
        const rp = rot(p);
        return { ...project(rp.x, rp.y, rp.z, cx, cy, baseScale), p };
      });
      rendered.sort((a, b) => a.depth - b.depth);

      for (const r of rendered) {
        const df = (r.depth + 1) * 0.5;
        const twk = 0.75 + 0.25 * Math.sin(t * 2.0 + r.p.seed);
        const size = Math.max(1.1, r.p.r * r.persp * (1.1 + twk * 0.4));
        const alpha = (0.28 + df * 0.4) * twk;
        // outer glow — dimmed
        const g = ctx.createRadialGradient(r.sx, r.sy, 0, r.sx, r.sy, size * 4);
        g.addColorStop(0, `hsla(${r.p.hue}, 60%, 62%, ${Math.min(1, alpha * 0.7)})`);
        g.addColorStop(1, `hsla(${r.p.hue}, 60%, 45%, 0)`);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(r.sx, r.sy, size * 4, 0, Math.PI * 2);
        ctx.fill();
        // softer core — no more hot white
        ctx.fillStyle = `hsla(${r.p.hue}, 55%, 78%, ${Math.min(0.85, alpha * 1.1)})`;
        ctx.beginPath();
        ctx.arc(r.sx, r.sy, size * 1.05, 0, Math.PI * 2);
        ctx.fill();
      }

      // Neural connections — dimmed
      const pn = nodes.map((n) => {
        const rp = rot(n);
        return { ...project(rp.x, rp.y, rp.z, cx, cy, baseScale), node: n };
      });
      ctx.lineWidth = 1.1;
      for (const [i, j] of conns) {
        const a = pn[i], b = pn[j];
        const pulse = 0.45 + 0.45 * Math.sin(t * 1.5 + i * 0.4);
        const alpha = 0.18 * pulse;
        const gr = ctx.createLinearGradient(a.sx, a.sy, b.sx, b.sy);
        gr.addColorStop(0, `hsla(195, 55%, 65%, ${alpha})`);
        gr.addColorStop(1, `hsla(275, 55%, 65%, ${alpha})`);
        ctx.strokeStyle = gr;
        ctx.beginPath();
        ctx.moveTo(a.sx, a.sy);
        ctx.lineTo(b.sx, b.sy);
        ctx.stroke();
      }
      // Neural node dots — dimmed
      for (const n of pn) {
        const pulse = 0.65 + 0.35 * Math.sin(t * 1.9 + n.node.seed);
        const size = n.node.r * n.persp * (1 + pulse * 0.3);
        const g = ctx.createRadialGradient(n.sx, n.sy, 0, n.sx, n.sy, size * 4);
        g.addColorStop(0, `hsla(${n.node.hue}, 55%, 68%, ${0.5 * pulse})`);
        g.addColorStop(1, `hsla(${n.node.hue}, 55%, 50%, 0)`);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(n.sx, n.sy, size * 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `hsla(200, 30%, 88%, ${Math.min(0.75, pulse * 0.75)})`;
        ctx.beginPath();
        ctx.arc(n.sx, n.sy, size * 0.7, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <div
      ref={wrapRef}
      className="relative h-full w-full"
      style={{
        WebkitMaskImage:
          "radial-gradient(ellipse at center, #000 55%, rgba(0,0,0,0.6) 78%, transparent 100%)",
        maskImage:
          "radial-gradient(ellipse at center, #000 55%, rgba(0,0,0,0.6) 78%, transparent 100%)",
      }}
    >
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
    </div>
  );
}
