import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileText, Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { upload as uploadApi } from "@/api";

export const Route = createFileRoute("/_authenticated/documents")({
  component: DocumentsPage,
  head: () => ({
    meta: [
      { title: "Documents · NEXUS EDU" },
      { name: "description", content: "Upload course documents into the RAG pipeline." },
      { property: "og:title", content: "Documents · NEXUS EDU" },
      { property: "og:description", content: "Upload course documents into the RAG pipeline." },
    ],
  }),
});

function DocumentsPage() {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploaded, setUploaded] = useState<Array<{ id: string; filename: string; chunks?: number }>>([]);

  // Note: the FRD lists /documents/upload and DELETE /documents/{id} but no list
  // endpoint. We keep an ephemeral in-page list of the docs the user just added.
  useQuery({ queryKey: ["docs-noop"], queryFn: async () => null, staleTime: Infinity });

  const upload = useMutation({
    mutationFn: (f: File) => uploadApi.uploadFile(f),
    onSuccess: (d) => {
      setUploaded((u) => [{ id: d.id, filename: d.filename, chunks: d.chunks }, ...u]);
      toast.success(`Indexed: ${d.filename}`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => uploadApi.removeFile(id),
    onSuccess: (_r, id) => {
      setUploaded((u) => u.filter((d) => d.id !== id));
      qc.invalidateQueries({ queryKey: ["docs-noop"] });
      toast.success("Removed.");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const onFiles = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((f) => upload.mutate(f));
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Documents</h1>
        <p className="mt-1 text-muted-foreground">
          Feed the RAG pipeline: PDFs, Word, PowerPoint, Markdown, and text.
        </p>
      </header>

      <motion.div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          onFiles(e.dataTransfer.files);
        }}
        animate={{ scale: dragOver ? 1.01 : 1 }}
        className={`glass-strong grid cursor-pointer place-items-center rounded-2xl border-2 border-dashed p-14 text-center transition ${
          dragOver ? "border-primary bg-primary/10" : "border-white/10"
        }`}
        onClick={() => inputRef.current?.click()}
      >
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-primary to-secondary glow-cyan animate-float-slow">
          <UploadCloud className="h-6 w-6 text-primary-foreground" />
        </div>
        <p className="mt-4 font-medium">Drop files here or click to browse</p>
        <p className="mt-1 text-xs text-muted-foreground">PDF · DOCX · PPTX · TXT · MD — up to 20 MB each</p>
        <input
          ref={inputRef}
          type="file"
          hidden
          multiple
          accept=".pdf,.docx,.pptx,.txt,.md"
          onChange={(e) => onFiles(e.target.files)}
        />
      </motion.div>

      {upload.isPending && (
        <div className="glass flex items-center gap-2 rounded-xl px-4 py-3 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
          Chunking & embedding…
        </div>
      )}

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-widest text-muted-foreground">Recent uploads</h2>
        {uploaded.length === 0 ? (
          <div className="glass rounded-2xl p-6 text-sm text-muted-foreground">
            Uploads from this session will appear here.
          </div>
        ) : (
          <ul className="space-y-2">
            {uploaded.map((d) => (
              <motion.li
                key={d.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                className="glass flex items-center gap-3 rounded-xl px-4 py-3"
              >
                <FileText className="h-4 w-4 text-primary" />
                <div className="flex-1 truncate text-sm">{d.filename}</div>
                {d.chunks != null && (
                  <span className="text-xs text-muted-foreground">{d.chunks} chunks</span>
                )}
                <button
                  onClick={() => remove.mutate(d.id)}
                  className="rounded-lg p-2 text-muted-foreground hover:bg-white/5 hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </motion.li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
