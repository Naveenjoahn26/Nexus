import { defineMcp } from "@lovable.dev/mcp-js";
import echoTool from "./tools/echo";
import healthTool from "./tools/health";

/**
 * NEXUS EDU MCP server (PUBLIC — no authentication).
 *
 * ⚠️ This server is intentionally unauthenticated. Anyone on the internet who
 * has the URL can invoke these tools. Because of that, ONLY expose tools that
 * do not read or modify per-user data.
 *
 * NEXUS EDU's user data (courses, documents, chats, generations) lives behind
 * an external FastAPI backend that Lovable cannot verify OAuth tokens for, so
 * per-user MCP tools are not shipped. To expose them safely, either add an
 * OAuth 2.1 authorization server to the FastAPI backend and switch this
 * `defineMcp` to `auth.oauth.issuer({...})`, or migrate auth to Lovable Cloud
 * and use its managed OAuth server.
 */
export default defineMcp({
  name: "nexus-edu-mcp",
  title: "NEXUS EDU",
  version: "0.1.0",
  instructions:
    "Public utility tools for the NEXUS EDU project. Use `health` to check server status and `echo` to verify connectivity. No user data is exposed.",
  tools: [healthTool, echoTool],
});
