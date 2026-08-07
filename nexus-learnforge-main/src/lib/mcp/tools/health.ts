import { defineTool } from "@lovable.dev/mcp-js";
import { z } from "zod";

export default defineTool({
  name: "health",
  title: "Health check",
  description: "Return the NEXUS EDU MCP server status and version.",
  inputSchema: {},
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  handler: () => ({
    content: [
      {
        type: "text",
        text: JSON.stringify({ status: "ok", server: "nexus-edu-mcp", version: "0.1.0" }),
      },
    ],
    structuredContent: { status: "ok", server: "nexus-edu-mcp", version: "0.1.0" },
  }),
});
