import { useEffect, useRef } from "react";

/**
 * Canvas-2D structured human face — a rotating 3D wireframe head built from
 * anatomically-placed feature curves (skull, jaw, brow, eye sockets, nose
 * ridge, lips) plus a supporting particle cloud. Projected each frame to 2D.
 */

type Pt = { x: number; y: number; z: number };
type Curve = { pts: Pt[]; hue: number; weight: number; glow: number };

// ---- Head surface: ellipsoid + nose ridge + brow + jaw taper + cheeks
function surface(theta: number, phi: number): Pt {
  const rx = 0.95;
  const ry = 1.32;
  const rz = 1.02;
  const sx = Math.sin(phi) * Math.cos(theta);
  const sy = Math.cos(phi);
  const sz = Math.sin(phi) * Math.sin(theta);
  const facing = Math.max(0, sx);

  // Nose ridge — narrow band, protrudes forward
  const noseBand = Math.exp(-Math.pow((phi - Math.PI * 0.52) * 3.5, 2));
  const noseCenter = Math.exp(-Math.pow(sz * 6.0, 2));
  const nose = facing * noseBand * noseCenter * 0.36;

  // Brow ridge — subtle protrusion above eyes
  const browBand = Math.exp(-Math.pow((phi - Math.PI * 0.4) * 5.5, 2));
  const brow = facing * browBand * 0.05;

  // Eye socket recess
  const eyeBand = Math.exp(-Math.pow((phi - Math.PI * 0.45) * 6.0, 2));
  const eyeSide = Math.exp(-Math.pow((Math.abs(sz) - 0.28) * 7.0, 2));
  const eye = -facing * eyeBand * eyeSide * 0.08;

  // Cheek fullness
  const cheekBand = Math.exp(-Math.pow((phi - Math.PI * 0.6) * 4.0, 2));
  const cheekSide = Math.exp(-Math.pow((Math.abs(sz) - 0.42) * 5.5, 2));
  const cheek = facing * cheekBand * cheekSide * 0.05;

  // Jaw taper — narrow at bottom
  const jawT = sy < -0.15 ? (sy + 0.15) : 0;
  const jaw = jawT * 0.22;

  // Chin
  const chinBand = Math.exp(-Math.pow((phi - Math.PI * 0.82) * 5.0, 2));
  const chin = facing * chinBand * Math.exp(-Math.pow(sz * 6.0, 2)) * 0.08;

  const r = 1.0;
  return {
    x: sx * (rx + nose + brow + eye + cheek + chin) * r,
    y: sy * (ry + jaw) * r,
    z: sz * (rz + (nose + cheek) * 0.6) * r,
  };
}

// ---- Feature curves that make it read as a FACE
function buildCurves(): Curve[] {
  const curves: Curve[] = [];
  const CY = 195; // cyan hue
  const PU = 275; // purple hue

  // Horizontal skull contour rings — top-down slices
  const ringPhis = [
    0.18, 0.26, 0.34, 0.40, 0.45, 0.50, 0.55, 0.60,
    0.66, 0.72, 0.78, 0.84, 0.90,
  ];
  for (const pf of ringPhis) {
    const phi = pf * Math.PI;
    const pts: Pt[] = [];
    const segs = 96;
    for (let s = 0; s <= segs; s++) {
      const theta = (s / segs) * Math.PI * 2;
      pts.push(surface(theta, phi));
    }
    curves.push({ pts, hue: CY, weight: 0.8, glow: 0.55 });
  }

  // Vertical meridians — from crown to chin, wrapping face
  const meridianThetas = [
    -0.55, -0.35, -0.18, 0.0, 0.18, 0.35, 0.55,
    Math.PI - 0.35, Math.PI, Math.PI + 0.35,
  ];
  for (const th of meridianThetas) {
    const pts: Pt[] = [];
    const segs = 80;
    for (let s = 0; s <= segs; s++) {
      const phi = (s / segs) * Math.PI;
      pts.push(surface(th, phi));
    }
    const front = Math.abs(Math.cos(th)) > 0.7;
    curves.push({
      pts,
      hue: front ? CY : PU,
      weight: front ? 0.9 : 0.6,
      glow: front ? 0.65 : 0.4,
    });
  }

  // Eye sockets (two ellipses)
  for (const side of [-1, 1]) {
    const pts: Pt[] = [];
    const segs = 48;
    const cx = 0.32; // forward
    const cy = 0.15; // slightly above center
    const cz = side * 0.32; // left/right
    const ex = 0.06; // eye width along x (depth)
    const ey = 0.09; // vertical radius
    const ez = 0.14; // horizontal radius across face
    for (let s = 0; s <= segs; s++) {
      const a = (s / segs) * Math.PI * 2;
      pts.push({
        x: cx + ex * Math.cos(a) * 0.3,
        y: cy + ey * Math.sin(a),
        z: cz + ez * Math.cos(a),
      });
    }
    curves.push({ pts, hue: CY, weight: 1.2, glow: 1.0 });
  }

  // Eye pupils (small dots as tiny curves)
  for (const side of [-1, 1]) {
    const pts: Pt[] = [];
    const segs = 20;
    const cx = 0.38;
    const cy = 0.14;
    const cz = side * 0.32;
    for (let s = 0; s <= segs; s++) {
      const a = (s / segs) * Math.PI * 2;
      pts.push({
        x: cx,
        y: cy + 0.025 * Math.sin(a),
        z: cz + 0.025 * Math.cos(a),
      });
    }
    curves.push({ pts, hue: 190, weight: 1.6, glow: 1.4 });
  }

  // Nose ridge — vertical line down the front
  {
    const pts: Pt[] = [];
    const segs = 40;
    for (let s = 0; s <= segs; s++) {
      const t = s / segs;
      const y = 0.22 - t * 0.5;
      const noseOut = Math.sin(t * Math.PI) * 0.14;
      pts.push({ x: 0.95 + noseOut, y, z: 0 });
    }
    curves.push({ pts, hue: CY, weight: 1.1, glow: 0.9 });
  }

  // Nostrils base — small arc
  {
    const pts: Pt[] = [];
    const segs = 24;
    for (let s = 0; s <= segs; s++) {
      const a = (s / segs) * Math.PI;
      pts.push({
        x: 1.02 - Math.sin(a) * 0.05,
        y: -0.28,
        z: Math.cos(a) * 0.09,
      });
    }
    curves.push({ pts, hue: CY, weight: 0.9, glow: 0.7 });
  }

  // Mouth — upper and lower lip curves
  for (const yOff of [-0.5, -0.56]) {
    const pts: Pt[] = [];
    const segs = 36;
    for (let s = 0; s <= segs; s++) {
      const t = s / segs;
      const a = (t - 0.5) * Math.PI * 0.8;
      const bow = yOff === -0.5 ? Math.cos(a * 2) * 0.02 : -Math.cos(a * 2) * 0.015;
      pts.push({
        x: 0.88 - Math.abs(a) * 0.05,
        y: yOff + bow,
        z: Math.sin(a) * 0.22,
      });
    }
    curves.push({ pts, hue: 205, weight: 1.0, glow: 0.85 });
  }

  // Jawline — from ear to chin to ear
  {
    const pts: Pt[] = [];
    const segs = 60;
    for (let s = 0; s <= segs; s++) {
      const t = (s / segs) * 2 - 1; // -1..1
      const a = t * Math.PI * 0.55;
      const y = -0.55 - Math.cos(a) * 0.55;
      pts.push({
        x: 0.15 + Math.cos(a) * 0.85,
        y,
        z: Math.sin(a) * 0.95,
      });
    }
    curves.push({ pts, hue: PU, weight: 1.0, glow: 0.75 });
  }

  // Cheekbone arcs
  for (const side of [-1, 1]) {
    const pts: Pt[] = [];
    const segs = 30;
    for (let s = 0; s <= segs; s++) {
      const t = s / segs;
      const a = t * Math.PI * 0.7 - Math.PI * 0.35;
      pts.push({
        x: 0.75 - Math.abs(a) * 0.1,
        y: -0.05 + Math.sin(a) * 0.05,
        z: side * (0.35 + Math.cos(a) * 0.15),
      });
    }
    curves.push({ pts, hue: CY, weight: 0.7, glow: 0.5 });
  }

  return curves;
}

// Sampling supporting particle cloud on the surface
function buildCloud(n: number): Pt[] {
  const pts: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(1 - 2 * Math.random());
    const p = surface(theta, phi);
    // slight outward jitter
    const j = 1 + (Math.random() - 0.5) * 0.02;
    pts.push({ x: p.x * j, y: p.y * j, z: p.z * j });
  }
  return pts;
}

export function ParticleHead2D() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const curves = buildCurves();
    const cloud = buildCloud(1800);
    let raf = 0;
    let running = true;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = parent.clientWidth;
      const h = parent.clientHeight;
      canvas.width = Math.max(1, Math.floor(w * dpr));
      canvas.height = Math.max(1, Math.floor(h * dpr));
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    if (canvas.parentElement) ro.observe(canvas.parentElement);

    const onMove = (e: PointerEvent) => {
      const r = canvas.getBoundingClientRect();
      mouseRef.current.x = (e.clientX - r.left) / r.width - 0.5;
      mouseRef.current.y = (e.clientY - r.top) / r.height - 0.5;
    };
    window.addEventListener("pointermove", onMove);

    const project = (p: Pt, cosY: number, sinY: number, cosX: number, sinX: number,
                     cx: number, cy: number, scale: number, focal: number) => {
      const x1 = p.x * cosY + p.z * sinY;
      const z1 = -p.x * sinY + p.z * cosY;
      const y2 = p.y * cosX - z1 * sinX;
      const z2 = p.y * sinX + z1 * cosX;
      const pz = focal / (focal + z2);
      return { x: cx + x1 * scale * pz, y: cy + y2 * scale * pz, z: z2, s: pz };
    };

    const draw = (t: number) => {
      if (!running) return;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;

      // Fade trail — subtle motion smear
      ctx.fillStyle = "rgba(8, 10, 22, 0.35)";
      ctx.fillRect(0, 0, w, h);

      const time = t * 0.001;
      // Slow oscillating rotation instead of full spin — reads as face
      const baseY = Math.sin(time * 0.35) * 0.9 + mouseRef.current.x * 0.6;
      const baseX = Math.sin(time * 0.5) * 0.08 + mouseRef.current.y * -0.4;

      const cosY = Math.cos(baseY);
      const sinY = Math.sin(baseY);
      const cosX = Math.cos(baseX);
      const sinX = Math.sin(baseX);

      const cx = w / 2;
      const cy = h / 2;
      const scale = Math.min(w, h) * 0.3;
      const focal = 3.4;

      // ---- Particle cloud (background depth)
      ctx.globalCompositeOperation = "lighter";
      for (let i = 0; i < cloud.length; i++) {
        const pr = project(cloud[i], cosY, sinY, cosX, sinX, cx, cy, scale, focal);
        const depth = (pr.z + 1.5) / 3;
        const alpha = 0.12 + Math.max(0, Math.min(1, depth)) * 0.28;
        const hue = 200 + (1 - depth) * 70;
        ctx.fillStyle = `hsla(${hue}, 90%, 65%, ${alpha})`;
        ctx.beginPath();
        ctx.arc(pr.x, pr.y, 0.7 * pr.s, 0, Math.PI * 2);
        ctx.fill();
      }

      // ---- Feature curves (the face structure)
      for (const c of curves) {
        const proj = c.pts.map((p) =>
          project(p, cosY, sinY, cosX, sinX, cx, cy, scale, focal)
        );
        // average depth for visibility fade
        let avgZ = 0;
        for (const p of proj) avgZ += p.z;
        avgZ /= proj.length;
        // Hide back-facing curves smoothly
        const facing = Math.max(0, Math.min(1, (0.6 - avgZ) / 1.2));
        if (facing < 0.05) continue;

        const alpha = (0.35 + facing * 0.55) * c.glow;
        ctx.strokeStyle = `hsla(${c.hue}, 95%, 68%, ${alpha})`;
        ctx.lineWidth = c.weight * (0.8 + facing * 0.6);
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        for (let i = 0; i < proj.length; i++) {
          const p = proj[i];
          if (i === 0) ctx.moveTo(p.x, p.y);
          else ctx.lineTo(p.x, p.y);
        }
        ctx.stroke();

        // Bright vertex dots on prominent curves
        if (c.glow > 0.7) {
          for (let i = 0; i < proj.length; i += 3) {
            const p = proj[i];
            ctx.fillStyle = `hsla(${c.hue}, 100%, 78%, ${alpha * 0.9})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 0.9 * p.s, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }

      ctx.globalCompositeOperation = "source-over";
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("pointermove", onMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="block h-full w-full"
      aria-hidden
    />
  );
}
