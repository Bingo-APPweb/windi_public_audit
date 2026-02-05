// WINDI SDK - Reference Emitter (TypeScript / Node)
// RFC-002: WINDI-SEC-JSON-v1 (HMAC default)
// "Flow is Truth. Content is Sovereign."

import crypto from "crypto";

export type Alg = "HMAC-SHA256";
export type Shelf = "S1" | "S2" | "S3" | "S4" | "S5" | "S6" | "S7";

export type WindiEvent =
  | "DOC_CREATED"
  | "APPROVAL_REQUESTED"
  | "APPROVED"
  | "REJECTED"
  | "APPROVAL_OVERRIDDEN"
  | "DEADLINE_EXCEEDED"
  | "DEPENDENCY_LINKED"
  | "DEPENDENCY_BLOCKING"
  | "STATE_TRANSITION";

const EVENTS = new Set<WindiEvent>([
  "DOC_CREATED",
  "APPROVAL_REQUESTED",
  "APPROVED",
  "REJECTED",
  "APPROVAL_OVERRIDDEN",
  "DEADLINE_EXCEEDED",
  "DEPENDENCY_LINKED",
  "DEPENDENCY_BLOCKING",
  "STATE_TRANSITION",
]);

export interface WindiEmitterConfig {
  clientId: string;
  keyId: string;
  csaltB64: string;
  hmacKeyB64: string;
  protocolVersion?: "1.0";
  alg?: Alg;
}

export interface TelemetryHeader {
  v: "1.0";
  alg: Alg;
  cid: string;
  kid: string;
  ts: number;
  nonce: string;
  seq: number;
}

export interface TelemetryPayload {
  shelf: Shelf;
  code: string;
  weight: number;
  domain_hash: string;
  doc_fingerprint: string;
  event: WindiEvent;
  ctx?: { window: "1m" | "5m" | "15m" | "1h" | "24h" | "7d" | "30d"; flags: number };
}

export interface TelemetryPacket {
  header: TelemetryHeader;
  payload: TelemetryPayload;
  auth: { sig: string };
}

function b64(buf: Buffer): string {
  return buf.toString("base64");
}

function sha256(data: Buffer | string): Buffer {
  return crypto.createHash("sha256").update(data).digest();
}

function stableSort(value: any): any {
  if (Array.isArray(value)) return value.map(stableSort);
  if (value && typeof value === "object") {
    const out: any = {};
    Object.keys(value)
      .sort()
      .forEach((k) => (out[k] = stableSort(value[k])));
    return out;
  }
  return value;
}

function canonicalJson(obj: any): Buffer {
  return Buffer.from(JSON.stringify(stableSort(obj)), "utf8");
}

export class WindiEmitter {
  private readonly cfg: Required<WindiEmitterConfig>;
  private readonly csalt: Buffer;
  private readonly hmacKey: Buffer;
  private readonly cid: string;
  private seq: number;

  constructor(cfg: WindiEmitterConfig) {
    this.cfg = { protocolVersion: "1.0", alg: "HMAC-SHA256", ...cfg };
    this.csalt = Buffer.from(this.cfg.csaltB64, "base64");
    this.hmacKey = Buffer.from(this.cfg.hmacKeyB64, "base64");
    this.cid = b64(sha256(Buffer.from(this.cfg.clientId, "utf8")));
    this.seq = 0;
  }

  deriveDomainHash(domainId: string): string {
    const raw = Buffer.concat([
      Buffer.from("WINDI:DOMAIN:v1", "utf8"),
      this.csalt,
      Buffer.from(domainId, "utf8"),
    ]);
    return b64(sha256(raw));
  }

  deriveDocFingerprint(docVectorBytes: Buffer): string {
    const raw = Buffer.concat([
      Buffer.from("WINDI:DOC:v1", "utf8"),
      this.csalt,
      docVectorBytes,
    ]);
    return b64(sha256(raw));
  }

  private sign(header: TelemetryHeader, payload: TelemetryPayload): string {
    const msg = canonicalJson({ header, payload });
    const mac = crypto.createHmac("sha256", this.hmacKey).update(msg).digest();
    return b64(mac);
  }

  emit(params: {
    shelf: Shelf;
    code: string;
    weight: number;
    domainId: string;
    docVectorBytes: Buffer;
    event: WindiEvent;
    ctxWindow?: TelemetryPayload["ctx"]["window"];
    ctxFlags?: number;
    tsMs?: number;
  }): TelemetryPacket {
    const { shelf, code, weight, domainId, docVectorBytes, event } = params;
    if (!EVENTS.has(event)) throw new Error(`Invalid event: ${event}`);
    if (weight < 0 || weight > 100) throw new Error("weight must be 0..100");

    const ts = params.tsMs ?? Date.now();
    const nonce = crypto.randomBytes(12);

    const header: TelemetryHeader = {
      v: "1.0",
      alg: "HMAC-SHA256",
      cid: this.cid,
      kid: this.cfg.keyId,
      ts,
      nonce: b64(nonce),
      seq: ++this.seq,
    };

    const payload: TelemetryPayload = {
      shelf,
      code,
      weight,
      domain_hash: this.deriveDomainHash(domainId),
      doc_fingerprint: this.deriveDocFingerprint(docVectorBytes),
      event,
      ctx: { window: params.ctxWindow ?? "5m", flags: params.ctxFlags ?? 0 },
    };

    const sig = this.sign(header, payload);
    return { header, payload, auth: { sig } };
  }
}

export function saltLocalId(csaltB64: string, localId: string): Buffer {
  const csalt = Buffer.from(csaltB64, "base64");
  return sha256(Buffer.concat([Buffer.from("WINDI:LOCALID:v1", "utf8"), csalt, Buffer.from(localId, "utf8")]));
}

export function buildDocVectorBytes(params: {
  docTypeId: number;
  issuerRoleId: number;
  impactBandId: number;
  lifecycleStateId: number;
  localDocIdSalted?: Buffer;
}): Buffer {
  const buf = Buffer.alloc(6);
  buf.writeUInt16BE(params.docTypeId, 0);
  buf.writeUInt16BE(params.issuerRoleId, 2);
  buf.writeUInt8(params.impactBandId, 4);
  buf.writeUInt8(params.lifecycleStateId, 5);
  return params.localDocIdSalted ? Buffer.concat([buf, params.localDocIdSalted]) : buf;
}
