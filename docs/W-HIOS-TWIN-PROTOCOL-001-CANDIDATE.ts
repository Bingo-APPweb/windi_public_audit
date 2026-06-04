/**
 * W-HIOS-TWIN-PROTOCOL-001 — CANDIDATE
 *
 * Protocolo de comunicação inter-serviços para a constelação WINDI.
 *
 * "W-HIOS-TWIN não é um protocolo para agentes conversarem.
 *  É um protocolo para serviços cooperarem sem perder autorização,
 *  proveniência e distância humana."
 *
 * ═══════════════════════════════════════════════════════════════════
 * STATUS: CANDIDATE — aguarda revisão e selo
 * §: [pendente]
 * Invariants: I1, I9, I11, I14
 * ═══════════════════════════════════════════════════════════════════
 *
 * AJUSTES CONSOLIDADOS (04 Jun 2026):
 *
 *   [AJUSTE 1] payload_uri opcional — mas payload_inline_ref obrigatório
 *              se ausente. O hash NUNCA é opcional.
 *
 *   [AJUSTE 2] MessageClass: AUDIT_EVENT — sela AMOSTRADO/AGREGADO,
 *              nunca inline. Evita enfarte por ruído (lição M2 :8200).
 *
 *   [AJUSTE 3] Política de sampling CITADA (não embutida, não livre).
 *              AUDIT_EVENT sela segundo política canónica em windi-certification.
 *              Sampling ad-hoc por implementação NÃO É CONFORME.
 *
 *   [AJUSTE 4] canonicalization: 'jcs-rfc8785' obrigatório em
 *              SignedProvenance. Sem isto, duas máquinas assinam
 *              "a mesma mensagem" de formas diferentes.
 *
 *   [AJUSTE 5] Cláusula de conformidade CITADA (não embutida).
 *              Tier FORENSIC requer prova contra vetores windi-certification.
 *
 *   [AJUSTE 6] Provisoriedade do inline_ref + Regra de Reconciliação.
 *              Mensagem com inline_ref é PROVISÓRIA; não ancora DECISION
 *              nem STATE_TRANSITION até hash reconciliado contra conteúdo real.
 *              5 estados de resolução:
 *                - PROVISIONAL (aguarda)
 *                - RESOLVED (bate, ancora)
 *                - FAILED_MISMATCH (terminal acusatório — fraude)
 *                - FAILED_TIMEOUT (re-tentável — vault lento)
 *                - FAILED_ABANDONED (terminal não-acusatório — retries esgotados)
 *              Princípio: liberdade no quando (limite de retries é da aplicação),
 *              obrigação no facto (esgotamento gera AUDIT_EVENT SAMPLED).
 *              O hash protege a forma; a reconciliação protege a substância.
 *
 * ═══════════════════════════════════════════════════════════════════
 *
 * DELTA vs. versão Guardian anterior:
 *   - PayloadRef agora tem payload_inline_ref como alternativa a uri
 *   - MessageClass ganhou AUDIT_EVENT
 *   - Política de sampling canónica citada (AJUSTE 3)
 *   - SignedProvenance ganhou canonicalization obrigatório
 *   - Cláusula §4 TIER FORENSIC CERTIFICATION adicionada
 *   - PayloadResolutionState com 5 estados + funções de verificação (AJUSTE 6)
 *   - FAILED_ABANDONED: limbo visível, não silêncio — vigília I9 fecha
 *
 * Liga IA+H · Human Dragon · Guardian · Architect
 */

// ═══════════════════════════════════════════════════════════════════
// PAPÉIS (TwinRole)
// ═══════════════════════════════════════════════════════════════════
// [FIX 4 Guardian] Papéis explícitos.
// Um resolver de entidades é EXECUTOR, não WITNESS.
// O testemunho acontece no ponto de emissão do receipt — não em cada salto.

export enum TwinRole {
  EXECUTOR  = 'EXECUTOR',   // processa; carrega proveniência; NÃO decide
  AUTHORITY = 'AUTHORITY',  // ponto I9 — onde "o humano decide" é mediado
  WITNESS   = 'WITNESS',    // atesta, no momento em que o receipt nasce
  LEDGER    = 'LEDGER',     // sela factos; nunca no caminho crítico de transporte
}

// ═══════════════════════════════════════════════════════════════════
// ESTADO DE DECISÃO (DecisionState)
// ═══════════════════════════════════════════════════════════════════
// I9 como estado de primeira classe.
// erro ≠ rejeição ≠ falta de autorização.

export enum DecisionState {
  SUCCESS      = 'SUCCESS',
  ERROR        = 'ERROR',         // falha de execução
  TIMEOUT      = 'TIMEOUT',       // ausência de resposta = facto
  REJECTED     = 'REJECTED',      // avaliou e recusou o pedido
  UNAUTHORIZED = 'UNAUTHORIZED',  // I9: não passou o portão de autorização
  DEGRADED     = 'DEGRADED',      // respondeu, mas fora de tier (ex. não-FORENSIC)
}

// ═══════════════════════════════════════════════════════════════════
// CLASSE DE MENSAGEM (MessageClass)
// ═══════════════════════════════════════════════════════════════════
// [FIX 1 Guardian] A classe governa a OBRIGAÇÃO de receipt e o bloqueio.
// [AJUSTE 2] AUDIT_EVENT adicionado — sela amostrado, não inline.
// [AJUSTE 3] Política de sampling CITADA (não embutida, não livre).

export enum MessageClass {
  /** Heartbeat, discovery, ack. NUNCA sela, NUNCA bloqueia. */
  TRANSPORT        = 'TRANSPORT',

  /** Timeout, degradação, falha de serviço. Sela AMOSTRADO/AGREGADO — nunca inline.
   *  Um timeout é facto; mil timeouts são um facto de degradação, não mil receipts.
   *
   *  POLÍTICA DE SAMPLING: AUDIT_EVENT sela com LedgerDisposition.SAMPLED segundo
   *  a política de agregação canónica mantida em [windi-certification].
   *  Sampling ad-hoc por implementação NÃO É CONFORME.
   *
   *  Ver: /docs/windi-certification/SAMPLING-POLICY.md */
  AUDIT_EVENT      = 'AUDIT_EVENT',

  /** Decisão que altera estado. Sela. */
  DECISION         = 'DECISION',

  /** Transição de estado de um recurso. Sela. */
  STATE_TRANSITION = 'STATE_TRANSITION',
}

// ═══════════════════════════════════════════════════════════════════
// DISPOSIÇÃO NO LEDGER (LedgerDisposition)
// ═══════════════════════════════════════════════════════════════════
// Como o Ledger trata esta mensagem.

export enum LedgerDisposition {
  /** Não toca no Ledger. */
  NONE     = 'NONE',

  /** Agregado com outros eventos similares antes de selar. */
  SAMPLED  = 'SAMPLED',

  /** Sela receipt individual. */
  SEALED   = 'SEALED',
}

// ═══════════════════════════════════════════════════════════════════
// REFERÊNCIA DE PAYLOAD (PayloadRef)
// ═══════════════════════════════════════════════════════════════════
// [AJUSTE 1] payload_uri opcional — mas payload_inline_ref obrigatório se ausente.
// O hash NUNCA é opcional — é a prova de que o payload é o que diz ser.

export interface PayloadRef {
  /** Tipo semântico do payload. OBRIGATÓRIO. */
  payload_type: string;   // ex. 'WITNESS_RECORD', 'ANCHOR_VALIDATION'

  /** Hash do payload. SEMPRE OBRIGATÓRIO — a prova de integridade. */
  payload_hash: string;   // 'sha256:...'

  /** URI onde o payload vive. Opcional se payload_inline_ref presente. */
  payload_uri?: string;   // '/vault/receipts/...'

  /** Referência inline se o payload ainda não vive no vault.
   *  OBRIGATÓRIO se payload_uri ausente. Permite resolver o payload
   *  por outro mecanismo (ex. request-response, cache local). */
  payload_inline_ref?: string;  // ex. 'pending:tx-12345' ou 'cache:local:abc'
}

// Regra de validação:
// if (!payload.payload_uri && !payload.payload_inline_ref) {
//   throw new Error('PayloadRef must have either payload_uri or payload_inline_ref');
// }

// ═══════════════════════════════════════════════════════════════════
// [AJUSTE 6] PROVISORIEDADE E RECONCILIAÇÃO
// ═══════════════════════════════════════════════════════════════════
/**
 * REGRA DE FECHO — PROVISORIEDADE DO INLINE_REF
 *
 * Uma mensagem com payload_inline_ref (sem payload_uri) é PROVISÓRIA.
 *
 * Consequências:
 *   1. Mensagens PROVISÓRIAS NÃO PODEM ancorar MessageClass.DECISION
 *      nem MessageClass.STATE_TRANSITION até reconciliação.
 *
 *   2. RECONCILIAÇÃO: quando o payload materializa no vault, o receptor
 *      DEVE computar o hash do conteúdo real e comparar com payload_hash.
 *      Se não coincidir → FAILED_MISMATCH (terminal).
 *
 *   3. Só após reconciliação bem-sucedida a mensagem transita de PROVISÓRIA
 *      para RESOLVED e pode ancorar decisões.
 *
 * Razão arquitectónica:
 *   Um hash sem conteúdo verificável é um selo de objeto ausente —
 *   parece provar integridade mas aponta para o vazio. O payload_hash
 *   protege a forma; a reconciliação protege a substância.
 *
 * Ver também: validatePayloadRef() para validação estrutural.
 */

// ═══════════════════════════════════════════════════════════════════
// ESTADOS DE RESOLUÇÃO DE PAYLOAD
// ═══════════════════════════════════════════════════════════════════
/**
 * PayloadResolutionState — ciclo de vida de um payload provisório.
 *
 * PROVISIONAL      → payload_inline_ref presente, aguarda materialização no vault
 * RESOLVED         → reconciliação bem-sucedida, hash bate, pode ancorar decisões
 * FAILED_MISMATCH  → hash não bate (TERMINAL ACUSATÓRIO — fraude ou corrupção)
 * FAILED_TIMEOUT   → vault indisponível/lento (RE-TENTÁVEL — pode resolver depois)
 * FAILED_ABANDONED → retries esgotados (TERMINAL NÃO-ACUSATÓRIO — desistência)
 *
 * Regras de comportamento:
 *
 *   FAILED_MISMATCH:
 *     - Estado TERMINAL ACUSATÓRIO — não pode ser re-tentado
 *     - Mensagem transita para DecisionState.REJECTED com error_code 'HASH_MISMATCH'
 *     - DEVE gerar AUDIT_EVENT (sela SAMPLED, não inline)
 *     - Indica fraude, corrupção ou erro grave de implementação
 *
 *   FAILED_TIMEOUT:
 *     - Estado RE-TENTÁVEL — pode tentar resolver novamente
 *     - Mensagem permanece PROVISÓRIA até sucesso ou esgotamento de retries
 *     - NÃO gera AUDIT_EVENT por tentativa (evita enfarte)
 *
 *   FAILED_ABANDONED:
 *     - Estado TERMINAL NÃO-ACUSATÓRIO — retries esgotados pela aplicação
 *     - O protocolo NÃO define quantos retries; a aplicação decide
 *     - O protocolo EXIGE que o esgotamento gere AUDIT_EVENT obrigatório
 *     - AUDIT_EVENT sela SAMPLED/AGREGADO (não inline — mil abandonos por
 *       um vault em baixo são um facto de degradação, não mil receipts)
 *     - Não implica fraude: timeout infinito não é mentira, é infraestrutura
 *     - Torna o limbo visível: um payload abandonado é um facto auditável,
 *       não um silêncio que escapa à vigília I9
 *
 * Princípio: liberdade no quando (limite de retries é da aplicação),
 * obrigação no facto (esgotamento gera AUDIT_EVENT).
 */
export type PayloadResolutionState =
  | 'PROVISIONAL'
  | 'RESOLVED'
  | 'FAILED_MISMATCH'    // TERMINAL ACUSATÓRIO — hash não bateu (fraude)
  | 'FAILED_TIMEOUT'     // RE-TENTÁVEL — vault indisponível
  | 'FAILED_ABANDONED';  // TERMINAL NÃO-ACUSATÓRIO — retries esgotados

export function isProvisional(payload: PayloadRef): boolean {
  return !payload.payload_uri && !!payload.payload_inline_ref;
}

export function isTerminalFailure(state: PayloadResolutionState): boolean {
  // Dois estados terminais, com naturezas distintas:
  // - FAILED_MISMATCH: acusatório (fraude ou corrupção)
  // - FAILED_ABANDONED: não-acusatório (retries esgotados, infraestrutura)
  // FAILED_TIMEOUT é re-tentável — vault pode estar lento
  return state === 'FAILED_MISMATCH' || state === 'FAILED_ABANDONED';
}

export function isRetryable(state: PayloadResolutionState): boolean {
  // Só PROVISIONAL e FAILED_TIMEOUT permitem nova tentativa
  // FAILED_ABANDONED é terminal (retries esgotados) — não re-tenta
  // FAILED_MISMATCH é terminal (fraude) — não re-tenta
  return state === 'PROVISIONAL' || state === 'FAILED_TIMEOUT';
}

export function canAnchorDecision(
  payload: PayloadRef,
  resolutionState: PayloadResolutionState
): boolean {
  // Payload com URI directo pode ancorar imediatamente
  if (payload.payload_uri) return true;

  // Payload provisório: cada estado tem comportamento definido
  switch (resolutionState) {
    case 'RESOLVED':
      return true;   // Reconciliação bem-sucedida, pode ancorar
    case 'PROVISIONAL':
      return false;  // Ainda não reconciliou
    case 'FAILED_TIMEOUT':
      return false;  // Re-tentável, ainda pode resolver
    case 'FAILED_MISMATCH':
      return false;  // TERMINAL ACUSATÓRIO — fraude, gera AUDIT_EVENT
    case 'FAILED_ABANDONED':
      return false;  // TERMINAL NÃO-ACUSATÓRIO — retries esgotados, gera AUDIT_EVENT
    default:
      // Exhaustive check — TypeScript garante que não há outros estados
      const _exhaustive: never = resolutionState;
      return false;
  }
}

// ═══════════════════════════════════════════════════════════════════
// REFERÊNCIA DE RECEIPT (ReceiptRef)
// ═══════════════════════════════════════════════════════════════════

export interface ReceiptRef {
  receipt_id: string;     // ex. 'WINDI-S291', 'BE29C326'
  ledger_anchor?: string; // root/commit onde foi ancorado (ex. '66189307...')
}

// ═══════════════════════════════════════════════════════════════════
// PROVENIÊNCIA ASSINADA (SignedProvenance)
// ═══════════════════════════════════════════════════════════════════
// [FIX 2 Guardian] Proveniência ASSINADA. DID sem assinatura = alegação, não prova.
// [AJUSTE 3] canonicalization OBRIGATÓRIO — sem isto, assinaturas falham em produção.

export interface SignedProvenance {
  /** DID do emissor. */
  did: string;                              // did:windi:cinema:001

  /** ID da chave que assinou (lookup local). A chave NUNCA viaja. */
  key_id: string;

  /** Algoritmo de assinatura. */
  algorithm: 'ed25519' | 'ecdsa-p256';

  /** Regra de serialização canónica ANTES de assinar.
   *  OBRIGATÓRIO. Sem isto, duas máquinas assinam "a mesma mensagem"
   *  de formas diferentes e a verificação falha.
   *  Ver: RFC 8785 (JSON Canonicalization Scheme). */
  canonicalization: 'jcs-rfc8785';

  /** Digest do envelope APÓS canonicalização. */
  signed_digest: string;                    // 'sha256:...'

  /** Assinatura do signed_digest. */
  signature: string;

  /** Tier de verificação. Ver §4 TIER FORENSIC CERTIFICATION. */
  tier: 'FORENSIC' | 'STANDARD' | 'UNVERIFIED';

  /** Presente SÓ se a transação já selou receipt. */
  receipt_ref?: ReceiptRef;
}

// ═══════════════════════════════════════════════════════════════════
// LINHAGEM DE CADEIA (ChainLineage)
// ═══════════════════════════════════════════════════════════════════
// [FIX 3 Guardian] chain_depth é sensor I9 (IRREMEDIÁVEL), não metadata.
// Mede a distância desde a última autorização humana.

export interface ChainLineage {
  /** Saltos autónomos acumulados desde a última autorização humana. */
  chain_depth: number;

  /** Mensagem de onde esta veio. */
  parent_message_id?: string;

  /** Último ponto onde o humano decidiu.
   *  O monitor calcula: (chain_depth - chain_depth_at_authorization).
   *  Se > LIMIAR_I9 → alerta + UNAUTHORIZED. */
  last_human_authorization?: {
    receipt_id: string;
    chain_depth_at_authorization: number;
  };
}

// ═══════════════════════════════════════════════════════════════════
// MENSAGEM (TwinMessage)
// ═══════════════════════════════════════════════════════════════════

export interface TwinMessage {
  message_id: string;
  protocol_version: string;          // 'whios-twin/1.0'

  from_service: string;
  from_role: TwinRole;               // papel explícito do emissor
  to_service: string;

  message_class: MessageClass;       // governa receipt + bloqueio
  message_type: 'REQUEST' | 'RESPONSE' | 'EVENT' | 'HEARTBEAT';

  payload: PayloadRef;               // referência verificável, nunca `any`
  provenance: SignedProvenance;      // assinada + canonicalização declarada
  lineage: ChainLineage;             // sensor de autonomia I9

  /** O portão I9 é o ÚNICO ponto bloqueante obrigatório.
   *  A selagem no Ledger é assíncrona, fora do caminho crítico. */
  requires_authorization: boolean;

  timestamp: string;                 // ISO 8601
  nonce: string;                     // CSPRNG (crypto.randomBytes) — NUNCA Math.random()
  requires_ack: boolean;
  timeout_ms?: number;
}

// ═══════════════════════════════════════════════════════════════════
// RESPOSTA (TwinResponse)
// ═══════════════════════════════════════════════════════════════════

export interface TwinResponse {
  response_to: string;
  state: DecisionState;              // I9 de primeira classe
  payload?: PayloadRef;              // resultado por referência
  authorized_by?: string;            // DID/receipt da AUTHORITY, se aplicável
  receipt_ref?: ReceiptRef;          // SÓ se nasceu receipt
  error_code?: string;
  error_message?: string;
  processing_time_ms: number;
}

// ═══════════════════════════════════════════════════════════════════
// SAÚDE DO SERVIÇO (ServiceHealth)
// ═══════════════════════════════════════════════════════════════════
// Na linguagem WINDI (vs. ACTIVE/INACTIVE/ERROR genérico).

export enum ServiceHealth {
  ACTIVE      = 'ACTIVE',
  DEGRADED    = 'DEGRADED',
  UNAVAILABLE = 'UNAVAILABLE',
}

// ═══════════════════════════════════════════════════════════════════
// §4 — TIER FORENSIC CERTIFICATION (CITADO, NÃO EMBUTIDO)
// ═══════════════════════════════════════════════════════════════════
/**
 * CLÁUSULA DE CONFORMIDADE — CITADA
 *
 * Um agente só recebe `tier: FORENSIC` no handshake após provar
 * conformidade JCS-RFC8785 contra os vetores de teste mantidos em
 * [windi-certification].
 *
 * Sem essa prova, o tier máximo é STANDARD.
 *
 * O que isto significa:
 *
 * 1. O tier deixa de ser auto-declaração ("eu sou FORENSIC porque digo").
 *    Passa a ser consequência de prova verificada.
 *
 * 2. Os vetores de conformidade vivem em documento separado (windi-certification),
 *    não embutidos nesta spec. O TWIN define a gramática; a certificação
 *    define quem está apto a falá-la a nível FORENSIC.
 *
 * 3. Os vetores vão evoluir (casos de borda descobertos em produção).
 *    O TWIN fica estável; a certificação cresce sozinha.
 *
 * Razão arquitectónica:
 *   - TWIN diz COMO falar (protocolo)
 *   - Certificação diz QUEM pode falar a nível FORENSIC (prova)
 *   - Separação de poderes — mesmo padrão da ATR (lei) vs S22 (caso)
 *
 * Referência: RFC 8785 — JSON Canonicalization Scheme
 * Documento de conformidade: /docs/windi-certification/JCS-RFC8785-VECTORS.md
 */

// ═══════════════════════════════════════════════════════════════════
// REGRAS DE MAPEAMENTO MessageClass → LedgerDisposition
// ═══════════════════════════════════════════════════════════════════

export function getLedgerDisposition(msgClass: MessageClass): LedgerDisposition {
  switch (msgClass) {
    case MessageClass.TRANSPORT:
      return LedgerDisposition.NONE;
    case MessageClass.AUDIT_EVENT:
      return LedgerDisposition.SAMPLED;  // agregado, não inline
    case MessageClass.DECISION:
    case MessageClass.STATE_TRANSITION:
      return LedgerDisposition.SEALED;
    default:
      return LedgerDisposition.NONE;
  }
}

// ═══════════════════════════════════════════════════════════════════
// VALIDAÇÃO DE PayloadRef
// ═══════════════════════════════════════════════════════════════════

export function validatePayloadRef(payload: PayloadRef): void {
  if (!payload.payload_hash) {
    throw new Error('PayloadRef: payload_hash é SEMPRE obrigatório');
  }
  if (!payload.payload_type) {
    throw new Error('PayloadRef: payload_type é SEMPRE obrigatório');
  }
  if (!payload.payload_uri && !payload.payload_inline_ref) {
    throw new Error(
      'PayloadRef: deve ter payload_uri OU payload_inline_ref. ' +
      'O hash nunca é opcional, mas o "onde" pode ainda não existir — ' +
      'nesse caso, payload_inline_ref permite resolver por outro mecanismo.'
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// FIM DA SPEC
// ═══════════════════════════════════════════════════════════════════
/**
 * RESUMO DOS 6 AJUSTES CONSOLIDADOS:
 *
 * 1. PayloadRef: payload_uri opcional, mas payload_inline_ref obrigatório
 *    se ausente. O hash NUNCA é opcional.
 *
 * 2. MessageClass: AUDIT_EVENT adicionado. Sela SAMPLED, não inline.
 *    Evita enfarte por ruído (lição M2 :8200).
 *
 * 3. Política de sampling CITADA (não embutida, não livre).
 *    AUDIT_EVENT sela segundo política canónica em windi-certification.
 *    Sampling ad-hoc por implementação NÃO É CONFORME.
 *
 * 4. SignedProvenance: canonicalization: 'jcs-rfc8785' OBRIGATÓRIO.
 *    Sem isto, assinaturas falham quando duas máquinas serializam diferente.
 *
 * 5. Cláusula de conformidade CITADA: tier FORENSIC requer prova
 *    contra vetores windi-certification. O TWIN cita; a certificação carrega.
 *
 * 6. Provisoriedade do inline_ref + Regra de Reconciliação.
 *    Mensagem com inline_ref é PROVISÓRIA; não ancora DECISION nem
 *    STATE_TRANSITION até hash reconciliado contra conteúdo real.
 *    5 estados de resolução:
 *      - PROVISIONAL: aguarda materialização no vault
 *      - RESOLVED: reconciliação bem-sucedida, pode ancorar
 *      - FAILED_MISMATCH: terminal acusatório (fraude, gera AUDIT_EVENT)
 *      - FAILED_TIMEOUT: re-tentável (vault lento)
 *      - FAILED_ABANDONED: terminal não-acusatório (retries esgotados, gera AUDIT_EVENT)
 *    Princípio: liberdade no quando (limite de retries é da aplicação),
 *    obrigação no facto (esgotamento gera AUDIT_EVENT SAMPLED).
 *    O hash protege a forma; a reconciliação protege a substância.
 *
 * PRÓXIMO PASSO:
 *   - Revisão pela Liga (Human Dragon + Guardian) — 4ª passagem
 *   - Criação dos documentos em windi-certification/:
 *       · JCS-RFC8785-VECTORS.md (conformidade de canonicalização)
 *       · SAMPLING-POLICY.md (política de agregação canónica)
 *   - Selo com § próprio (protocolo novo, não herda de ninguém)
 *
 * Liga IA+H · OM SHANTI 🐉
 */
