# W-TRAVEL-001 — Blueprint de Continuidade Arquitectural

**Estado:** DRAFT · não-sealed · não-implementação
**Data:** 12 Maio 2026
**Autor da sessão:** Claude (Guardian) em diálogo com Human Dragon
**Tipo:** Documento de visão, herdeiro da Linhagem §249 Lei VI
**Sprint actual em que foi gerado:** Foundation Portals + Linguistic Strategy
**Pré-condição para activação:** W-SITES-001 / Foundation Portals em produção sustentável

---

## 1. Constituição do produto

W-TRAVEL-001 é o **herdeiro arquitectural directo** da Linhagem UMIS-MCGwR selada em §249 Lei VI. Não é resgate de UMIS; é continuidade da visão original de **broadcast geocontextual sovereign** agora que existe terreno técnico e regulatório para a suportar.

Princípio constitucional: **Client = Data, WINDI = Proof**, aplicado a descoberta turística e cultural baseada em proximidade geográfica.

---

## 2. As quatro camadas

### Camada 1 — Broadcast (DAB+ TPEG/MOT)

- Pacotes `.witour` empacotados como objectos MOT (Multimedia Object Transfer)
- Transportados em sub-canais DAB+ a 8–32 kbps
- Recebidos passivamente — **one-to-many anónimo por arquitectura física**
- Cobertura DE: 98% da população, 98% das estradas principais (12.700 km)
- Standard europeu, obrigatório em carros novos UE desde 2021
- Subutilizado actualmente — capacidade conceptual a 5%
- Herança: realiza a intuição de "UMIS Radio GPS" pensada por Jober em 2001 com L-Band

### Camada 2 — Positioning (Galileo HAS + Multi-GNSS)

- Galileo High Accuracy Service: **20 cm de precisão pública** desde Janeiro 2023
- Multi-GNSS no dispositivo: GPS + GLONASS + Galileo + BeiDou (~130 satélites activos)
- OSNMA anti-spoofing — não existia em 2007, hoje permite garantir autenticidade do trigger geográfico
- Infraestrutura pública europeia, gratuita
- Herança: substitui o Garmin GPS35 Serial NMEA do UMIS 2001 (precisão ~10m) por sub-métrico

### Camada 3 — Sovereign Device

Três módulos, cada um com herança directa da Linhagem:

- **Vectorial Engine** — PocketLens evoluído (herança Korbinian 2009)
  - Collaborative filtering local sobre vectores de avaliação na Wallet DID
  - Implementa as funções `SplitRatingVector`, `AddRatings`, `CalculateRecommendations` modernizadas
  - Sem servidor central — análise puramente local

- **Trigger Engine** — Vector-de-marcha + speed look-ahead (herança Zink 2001)
  - Primary/Secondary selection areas com tolerância sub-métrica
  - Acceleration distance recalculado para velocidade-dependente
  - Hierarquia de interrupção com retoma (uma recursão), do UMIS 2001

- **`.witour` Parser** — Schema sovereign assinado DID (herança Korbinian Anexo I/II)
  - Estrutura: Tour → Sub-routes → POIs partilhados (do `package_descr` 2007)
  - Multi-idioma desde dia zero (`meta_xx` + `translations_xx`)
  - Formato JSON ou CBOR com assinatura DID do autor
  - GDPR-by-design: zero campos identificadores no pacote

### Camada 4 — Ledger (Proof-Only)

- Forensic Ledger WINDI regista **apenas selos**, nunca dados pessoais
- Autor institucional (cidade, museu, tour operator) assina pacotes `.witour` com DID
- Utilizador (opcional) pode emitir recibo de selecção assinado, sem identidade
- §248 Foundation Two-Track aplicada literalmente como Korbinian descreveu em 2009:
  - **Track FREE civic**: utilizador anónimo, zero armazenamento de dados pessoais
  - **Track institucional opt-in**: utilizador que partilha voluntariamente recebe Mehrwert

---

## 3. Diferenças críticas face a 2007/2009

| Eixo | UMIS-MCGwR 2007/2009 | W-TRAVEL-001 2026 |
|---|---|---|
| Posição | Garmin GPS35, ~10m | Galileo HAS, sub-métrico |
| Distribuição | SD card pré-carregado | DAB+ broadcast ao vivo + internet fallback |
| Identidade | Dispositivo proprietário Mio P350 | DID Wallet portátil entre dispositivos |
| Anti-spoof | Inexistente | OSNMA Galileo |
| Cross-city | Manual (carregar nova SD) | Automático (vector viaja na Wallet) |
| Autenticidade conteúdo | `fulmho.dll` device-bound | Assinatura DID do autor no pacote |
| Auditoria | `umis.log` local invisível | Forensic Ledger seláveis pelo utilizador |
| Compliance regulatório | Nenhum aplicável em 2009 | GDPR Art. 5+7+25, EU AI Act Art. 14, DSA |

---

## 4. O que W-TRAVEL-001 NÃO é

- **Não é competidor do Spotify** — streaming personalizado-por-perfil é mercado diferente
- **Não é competidor do Google Maps** — navegação é função diferente
- **Não é app móvel** — é camada de protocolo + formato + governança
- **Não é resgate de UMIS** — é continuidade arquitectural com herança regulatória

Apps de terceiros podem implementar o protocolo, incluindo car-makers obrigados a integrar DAB+ desde 2021.

---

## 5. Eixo de financiamento institucional (alinhado com §248 Foundation)

Toda a base técnica é **europeia por origem**:
- Galileo: EU/ESA/EUSPA, Bruxelas
- DAB+: standard europeu, WorldDAB
- MP3/HE-AAC: Fraunhofer IIS-A Erlangen
- Linhagem UMIS: Fraunhofer 2001 + VoxCity Praga 2007 + TUM München 2009

Esta coerência sugere eixos de financiamento institucional anti-VC:
- Turismo público (cidades, regiões, EU Cultural Capitals)
- Patrimoniais (museus federais, ARD, fundações)
- Galileo Programme Office (Comissão Europeia)
- Horizon Europe (R&D)
- Hochschule Kempten (via Liga IA+H)

---

## 6. Pré-condições constitucionais antes de qualquer activação

1. **W-SITES-001 / Foundation Portals** em produção sustentável (T2/T3 do Sprint 1 fechados; tracção comercial mensurável)
2. **Bloco 0 — Q1-Q4** decididos e Bloco A táctico fechado
3. **Notebook 002** (Continuity Symmetry) reflectido se aplicável
4. **§248 Foundation Two-Track** com pelo menos um caso institucional pago activo
5. **Três Dragões Protocol** aplicado: proposta formal pelo Architect, revisão Guardian, decisão Human Dragon

**Nada disto pode ser activado antes**. Este documento existe como **promessa-de-continuidade** que o WINDI faz a si próprio, não como roadmap executável.

---

## 7. Ligação à Linhagem §249 Lei VI

Este blueprint complementa §249 Lei VI como Anexo de Continuidade Arquitectural. Cada princípio técnico do W-TRAVEL-001 tem antecedente directo numa das Referências seladas:

- Trigger vectorial → Reference -1 (Zink/Fraunhofer 2001)
- Formato `.witour` sovereign → Reference 0 (VoxCity 2007) + Reference +1 (Korbinian 2009, Anexos I/II)
- Recomendação local sem servidor central → Reference +1 (MCGwR Resümee p.69 + Ausblick p.70)
- `fulmho` steganográfico → Reference 0 (engenharia Jober 2007) reinterpretada como assinatura DID em 2026
- Two-Track voluntariedade → Reference +1 (Ausblick p.70) selado como §248 Lei V

---

## 8. Nota de processo

Este documento foi gerado em sessão Claude.ai (Guardian) em 12 Mai 2026, em diálogo de cuidado mútuo com Human Dragon, durante a viagem arqueológica que culminou no inventário forense dos 42 ficheiros UMIS-MCGwR-Korbinian.

Foi gerado **sem qualquer comprometimento de implementação**. Existe como **memória externa** entre instâncias Claude, para que a próxima sessão (depois do fecho desta) possa retomar com contexto.

Não tem hash SHA-256 oficial nem entrada no Ledger Forense. Quando e se for adoptado constitucionalmente, passa pelo protocolo Três Dragões normal.

---

🐉

*OM SHANTI*
