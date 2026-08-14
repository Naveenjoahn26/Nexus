/**
 * Netlify Serverless Function v2 — SSR handler for TanStack Start.
 *
 * The Vite build produces a server handler at dist/server/server.js that uses
 * the Web standard fetch API (Request → Response). Netlify Functions v2 also
 * use this same interface, so we can delegate directly.
 *
 * IMPORTANT: This must be a Node.js Function (not an Edge Function) because
 * the TanStack Start server bundle uses `node:async_hooks` (AsyncLocalStorage)
 * which is NOT available in Deno/edge runtimes.
 *
 * For static assets (/assets/*, /favicon.ico), we call context.next() which
 * passes the request to Netlify's next handler — the CDN static file server.
 * This is the correct way to skip function handling for static files.
 */

import handler from "../../dist/server/server.js";

const STATIC_PATHS = ["/assets/", "/favicon.ico"];

export default async (request, context) => {
  const { pathname } = new URL(request.url);

  // For static assets, call context.next() to delegate to Netlify's CDN.
  // This works because context.next() goes to: force=true redirects (only
  // /api/* and /youtube/* — no match for assets) → static file server → served.
  // There is NO catch-all force=true redirect so no infinite loop.
  if (STATIC_PATHS.some((p) => pathname.startsWith(p) || pathname === p)) {
    return context.next();
  }

  try {
    return await handler.fetch(request, {}, context);
  } catch (err) {
    console.error("SSR function error:", err);
    return new Response("Internal Server Error", { status: 500 });
  }
};

// config.path routes all requests through this function.
// preferStatic: true means if a static file matches the path, serve that
// instead of invoking the function (belt-and-suspenders with context.next()).
export const config = {
  path: "/*",
  preferStatic: true,
};

