import { useState, useRef, useCallback, useEffect } from "react";

// ═══════════════════════════════════════════════════════════════
// WINDI EVIDENCE UPLOADER v11.0 — Composer Evidence Module
// "A prova nasce íntegra na mão do humano."
// ═══════════════════════════════════════════════════════════════

const ACCEPTED_TYPES = {
  "image/png": { icon: "🖼", category: "IMG", maxMB: 25 },
  "image/jpeg": { icon: "🖼", category: "IMG", maxMB: 25 },
  "image/webp": { icon: "🖼", category: "IMG", maxMB: 25 },
  "image/gif": { icon: "🖼", category: "IMG", maxMB: 10 },
  "video/mp4": { icon: "🎬", category: "VID", maxMB: 500 },
  "video/webm": { icon: "🎬", category: "VID", maxMB: 500 },
  "audio/mpeg": { icon: "🔊", category: "AUD", maxMB: 100 },
  "audio/wav": { icon: "🔊", category: "AUD", maxMB: 100 },
  "audio/ogg": { icon: "🔊", category: "AUD", maxMB: 100 },
  "application/pdf": { icon: "📄", category: "DOC", maxMB: 50 },
};

const EVIDENCE_ROLES = [
  { value: "primary_evidence", label: "Primary Evidence", color: "#C9A84C" },
  { value: "supporting_evidence", label: "Supporting", color: "#6B8E6B" },
  { value: "context_material", label: "Context Material", color: "#7B8FA1" },
  { value: "reference_only", label: "Reference Only", color: "#999999" },
];

const VIDEO_THRESHOLD_MB = 50;

async function computeSHA256(file, onProgress) {
  const chunkSize = 2 * 1024 * 1024;
  const totalChunks = Math.ceil(file.size / chunkSize);

  if (file.size <= chunkSize) {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    onProgress?.(100);
    return [...new Uint8Array(hashBuffer)]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  // Chunked reading for large files — hash the full concatenated buffer
  const chunks = [];
  let offset = 0;
  let chunkIndex = 0;

  while (offset < file.size) {
    const slice = file.slice(offset, offset + chunkSize);
    const buffer = await slice.arrayBuffer();
    chunks.push(new Uint8Array(buffer));
    offset += chunkSize;
    chunkIndex++;
    onProgress?.(Math.round((chunkIndex / totalChunks) * 95));
  }

  const fullBuffer = new Uint8Array(
    chunks.reduce((acc, c) => acc + c.length, 0)
  );
  let pos = 0;
  for (const chunk of chunks) {
    fullBuffer.set(chunk, pos);
    pos += chunk.length;
  }

  const hashBuffer = await crypto.subtle.digest("SHA-256", fullBuffer.buffer);
  onProgress?.(100);
  return [...new Uint8Array(hashBuffer)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

function generateEvidenceId(category, existingFiles) {
  const count =
    existingFiles.filter((f) => f.category === category).length + 1;
  return `${category}-${String(count).padStart(2, "0")}`;
}

function EvidenceCard({ file, onRemove, onRoleChange }) {
  const isHashing = file.status === "hashing";
  const isReady = file.status === "ready";
  const isError = file.status === "error";
  const isPointer = file.transportMode === "pointer";

  return (
    <div
      style={{
        background: "var(--card)",
        border: `1px solid ${isError ? "#8B3A3A" : isReady ? "var(--gold-dim)" : "var(--border)"}`,
        borderRadius: 8,
        padding: 16,
        position: "relative",
        transition: "all 0.3s ease",
        opacity: isHashing ? 0.85 : 1,
      }}
    >
      {/* Header Row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>{file.icon}</span>
          <div>
            <div
              style={{
                fontFamily: "'Bricolage Grotesque', sans-serif",
                fontWeight: 600,
                fontSize: 14,
                color: "var(--gold)",
                letterSpacing: "0.5px",
              }}
            >
              {file.evidenceId}
            </div>
            <div
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontSize: 12,
                color: "var(--muted)",
                maxWidth: 180,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {file.name}
            </div>
          </div>
        </div>

        <button
          onClick={() => onRemove(file.id)}
          style={{
            background: "none",
            border: "none",
            color: "var(--muted)",
            cursor: "pointer",
            fontSize: 16,
            padding: 4,
            lineHeight: 1,
            borderRadius: 4,
          }}
          title="Remove evidence"
        >
          ✕
        </button>
      </div>

      {/* Preview */}
      {file.preview && (
        <div
          style={{
            marginBottom: 12,
            borderRadius: 6,
            overflow: "hidden",
            maxHeight: 120,
            background: "#0a0a0a",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <img
            src={file.preview}
            alt={file.name}
            style={{
              maxWidth: "100%",
              maxHeight: 120,
              objectFit: "contain",
            }}
          />
        </div>
      )}

      {/* Hash Progress */}
      {isHashing && (
        <div style={{ marginBottom: 12 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 4,
            }}
          >
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                color: "var(--gold)",
                letterSpacing: "1px",
                textTransform: "uppercase",
              }}
            >
              Computing SHA-256
            </span>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                color: "var(--muted)",
              }}
            >
              {file.hashProgress}%
            </span>
          </div>
          <div
            style={{
              height: 3,
              background: "var(--border)",
              borderRadius: 2,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${file.hashProgress}%`,
                background:
                  "linear-gradient(90deg, var(--gold-dim), var(--gold))",
                borderRadius: 2,
                transition: "width 0.2s ease",
              }}
            />
          </div>
        </div>
      )}

      {/* Hash Display */}
      {isReady && file.sha256 && (
        <div
          style={{
            background: "#0D0D0D",
            border: "1px solid var(--border)",
            borderRadius: 4,
            padding: "6px 8px",
            marginBottom: 12,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span style={{ color: "#4CAF50", fontSize: 12 }}>✓</span>
          <code
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 9.5,
              color: "var(--muted)",
              letterSpacing: "0.3px",
              wordBreak: "break-all",
              lineHeight: 1.4,
            }}
          >
            {file.sha256}
          </code>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div
          style={{
            background: "#1a0a0a",
            border: "1px solid #8B3A3A",
            borderRadius: 4,
            padding: "6px 8px",
            marginBottom: 12,
            fontFamily: "'Outfit', sans-serif",
            fontSize: 11,
            color: "#D45454",
          }}
        >
          {file.error}
        </div>
      )}

      {/* Metadata Row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: "var(--muted)",
            }}
          >
            {formatBytes(file.size)}
          </span>

          {isPointer && (
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9,
                color: "#7B8FA1",
                background: "#1a1f2a",
                padding: "2px 6px",
                borderRadius: 3,
                letterSpacing: "0.5px",
                textTransform: "uppercase",
              }}
            >
              Vault Pointer
            </span>
          )}

          {!isPointer && isReady && (
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9,
                color: "#6B8E6B",
                background: "#0a1a0a",
                padding: "2px 6px",
                borderRadius: 3,
                letterSpacing: "0.5px",
                textTransform: "uppercase",
              }}
            >
              Local Payload
            </span>
          )}
        </div>

        {/* Role Selector */}
        {isReady && (
          <select
            value={file.role}
            onChange={(e) => onRoleChange(file.id, e.target.value)}
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontSize: 11,
              background: "var(--surface)",
              color: EVIDENCE_ROLES.find((r) => r.value === file.role)?.color || "var(--text)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "3px 6px",
              cursor: "pointer",
              outline: "none",
            }}
          >
            {EVIDENCE_ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}

function ManifestPreview({ files }) {
  const readyFiles = files.filter((f) => f.status === "ready");
  if (readyFiles.length === 0) return null;

  const manifest = {
    schema: "evidence-manifest-v1.1",
    generated_at: new Date().toISOString(),
    evidence: {
      count: readyFiles.length,
      files: readyFiles.map((f) => ({
        id: f.evidenceId,
        filename: f.name,
        sha256: f.sha256,
        path: `evidence/${f.evidenceId}${f.name.substring(f.name.lastIndexOf("."))}`,
        role: f.role,
        bytes: f.size,
        mime: f.mime,
        transport: f.transportMode,
        ...(f.transportMode === "pointer"
          ? { storage: { type: "vault", hash_locator: `sha256:${f.sha256}`, retrieval_required: true } }
          : {}),
      })),
    },
  };

  return (
    <div
      style={{
        background: "#0D0D0D",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: 16,
        marginTop: 16,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 10,
        }}
      >
        <span
          style={{
            fontFamily: "'Bricolage Grotesque', sans-serif",
            fontSize: 13,
            fontWeight: 600,
            color: "var(--gold)",
            letterSpacing: "0.5px",
          }}
        >
          manifest.json
        </span>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 9,
            color: "var(--muted)",
            textTransform: "uppercase",
            letterSpacing: "1px",
          }}
        >
          Evidence Schema v1.1
        </span>
      </div>
      <pre
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: "var(--muted)",
          lineHeight: 1.5,
          margin: 0,
          overflow: "auto",
          maxHeight: 300,
          whiteSpace: "pre-wrap",
          wordBreak: "break-all",
        }}
      >
        {JSON.stringify(manifest, null, 2)}
      </pre>
    </div>
  );
}

export default function EvidenceUploader() {
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [showManifest, setShowManifest] = useState(false);
  const [theme, setTheme] = useState("dark");
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);
  const idCounter = useRef(0);

  const themeVars =
    theme === "dark"
      ? {
          "--bg": "#0D0D0D",
          "--surface": "#1A1A1A",
          "--card": "#222222",
          "--border": "#333333",
          "--text": "#E8E8E8",
          "--muted": "#999999",
          "--gold": "#C9A84C",
          "--gold-dim": "#8B7535",
        }
      : {
          "--bg": "#FAFAF8",
          "--surface": "#FFFFFF",
          "--card": "#F5F5F0",
          "--border": "#E0E0D8",
          "--text": "#1A1A1A",
          "--muted": "#666666",
          "--gold": "#8B7535",
          "--gold-dim": "#C9A84C",
        };

  const processFile = useCallback(
    async (rawFile) => {
      const typeInfo = ACCEPTED_TYPES[rawFile.type];
      if (!typeInfo) {
        const tempId = `err-${++idCounter.current}`;
        setFiles((prev) => [
          ...prev,
          {
            id: tempId,
            name: rawFile.name,
            size: rawFile.size,
            icon: "⚠",
            status: "error",
            error: `Unsupported type: ${rawFile.type || "unknown"}`,
            category: "ERR",
            evidenceId: "ERR",
          },
        ]);
        return;
      }

      const maxBytes = typeInfo.maxMB * 1024 * 1024;
      if (rawFile.size > maxBytes) {
        const tempId = `err-${++idCounter.current}`;
        setFiles((prev) => [
          ...prev,
          {
            id: tempId,
            name: rawFile.name,
            size: rawFile.size,
            icon: typeInfo.icon,
            status: "error",
            error: `Exceeds ${typeInfo.maxMB}MB limit (${formatBytes(rawFile.size)})`,
            category: typeInfo.category,
            evidenceId: "ERR",
          },
        ]);
        return;
      }

      const fileId = `ev-${++idCounter.current}`;

      // Generate preview for images
      let preview = null;
      if (rawFile.type.startsWith("image/")) {
        preview = URL.createObjectURL(rawFile);
      }

      // Determine transport mode
      const sizeMB = rawFile.size / (1024 * 1024);
      const transportMode =
        rawFile.type.startsWith("video/") && sizeMB > VIDEO_THRESHOLD_MB
          ? "pointer"
          : "local";

      setFiles((prev) => {
        const evidenceId = generateEvidenceId(typeInfo.category, prev);
        return [
          ...prev,
          {
            id: fileId,
            name: rawFile.name,
            size: rawFile.size,
            mime: rawFile.type,
            icon: typeInfo.icon,
            category: typeInfo.category,
            evidenceId,
            status: "hashing",
            hashProgress: 0,
            sha256: null,
            role: "primary_evidence",
            preview,
            transportMode,
            error: null,
          },
        ];
      });

      // Compute SHA-256 with progress
      try {
        const hash = await computeSHA256(rawFile, (progress) => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, hashProgress: progress } : f
            )
          );
        });

        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId ? { ...f, status: "ready", sha256: hash } : f
          )
        );
      } catch (err) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? { ...f, status: "error", error: `Hash failed: ${err.message}` }
              : f
          )
        );
      }
    },
    []
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      dragCounter.current = 0;

      const droppedFiles = Array.from(e.dataTransfer.files);
      droppedFiles.forEach(processFile);
    },
    [processFile]
  );

  const handleDragEnter = (e) => {
    e.preventDefault();
    dragCounter.current++;
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    dragCounter.current--;
    if (dragCounter.current === 0) setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleFileInput = (e) => {
    Array.from(e.target.files).forEach(processFile);
    e.target.value = "";
  };

  const removeFile = (id) => {
    setFiles((prev) => {
      const f = prev.find((x) => x.id === id);
      if (f?.preview) URL.revokeObjectURL(f.preview);
      return prev.filter((x) => x.id !== id);
    });
  };

  const changeRole = (id, role) => {
    setFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, role } : f))
    );
  };

  const readyCount = files.filter((f) => f.status === "ready").length;
  const hashingCount = files.filter((f) => f.status === "hashing").length;
  const errorCount = files.filter((f) => f.status === "error").length;
  const localCount = files.filter(
    (f) => f.status === "ready" && f.transportMode === "local"
  ).length;
  const pointerCount = files.filter(
    (f) => f.status === "ready" && f.transportMode === "pointer"
  ).length;

  return (
    <div
      style={{
        ...themeVars,
        fontFamily: "'Outfit', sans-serif",
        color: "var(--text)",
        background: "var(--bg)",
        minHeight: "100vh",
        padding: "24px 20px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "'Bricolage Grotesque', sans-serif",
              fontSize: 20,
              fontWeight: 700,
              color: "var(--gold)",
              margin: 0,
              letterSpacing: "0.5px",
            }}
          >
            Evidence Uploader
          </h1>
          <p
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontSize: 12,
              color: "var(--muted)",
              margin: "4px 0 0 0",
            }}
          >
            Composer v11 — Chain of Custody starts here
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              background: "var(--surface)",
              color: "var(--muted)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "4px 10px",
              cursor: "pointer",
              letterSpacing: "0.5px",
            }}
          >
            {theme === "dark" ? "KLAR" : "NOIR"}
          </button>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? "var(--gold)" : "var(--border)"}`,
          borderRadius: 12,
          padding: files.length === 0 ? "48px 24px" : "24px",
          textAlign: "center",
          cursor: "pointer",
          transition: "all 0.3s ease",
          background: isDragging
            ? theme === "dark"
              ? "rgba(201, 168, 76, 0.05)"
              : "rgba(139, 117, 53, 0.05)"
            : "transparent",
          marginBottom: 20,
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={Object.keys(ACCEPTED_TYPES).join(",")}
          onChange={handleFileInput}
          style={{ display: "none" }}
        />

        {files.length === 0 ? (
          <>
            <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.6 }}>
              🛡️
            </div>
            <div
              style={{
                fontFamily: "'Bricolage Grotesque', sans-serif",
                fontSize: 16,
                fontWeight: 600,
                color: "var(--text)",
                marginBottom: 6,
              }}
            >
              Drop evidence files here
            </div>
            <div
              style={{
                fontSize: 12,
                color: "var(--muted)",
                marginBottom: 12,
              }}
            >
              Images, video, audio, PDF — hashed client-side before upload
            </div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9,
                color: "var(--gold-dim)",
                letterSpacing: "1px",
                textTransform: "uppercase",
              }}
            >
              SHA-256 computed locally — proof born in your hands
            </div>
          </>
        ) : (
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: "var(--muted)",
              letterSpacing: "0.5px",
            }}
          >
            + Drop more files to add evidence
          </div>
        )}
      </div>

      {/* Status Bar */}
      {files.length > 0 && (
        <div
          style={{
            display: "flex",
            gap: 16,
            marginBottom: 16,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              letterSpacing: "0.5px",
            }}
          >
            <span style={{ color: "#4CAF50" }}>●</span>{" "}
            <span style={{ color: "var(--muted)" }}>
              {readyCount} sealed
            </span>
          </div>
          {hashingCount > 0 && (
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                letterSpacing: "0.5px",
              }}
            >
              <span style={{ color: "var(--gold)" }}>●</span>{" "}
              <span style={{ color: "var(--muted)" }}>
                {hashingCount} hashing
              </span>
            </div>
          )}
          {errorCount > 0 && (
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                letterSpacing: "0.5px",
              }}
            >
              <span style={{ color: "#D45454" }}>●</span>{" "}
              <span style={{ color: "var(--muted)" }}>
                {errorCount} error
              </span>
            </div>
          )}

          <div style={{ flex: 1 }} />

          {readyCount > 0 && (
            <div
              style={{
                display: "flex",
                gap: 8,
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9,
                letterSpacing: "0.5px",
                textTransform: "uppercase",
              }}
            >
              <span style={{ color: "#6B8E6B" }}>
                {localCount} local
              </span>
              {pointerCount > 0 && (
                <span style={{ color: "#7B8FA1" }}>
                  {pointerCount} pointer
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Evidence Cards Grid */}
      {files.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: 12,
          }}
        >
          {files.map((f) => (
            <EvidenceCard
              key={f.id}
              file={f}
              onRemove={removeFile}
              onRoleChange={changeRole}
            />
          ))}
        </div>
      )}

      {/* Actions */}
      {readyCount > 0 && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: 20,
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <button
            onClick={() => setShowManifest(!showManifest)}
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              background: "var(--surface)",
              color: "var(--gold)",
              border: "1px solid var(--gold-dim)",
              borderRadius: 6,
              padding: "8px 16px",
              cursor: "pointer",
              letterSpacing: "0.5px",
            }}
          >
            {showManifest ? "Hide" : "Preview"} manifest.json
          </button>

          <button
            disabled={hashingCount > 0}
            style={{
              fontFamily: "'Bricolage Grotesque', sans-serif",
              fontSize: 13,
              fontWeight: 600,
              background:
                hashingCount > 0
                  ? "var(--border)"
                  : "linear-gradient(135deg, var(--gold-dim), var(--gold))",
              color: hashingCount > 0 ? "var(--muted)" : "#0D0D0D",
              border: "none",
              borderRadius: 6,
              padding: "10px 24px",
              cursor: hashingCount > 0 ? "not-allowed" : "pointer",
              letterSpacing: "0.5px",
            }}
          >
            {hashingCount > 0
              ? `Hashing ${hashingCount} file${hashingCount > 1 ? "s" : ""}...`
              : `Seal ${readyCount} Evidence File${readyCount > 1 ? "s" : ""}`}
          </button>
        </div>
      )}

      {/* Manifest Preview */}
      {showManifest && <ManifestPreview files={files} />}

      {/* Footer */}
      <div
        style={{
          marginTop: 32,
          paddingTop: 16,
          borderTop: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 9,
            color: "var(--muted)",
            letterSpacing: "0.5px",
          }}
        >
          WINDI PACT v1.0 — Evidence Schema v1.1
        </span>
        <span
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 10,
            color: "var(--gold-dim)",
            fontStyle: "italic",
          }}
        >
          "Evidence is the currency of truth. The Ledger is its bank."
        </span>
      </div>
    </div>
  );
}
