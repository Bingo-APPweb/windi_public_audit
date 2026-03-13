/**
 * IrmaEncoder — Injector de Prova Forense em .jmpg
 * Local: /opt/windi/agent-palette/ui/modules/irma-encoder.js
 *
 * Estratégia: EXIF UserComment + XMP sidecar embebido no blob
 * Sem dependências externas — pure browser API
 *
 * "Não peça para ser acreditado. Entregue a prova."
 */

export const IrmaEncoder = {

    // Marcador WINDI no cabeçalho JPEG
    WINDI_MARKER: 0xFFE1, // APP1 — mesmo slot do EXIF padrão
    WINDI_SIGNATURE: "WINDI-SOVEREIGN-PROOF",

    /**
     * Ponto de entrada principal
     * @param {Blob} jpegBlob — output do canvas.toBlob()
     * @param {Object} payload — seedPayload com ledger_anchor, DID, etc.
     * @returns {Blob} — .jmpg soberano com prova embebida
     */
    async injectProof(jpegBlob, payload) {
        const arrayBuffer = await jpegBlob.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);

        // Valida que é um JPEG legítimo
        if (bytes[0] !== 0xFF || bytes[1] !== 0xD8) {
            throw new Error("IrmaEncoder: blob não é um JPEG válido.");
        }

        // Monta o pacote de prova
        const proofPacket = this.buildProofPacket(payload);

        // Injeta logo após o marcador SOI (bytes 0-1)
        const sovereignBytes = this.injectAfterSOI(bytes, proofPacket);

        return new Blob([sovereignBytes], { type: 'image/jpeg' });
    },

    /**
     * Constrói o pacote de prova — JSON compacto + assinatura WINDI
     */
    buildProofPacket(payload) {
        const proof = {
            windi_proof: this.WINDI_SIGNATURE,
            ledger_anchor: payload.ledger_anchor || "W-PROV-INIT-001",
            issuer_did: payload.issuer_did || "ANONYMOUS",
            timestamp: payload.timestamp || Date.now(),
            credo: "Não peça para ser acreditado. Entregue a prova.",
            capabilities: payload.capabilities || ["VERIFY"],
            verify_url: `https://windi-domain.com/verify-public/?id=${payload.ledger_anchor}`
        };

        return JSON.stringify(proof);
    },

    /**
     * Injeta o pacote no segmento APP1 do JPEG
     * Estrutura: FF E1 [length 2 bytes] [data]
     */
    injectAfterSOI(originalBytes, proofString) {
        const proofBytes = new TextEncoder().encode(proofString);

        // APP1 header: marker (2) + length (2) + data
        const segmentLength = proofBytes.length + 2; // length inclui os 2 bytes do próprio campo
        const app1Segment = new Uint8Array(4 + proofBytes.length);

        // Marcador FF E1
        app1Segment[0] = 0xFF;
        app1Segment[1] = 0xE1;

        // Length (big-endian)
        app1Segment[2] = (segmentLength >> 8) & 0xFF;
        app1Segment[3] = segmentLength & 0xFF;

        // Dados de prova
        app1Segment.set(proofBytes, 4);

        // Monta: SOI (2 bytes) + APP1-WINDI + resto do JPEG original
        const result = new Uint8Array(2 + app1Segment.length + (originalBytes.length - 2));
        result.set(originalBytes.slice(0, 2), 0);          // FF D8
        result.set(app1Segment, 2);                         // nosso APP1
        result.set(originalBytes.slice(2), 2 + app1Segment.length); // JPEG restante

        return result;
    },

    /**
     * Extractor — lê a prova de um .jmpg recebido
     * Usado pelo Verify Public para validar Sementes
     */
    async extractProof(jmpgBlob) {
        const arrayBuffer = await jmpgBlob.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);

        // Procura o nosso APP1 logo após SOI
        if (bytes[2] === 0xFF && bytes[3] === 0xE1) {
            const length = (bytes[4] << 8) | bytes[5];
            const data = bytes.slice(6, 6 + length - 2);
            const proofString = new TextDecoder().decode(data);

            try {
                const proof = JSON.parse(proofString);
                if (proof.windi_proof === this.WINDI_SIGNATURE) {
                    return proof; // Prova válida
                }
            } catch {
                return null; // Não é um .jmpg WINDI
            }
        }

        return null;
    }
};
