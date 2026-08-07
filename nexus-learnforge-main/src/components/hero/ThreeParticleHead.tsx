import { Canvas, useFrame, useThree } from "@react-three/fiber";

import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

/**
 * Premium React Three Fiber particle head.
 * Lazy-loaded and only mounted when WebGL is available.
 */

// ---------- sphere sampler (dense AI core, no face geometry) -----------
function spherePoint(out = new THREE.Vector3()) {
  const u = Math.random();
  const v = Math.random();
  const theta = 2 * Math.PI * u;
  const phi = Math.acos(2 * v - 1);
  const rad = Math.pow(Math.random(), 0.5) * 1.0;
  out.set(
    rad * Math.sin(phi) * Math.cos(theta),
    rad * Math.sin(phi) * Math.sin(theta),
    rad * Math.cos(phi),
  );
  return out;
}

function useHeadTransform() {
  const ref = useRef<THREE.Group>(null!);
  const mouse = useRef({ x: 0, y: 0 });
  useFrame((state, delta) => {
    const t = state.clock.elapsedTime;
    if (!ref.current) return;
    ref.current.rotation.y += delta * 0.18;
    mouse.current.x += (state.pointer.x - mouse.current.x) * 0.05;
    mouse.current.y += (state.pointer.y - mouse.current.y) * 0.05;
    ref.current.rotation.x = mouse.current.y * -0.3;
    const s = 1 + Math.sin(t * 1.1) * 0.035;
    ref.current.scale.setScalar(s);
    ref.current.position.y = Math.sin(t * 0.6) * 0.06;
  });
  return ref;
}

function HeadParticles({ count = 40000 }: { count?: number }) {
  const points = useRef<THREE.Points>(null!);
  const mat = useRef<THREE.ShaderMaterial>(null!);

  const { positions, sizes, seeds } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const seeds = new Float32Array(count);
    const v = new THREE.Vector3();
    for (let i = 0; i < count; i++) {
      spherePoint(v);
      positions.set([v.x, v.y, v.z], i * 3);
      sizes[i] = Math.random() * 1.6 + 0.4;
      seeds[i] = Math.random();
    }
    return { positions, sizes, seeds };
  }, [count]);

  useFrame((state) => {
    if (mat.current) mat.current.uniforms.uTime.value = state.clock.elapsedTime;
  });

  return (
    <points ref={points} frustumCulled={false}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-aSize" args={[sizes, 1]} />
        <bufferAttribute attach="attributes-aSeed" args={[seeds, 1]} />
      </bufferGeometry>
      <shaderMaterial
        ref={mat}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        uniforms={{ uTime: { value: 0 } }}
        vertexShader={`
          attribute float aSize;
          attribute float aSeed;
          uniform float uTime;
          varying float vGlow;
          varying float vY;
          void main() {
            vec3 p = position;
            float n = sin(p.y * 3.0 + uTime * 1.2 + aSeed * 6.283)
                    + cos(p.x * 3.5 + uTime * 0.9)
                    + sin((p.x + p.z) * 4.0 + uTime * 1.6);
            p += normalize(p + 0.0001) * n * 0.018;
            float pulse = smoothstep(0.02, 0.0, abs(p.y - sin(uTime * 0.6) * 1.4));
            vGlow = pulse + 0.5 + 0.5 * sin(uTime * 2.0 + aSeed * 10.0);
            vY = p.y;
            vec4 mv = modelViewMatrix * vec4(p, 1.0);
            gl_PointSize = aSize * (260.0 / -mv.z) * (0.8 + pulse * 1.5);
            gl_Position = projectionMatrix * mv;
          }
        `}
        fragmentShader={`
          varying float vGlow;
          varying float vY;
          void main() {
            vec2 uv = gl_PointCoord - 0.5;
            float d = length(uv);
            if (d > 0.5) discard;
            float a = smoothstep(0.5, 0.0, d);
            vec3 cyan = vec3(0.22, 0.88, 1.0);
            vec3 purple = vec3(0.69, 0.42, 1.0);
            vec3 col = mix(cyan, purple, smoothstep(-1.5, 1.5, vY));
            col += vec3(0.4, 0.3, 0.6) * vGlow * 0.5;
            gl_FragColor = vec4(col, a);
          }
        `}
      />
    </points>
  );
}

function NeuralNet({ nodes = 80 }: { nodes?: number }) {
  const matRef = useRef<THREE.ShaderMaterial>(null!);

  const { positions } = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    const v = new THREE.Vector3();
    for (let i = 0; i < nodes; i++) {
      // nodes sit on a slightly puffed shell around the core
      spherePoint(v);
      const n = v.clone().normalize().multiplyScalar(1.05 + Math.random() * 0.12);
      pts.push(n);
    }
    const pairs: [number, number][] = [];
    for (let i = 0; i < pts.length; i++) {
      const dists = pts.map((p, j) => ({ j, d: p.distanceTo(pts[i]) }));
      dists.sort((a, b) => a.d - b.d);
      pairs.push([i, dists[1].j], [i, dists[2].j]);
    }
    const positions = new Float32Array(pairs.length * 6);
    pairs.forEach(([a, b], k) => {
      positions.set([pts[a].x, pts[a].y, pts[a].z, pts[b].x, pts[b].y, pts[b].z], k * 6);
    });
    return { positions };
  }, [nodes]);

  useFrame((state) => {
    if (matRef.current) matRef.current.uniforms.uTime.value = state.clock.elapsedTime;
  });

  return (
    <lineSegments>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <shaderMaterial
        ref={matRef}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        uniforms={{ uTime: { value: 0 } }}
        vertexShader={`
          uniform float uTime;
          varying float vP;
          void main() {
            vP = 0.5 + 0.5 * sin(uTime * 2.0 + position.y * 4.0 + position.x * 3.0);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `}
        fragmentShader={`
          varying float vP;
          void main() {
            vec3 col = mix(vec3(0.22, 0.88, 1.0), vec3(0.69, 0.42, 1.0), vP);
            gl_FragColor = vec4(col, 0.35 + vP * 0.35);
          }
        `}
      />
    </lineSegments>
  );
}

function Sparks({ count = 400 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null!);
  const { positions, phases } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const phases = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      const r = 1.8 + Math.random() * 1.2;
      const th = Math.random() * Math.PI * 2;
      const ph = Math.acos(1 - 2 * Math.random());
      positions[i * 3] = r * Math.sin(ph) * Math.cos(th);
      positions[i * 3 + 1] = r * Math.cos(ph);
      positions[i * 3 + 2] = r * Math.sin(ph) * Math.sin(th);
      phases[i] = Math.random() * 6.283;
    }
    return { positions, phases };
  }, [count]);
  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.1;
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.15;
    }
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-aPhase" args={[phases, 1]} />
      </bufferGeometry>
      <shaderMaterial
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        uniforms={{ uTime: { value: 0 } }}
        vertexShader={`
          attribute float aPhase;
          uniform float uTime;
          varying float vT;
          void main() {
            vT = 0.5 + 0.5 * sin(uTime * 3.0 + aPhase);
            vec4 mv = modelViewMatrix * vec4(position, 1.0);
            gl_PointSize = (1.5 + vT * 3.0) * (200.0 / -mv.z);
            gl_Position = projectionMatrix * mv;
          }
        `}
        fragmentShader={`
          varying float vT;
          void main() {
            vec2 uv = gl_PointCoord - 0.5;
            float d = length(uv);
            if (d > 0.5) discard;
            float a = smoothstep(0.5, 0.0, d) * vT;
            vec3 col = mix(vec3(0.22, 0.88, 1.0), vec3(1.0, 0.6, 0.9), vT);
            gl_FragColor = vec4(col, a);
          }
        `}
      />
    </points>
  );
}

function CursorLight() {
  const ref = useRef<THREE.PointLight>(null!);
  useFrame((state) => {
    if (!ref.current) return;
    const target = new THREE.Vector3(state.pointer.x * 3, state.pointer.y * 2, 3);
    ref.current.position.lerp(target, 0.08);
  });
  return <pointLight ref={ref} intensity={3} distance={10} color="#b06bff" />;
}

function CameraRig() {
  const { camera } = useThree();
  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const px = state.pointer.x * 0.4 + Math.sin(t * 0.2) * 0.15;
    const py = state.pointer.y * 0.25 + Math.cos(t * 0.15) * 0.1;
    camera.position.x += (px - camera.position.x) * 0.03;
    camera.position.y += (py - camera.position.y) * 0.03;
    camera.lookAt(0, 0, 0);
  });
  return null;
}

function Scene({ particleCount }: { particleCount: number }) {
  const head = useHeadTransform();
  return (
    <>
      <fog attach="fog" args={["#0a0c18", 6, 14]} />
      <ambientLight intensity={0.35} />
      <directionalLight position={[4, 6, 5]} intensity={1.2} color="#7dd3fc" />
      <pointLight position={[-4, -2, 3]} intensity={2} color="#b06bff" />
      <CursorLight />
      <CameraRig />
      <group ref={head}>
        <HeadParticles count={particleCount} />
        
        <NeuralNet nodes={70} />
      </group>
      <Sparks count={350} />
    </>
  );
}


function useParticleBudget() {
  const [count, setCount] = useState(40000);
  useEffect(() => {
    const w = window.innerWidth;
    if (w < 640) setCount(15000);
    else if (w < 1024) setCount(25000);
    else setCount(45000);
  }, []);
  return count;
}

interface ThreeParticleHeadProps {
  onContextLost?: () => void;
}

/**
 * Primary premium renderer. Default export so it can be React.lazy()'d
 * and only loaded when WebGL is confirmed available.
 */
export default function ThreeParticleHead({ onContextLost }: ThreeParticleHeadProps) {
  const particleCount = useParticleBudget();
  return (
    <Canvas
      dpr={[1, 2]}
      camera={{ position: [0, 0, 5], fov: 45 }}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      onCreated={({ gl }) => {
        gl.setClearColor(0x000000, 0);
        gl.domElement.addEventListener("webglcontextlost", (e) => {
          e.preventDefault();
          onContextLost?.();
        });
      }}
      style={{ width: "100%", height: "100%" }}
    >
      <Scene particleCount={particleCount} />
    </Canvas>
  );
}

