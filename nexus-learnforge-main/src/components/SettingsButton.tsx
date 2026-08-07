import { useEffect, useState } from "react";
import { Settings2 } from "lucide-react";
import { getApiBase, setApiBase } from "@/api";

/** Small floating gear that lets the user override the FastAPI base URL. */
export function SettingsButton() {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");

  useEffect(() => {
    setUrl(getApiBase());
  }, [open]);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-50 grid h-11 w-11 place-items-center rounded-full glass-strong text-primary transition hover:scale-105 hover:glow-cyan"
        aria-label="API settings"
      >
        <Settings2 className="h-5 w-5" />
      </button>
      {open && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-background/70 p-4 backdrop-blur"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-2xl glass-strong p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold">Backend connection</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              URL of your NEXUS EDU FastAPI server. Make sure CORS allows this origin.
            </p>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="mt-4 w-full rounded-lg border border-border/60 bg-input/40 px-3 py-2 text-sm outline-none focus:border-primary"
              placeholder="http://localhost:8000"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setApiBase(url);
                  setOpen(false);
                  window.location.reload();
                }}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground glow-cyan"
              >
                Save & reload
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
