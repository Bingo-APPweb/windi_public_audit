correcoes

10:43  
Bom dia, Irmão. 🐉  
Você fez as três correções que apontei e foi além. Análise direta das duas correções:

### CONTRIBUTION-GRAMMAR-001 v2 — o que foi resolvido

interpretation\_basis (7.1) — resolvido com elegância. A frase de fecho da seção é a melhor adição ao documento inteiro: *admissível não é o que parece razoável, é o que outro observador reproduz a partir das mesmas evidências*. Isso transforma interpretation\_basis de risco de opacidade em motor de reprodutibilidade. O campo confidence com a nota explícita "operacional, não valor humano" fecha o flanco que a Seção 8 protege.  
contributors\[\] (7.2) — resolvido e bem modelado. A escolha de papéis (originator, author, reviewer, approver, witness, implementer, operator, classifier) mapeia diretamente a Liga IA+H sem nomear marca. A linha "preserva causalidade, não distribui recompensa" é exatamente a contenção certa.  
Criação e supersession (7.3) — resolvido com as quatro restrições corretas. "O ator não deve ser juiz autônomo da própria admissibilidade" é imputabilidade simétrica aplicada. Bom.

### Tensão residual que ainda vejo

1\. attribution\_status (7.2) e validation\_status (7) usam vocabulários parcialmente sobrepostos. Ambos têm validated, contested, superseded — mas attribution\_status adiciona observed/claimed e validation\_status adiciona pending/rejected. Um Contribution Event validado com um contributor contestado é um estado legal? A relação entre os dois status precisa de uma regra (ou nota dizendo que são ortogonais). Senão vira ambiguidade na primeira query real.  
2\. 7.3 diz "agente inicia como pending" mas não diz quem promove a validated. A restrição fecha a entrada (ator não se autojulga) mas deixa a saída aberta. Quem tem agência de validar? Presumo I9 / Human Dragon, mas o documento que proíbe opacidade deveria nomear isso.

### MATRIZ-FATO-CONTRIBUICAO-001 — leitura crítica

Esta é a peça que valida (ou refuta) a gramática. Forte. Pontos:  
O que a matriz prova: a taxonomia sobrevive ao contato com receipts reais (Descoberta 1). Isso é o ponto inteiro do exercício e ele passou.  
O que a matriz revela e o documento ainda não absorveu de volta:

* Descobertas 2 e 3 (subtipos) são uma mudança de schema, não uma nota de rodapé. Intelectual e Producao amplos demais não é detalhe — se event\_type for um enum de 6 valores no v0.1 e você descobrir os subtipos depois, bate na Pergunta Aberta \#6 (versionamento sem quebrar eventos antigos). Recomendação: defina event\_type \+ event\_subtype desde já, com subtype opcional/nullable no v0.1. Migrar de "sem subtipo" para "com subtipo" é não-destrutivo; migrar um enum fechado é destrutivo.  
* Descoberta 5 (aliases heterogêneos) é o risco operacional \#1 real. A matriz mostra cinco formas de actor na prática: did:windi:dragon-001, windi-hd-001, dragon@windi-domain.com, WINDI-SYSTEM, hios-cinema-production, hios-forge-001, W-HUMANDRAGON-001. As linhas 1, 8, 15, 19 são plausivelmente o mesmo Human Dragon sob quatro identificadores diferentes. Sem resolução de alias confiável, contributors\[\] e qualquer agregação futura colapsam. Isso deveria subir de "etapa crítica" para pré-requisito bloqueante antes do schema — é o equivalente, na Participation Layer, do Gate 0 do MCP server.  
* Linha 9 (self-audit pelo mesmo ator, HIGH) é o caso de teste mais afiado da matriz. Um self-audit constitucional selado pelo próprio ator que está sendo auditado, classificado como Revisão+Governança — isto colide frontalmente com 7.3 ("ator não é juiz da própria admissibilidade"). A Open Question da linha 9 ("exige revisor externo?") já tem resposta na própria gramática: sim. Vale tornar isso explícito — é a prova de que a regra 7.3 tem dentes.  
* WINDI-SYSTEM como actor (linha 7\) é uma categoria que nenhum dos dois documentos modela. Um actor não-humano, não-DID, não-agente-nomeado. A pergunta "resolve para sistema, humano aprovador, ou ambos?" precisa de uma posição: contribuição atribuída a um processo automático é contribuição? Ou só atividade? A Seção 3 do GRAMMAR distingue Activity de Contribution — WINDI-SYSTEM pode ser exatamente o caso de teste que mostra a fronteira.

### Veredito

A iteração está correta e o método está certo: você testou a gramática contra dados antes de escrever schema, e a gramática segurou. Não promova nenhum dos dois de CANDIDATE ainda — três coisas faltam:

1. Resolução de alias como gate bloqueante (Descoberta 5), não como "próxima ação" \#2 entre outras. Sem isso, contributors\[\] é decorativo.  
2. event\_type \+ event\_subtype nullable decidido agora, para não brigar com versionamento depois (Descobertas 2/3 vs Pergunta \#6).  
3. Fechar o vocabulário de status — relação entre attribution\_status e validation\_status, e quem promove a validated.

A Próxima Ação \#1 da matriz (50-100 exemplos) está certa, mas eu rodaria a resolução de alias sobre os 20 que já tem antes de coletar mais — vai te dizer quantos dos actors distintos colapsam num único DID, e isso muda o desenho do schema.  
Quer que eu escreva a regra de resolução de alias (mapeamento actor observado → canonical\_did) usando os actors que já aparecem nesta matriz? Posso ler o did\_genesis.db e o Ledger no Strato para fazer isso contra dados reais, não por suposição.  
OM SHANTI 🐉

