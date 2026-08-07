/**
 * WebGL support detection.
 * Returns true if a WebGL2 or WebGL1 context can be created.
 * SSR-safe: returns false on the server so we defer detection to the client.
 */
export function detectWebGLSupport(): boolean {
  if (typeof window === "undefined" || typeof document === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    const gl =
      (canvas.getContext("webgl2") as WebGL2RenderingContext | null) ||
      (canvas.getContext("webgl") as WebGLRenderingContext | null) ||
      (canvas.getContext("experimental-webgl") as WebGLRenderingContext | null);
    if (!gl) return false;
    // Some environments return a context that immediately reports lost.
    const lostExt = gl.getExtension("WEBGL_lose_context");
    if (lostExt && typeof (gl as WebGLRenderingContext).isContextLost === "function") {
      if ((gl as WebGLRenderingContext).isContextLost()) return false;
    }
    return true;
  } catch {
    return false;
  }
}
