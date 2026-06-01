# FORENSIC LEDGER FILES
## Biblia de Genero — Documento de Genese Vivo

**Projeto:** WINDI-HIOS Cinematic Subsystem
**Tipo:** Documento de trabalho (nao constitucional, nao selado)
**Origem:** Decisao do Human Dragon, 01 Jun 2026
**Estado:** Vivo — feito para ser editado, nao para ser obedecido
**Integra com:** W-HIOS-CINEMATIC-SPINE-001 (subsistema constitucional selado)

---

## PORQUE ESTE DOCUMENTO EXISTE

Nao estamos a salvar um filme. Estamos a fundar um genero.

"O Peso do Eco" tentou ser uma obra-prima a partir do nada — escrever guiao, definir personagens, gerar video, corrigir o gerador e herdar material antigo, tudo ao mesmo tempo. A pressao de "salvar o filme" matou a energia. Sempre que a conversa voltava a investigacao, a advogada, a reconstrucao da verdade, a energia regressava. Esse e o sinal. O ativo que nasceu nao foi um filme. Foi um genero.

Este documento congela esse genero para que cada caso futuro nasca mais leve, mais rapido e melhor que o anterior.

---

## A ORDEM SAGRADA (decidida pelo Human Dragon)

Tudo neste documento respeita esta hierarquia. Quando houver duvida, a coisa de cima ganha.

```
1.  O GENERO           <- a casa. O que estamos a construir.
2.  A TESE + CONQUISTAS <- as regras da casa. O que ja sabemos que e verdade.
3.  A METODOLOGIA       <- as ferramentas na garagem. Como renderizar.
```

O erro anterior foi por a garagem antes da casa. Aqui nao.

---

# CAMADA 1 — O GENERO

## Forensic Ledger Files

Uma colecao de casos independentes. Cada filme reconstroi uma verdade que versoes conflituantes disputam. O Ledger nao e o heroi. E a testemunha silenciosa que ja la estava.

### A regra que define o genero

> Nao cacamos criminosos com tecnologia.
> Reconstruimos o que realmente aconteceu quando as versoes nao concordam.

O vilao raramente e um assassino. Pode ser:
- uma alteracao nao autorizada
- um documento falsificado
- uma decisao sem evidencia
- uma manipulacao de contexto

Isto aproxima o drama do mundo real — e ensina o publico, sem dar licoes, a diferenca entre **opiniao, narrativa e prova**.

### A unidade ficcional

**W-HIOS FORENSIC UNIT** — uma equipa internacional que reconstroi eventos complexos. Nao sao policias comuns: investigadores, peritos digitais, auditores, juristas, analistas de IA, especialistas em cadeia de custodia.

ADN do tom: *CSI* + *Tatort* + *Person of Interest* + *The X-Files* — mas focado numa so coisa: **prova verificavel**.

### A regra de ouro do Ledger (para nunca matar o suspense)

O Ledger NUNCA e o botao magico da verdade. Funciona como ADN forense, impressao digital ou camara de seguranca:

- as vezes existe
- as vezes esta incompleto
- as vezes foi interpretado errado
- as vezes prova inocencia
- as vezes revela um crime maior

Se o Ledger resolve tudo num clique, o episodio esta morto. Escreve sempre com pelo menos uma destas friccoes.

### Estrutura de genero (nao de filme)

Cada caso e autonomo. Numeracao simples: CASE-001, CASE-002...
Nao ha "temporada a salvar". Ha casos que provam hipoteses.

Mapa de territorio (cada profissao e um filao):
medicina, advocacia, engenharia, banca, seguros, logistica, construcao, educacao, ciencia, jornalismo. Cada uma tem evidencias, decisoes, responsabilidades, cadeia de custodia.

Arcos maiores possiveis (quando o genero amadurecer):
- **Bloco 1 — Crimes da Era Digital** (casos individuais)
- **Bloco 2 — Geopolitica** (sistemas inteiros: energia, contratos, defesa civil)
- **Bloco 3 — Memoria** (o mais filosofico: quem escreveu, quem autorizou, quem sabia, o que foi alterado)

---

# CAMADA 2 — A TESE + AS SEIS CONQUISTAS

## A Tese Central (congelada)

> "A vitima nao resolve o caso porque deixou uma mensagem dramatica ou previu a morte. Resolve-o porque viveu. Filmou. Registou. Existiu. E a verdade permaneceu preservada."

A tecnologia deixa de ser software policial. Passa a ser o escudo que protegeu a ultima memoria viva contra a maquina de apagar rastos.

Frase-chave do genero (sentida, nunca dita em voz alta):
> **"A prova nao mente. A prova apenas espera."**

## As Seis Conquistas (o que ja sabemos que funciona)

Estas seis valem mais do que qualquer render individual. Sao lei de trabalho.

1. **O tema funciona.** Vitima regista fragmentos -> tornam-se prova -> investigacao reconstroi -> a prova digital derrota a narrativa do acusado.

2. **Profiling, nao dramatizacao.** O crime nao e mostrado. E reconstruido. Isto afasta a obra do espetaculo da violencia e aproxima-a do drama judicial serio. O publico nunca ve a vulnerabilidade da vitima explorada como espetaculo — ve a montagem meticulosa da verdade.

3. **Os limites do gerador sao conhecidos.** Fala -> pos-producao. Texto -> pos-producao. Interface do Ledger -> pos-producao. Veiculos/props -> melhor por referencia visual. Continuidade facial -> nao se resolve por prompt.

4. **Referencias visuais para objetos funcionam.** Props e veiculos ancoram-se a imagens, nao a descricoes textuais (resolve anomalias como carros de policia errados).

5. **Fala, texto e UI pertencem a pos-producao.** O gerador de video so simula fisica e movimento. Tudo o resto e composicao posterior (SVG, TTS, lip-sync).

6. **Personagem = ancora visual, nao prompt gigante.** A audiencia segue a Elisa porque entende quem ela e, nao porque o nariz dela e identico em todos os planos.

---

# CAMADA 3 — A METODOLOGIA (ferramentas, ao servico do caso)

## Postura sobre continuidade facial: ANCHORS LEVES

A norma e identidade reconhecivel, sem perfeccionismo. A continuidade facial absoluta nao e a fundacao — e uma ferramenta opcional.

Regra de decisao:
- **Por defeito:** anchor leve. A audiencia segue quem a personagem e.
- **Liga o Tri-Phased completo SO quando:** o rosto E a prova num plano especifico (ex: reconhecimento, identificacao, o detalhe facial carrega a revelacao).

Nunca gastes energia a perseguir continuidade que o publico nao precisa. Essa e a armadilha que drenou "O Peso do Eco".

## A separacao de camadas (sempre)

O gerador de video tem UMA responsabilidade: fisica e movimento. E tudo.

| Camada | Onde se resolve |
|--------|-----------------|
| Movimento, fisica, atmosfera | Gerador de video |
| Rosto/identidade | Image-anchor (leve por defeito) |
| Props e veiculos | Referencia visual ancorada |
| Fala / dialogo | Pos-producao (TTS / voz + lip-sync) |
| Texto, UI, interface do Ledger | Pos-producao (overlay SVG) |
| Som, ritmo, transicoes | Montagem |

Prompt de video limpo = so acao cinetica. Tudo o resto vem de uma gaveta separada.

## Tri-Phased (disponivel, nao obrigatorio)

Quando um caso pedir rigor visual, as tres gavetas isoladas estao prontas:
- **Casting Locker** — ancoras faciais estaticas em HD
- **Locations & Props Locker** — placas, livery, topografia reais ancoradas
- **Action Render Locker** — prompts minimos de movimento, injecao no primeiro frame

Mas lembra-te da ordem sagrada: isto e a garagem. So desces ca quando o caso precisa.

## Integracao com SPINE-001

Este genero opera SOBRE o subsistema constitucional W-HIOS-CINEMATIC-SPINE-001:
- **CHARACTER_STATE** (B1) -> os canons dos personagens
- **WORLD_STATE** (B2) -> CONTINUITY-BIBLE + WORLD-STATE instance
- **ACTION_CHAIN** (B3) -> deltas narrativos autorizados
- **DRIFT_VALIDATOR** (B4) -> medicoes forenses
- **CINEMATIC_RECEIPT** (B5) -> selo no Ledger

A diferenca: SPINE e a infraestrutura constitucional (como). Este documento e a visao criativa (porque e o que).

---

# CASE-001 — "O PESO DO ECO"

**Estatuto:** Laboratorio. Nao o centro do universo. O primeiro experimento.
**Localizacao:** `/home/windi/hios/cinema/obras/o-peso-do-eco/`

Nao precisa de ser perfeito. Precisa de provar uma hipotese:
> *Consegue-se reconstruir a verdade atraves de evidencia preservada — sem dramatizar o crime, sem perseguir continuidade de Hollywood?*

Se provar isso, o genero esta validado e CASE-002 nasce mais forte.

### Ativos ja existentes (herdados)

| Ativo | Ficheiro | Estado |
|-------|----------|--------|
| CONTINUITY-BIBLE | `production/CONTINUITY-BIBLE-001.yaml` | SEALED com §293 refs |
| WORLD-STATE | `production/WORLD-STATE-001.instance.yaml` | SEALED |
| Elisa v2 | `canons/ELISA-v2-CHARACTER-STATE.md` | SEALED |
| Helena v1 | `canons/HELENA-v1-CHARACTER-STATE.md` | existe |
| Hartmann v2b | `canons/HARTMANN-v2b-CHARACTER-STATE.md` | FORENSIC anchor |
| Marcus v1 | `canons/MARCUS-v1-CHARACTER-STATE.md` | existe |
| Thomas v1 | `canons/THOMAS-v1-CHARACTER-STATE.md` | existe |
| S14-S21 medidas | `_forense/obra2-v2/` | BASELINE congelado |

### O guiao como teste das regras

Le-o atraves destas lentes:
- A ausencia forense do crime (S02) — testa a Conquista 2.
- O carro de Marcus ao fundo do video (S01/S16) — testa props por referencia (Conquista 4).
- A revelacao por hash, nao por HD (S14-S15) — testa a regra de ouro do Ledger.
- O rosto da Helena no climax (S17) — unico candidato a Tri-Phased completo, porque ali o rosto carrega a emocao da revelacao.

---

## COMO USAR ESTA BIBLIA

- E viva. Edita-a quando um caso te ensinar algo novo.
- A ordem sagrada nao se mexe sem decisao do Human Dragon.
- Antes de cada render, pergunta: *isto serve a casa, ou estou a polir a garagem?*
- Quando a energia cair, volta a investigacao e a verdade. E ai que o genero respira.

---

## PROXIMO PASSO SUGERIDO

Escolher uma das duas vias:

**Via A — Prova minima com render existente:**
Usar os renders ja existentes (S14, S15, S16, S20, S21) para validar a tese central sem gerar nada novo. Montar um micro-demo de 2-3 minutos que prove: "a prova nao mente, a prova apenas espera."

**Via B — Um unico render novo como teste limpo:**
Gerar S16 (o carro de Marcus ao fundo) com props por referencia visual, aplicando as Conquistas 3-4-5. Um so plano, metodologia limpa, antes de escalar.

Human Dragon decide.

---

*Liga IA+H, WINDI Publishing House, Forensic Ledger Files*
*Documento de genese vivo — nao selado, feito para crescer*
