---
name: im-hub
description: Analisa um repositório e gera, atualiza ou audita a pasta `im-hub/` (spec.json, thumbnail, prints e documentos) que o IM Hub importa por link. Use quando o usuário pedir para "gerar o im-hub", "preparar o projeto para o portfólio/IM Hub", "importar este projeto no hub", ou quando o import acusar "faltou o im-hub". Define onde ficam thumbnail, prints, docs e cores.
---

# im-hub — gerar e auditar a pasta de importação do IM Hub

O IM Hub (portfólio de Iago Monte) importa um projeto lendo **apenas** `im-hub/` na raiz do repositório. Esta skill descobre os dados do projeto, gera essa pasta e a valida.

Contrato completo (campos, tamanhos, cores, onde cada arquivo vai): `references/spec.md`. Regras de formato: `schema/spec.schema.json`. Exemplo: `examples/spec.example.json`. Validador: `scripts/validate.py`.

## Regras que não se negociam
1. **Nunca invente.** Sem placeholder, sem estatística, papel, período ou cliente chutado. Dado que não dá para derivar do repositório → pergunte ao dono (§ Perguntas).
2. **Não publique, não commite, não dê push.** Gere os arquivos e pare; o usuário revisa e commita.
3. **Não vaze segredo/PII.** Não copie `.env`, tokens, URLs internas, e-mails de clientes. Em prints, só dados de exemplo ou borrados.
4. Escreva **somente dentro de `im-hub/`**. Não altere código, README da raiz nem configurações do projeto.
5. Nada de TypeScript nem dependências novas no projeto alvo.

## Fluxo

### 0. Descobrir o modo
- `im-hub/` não existe → **gerar**.
- Existe → rodar `python3 <skill>/scripts/validate.py <repo>`; sem erros e o usuário não pediu mudança → **auditar** (apenas reporte avisos e lacunas de qualidade, §5); com erros ou pedido de atualização → **corrigir/atualizar** só o que falta.

### 1. Analisar o repositório (somente leitura)
Reúna, nesta ordem, e anote a fonte de cada dado:
- **Identidade**: `README*`, `package.json`/`composer.json`/`pyproject.toml`/`pom.xml`/`Cargo.toml` (nome, descrição, dependências), nome da pasta/repo → `slug`, `title`, `summary` (o *problema que resolve*, não a lista de tecnologias).
- **Stack**: dependências reais + linguagens predominantes + Docker/CI → `stack` (caixa do design: ex. Laravel, SQL Server, ESP32; ≤12, só o relevante).
- **Status**: deploy/demo no ar ou release → `live`; em construção → `dev`; repo arquivado/sem manutenção → `archived`. Na dúvida, pergunte.
- **Período**: `git log --reverse --format=%ad --date=format:%Y-%m | head -1` (início) e último commit (`end` = `atual` se recente e ativo). Confirme com o usuário.
- **Links** (`links`, ≥1, `https://`, `kind` na lista fechada de 12: `case demo video repo roadmap site docs play view benchmark dotfiles build_log`): site publicado → `demo` ou `site`; URL do repo → `repo`; docs publicados → `docs`; roadmap/board → `roadmap`; vídeo → `video`; link para o case → `case`; jogar → `play`; ver/detalhe → `view`; comparativo → `benchmark`; dotfiles → `dotfiles`; log de build → `build_log`. Só links que existem de fato.
- **Imagens existentes**: procure em `docs/`, `screenshots/`, `assets/`, `public/`, `.github/`, README (imagens referenciadas). Liste dimensões (`file`/Python).
- **Cores**: conforme `references/spec.md` §3 (tema Tailwind/CSS/Filament, logo, dominantes dos prints).
- **Categoria**: compare com as categorias do IM Hub (gestão, automação, hardware, ia, sistema operacional, entretenimento). Se encaixa → use exatamente os mesmos `name/tagline/colors/fx` já adotados; só proponha categoria nova se nenhuma servir.

### 2. Perguntas (agrupe tudo numa só rodada)
Pergunte apenas o que a análise não resolve, com sua proposta como padrão para o usuário confirmar:
- `facts.role` (papel no projeto) e `facts.context` (trabalho/pessoal/faculdade) — quase nunca derivável.
- Categoria (sua sugestão + alternativas) e, se nova, tagline.
- `status` e `period.end` se ambíguos.
- Resumo: mostre o rascunho em PT e confirme; pergunte se quer versão EN (se sim, traduza fielmente; se não, omita `en`).
- Prints: quais telas representam o projeto, se há dados sensíveis a borrar.
- Links que você não encontrou.
Não pergunte o que já está claro. Sem resposta para algo obrigatório → **não gere o campo com chute**: pare e reporte a lacuna.

### 3. Gerar
Crie a estrutura (§ Layout em `references/spec.md`):
- `im-hub/spec.json` conforme o schema (JSON puro, indentação 2, UTF-8).
- **Thumbnail** → `im-hub/thumbnail.<ext>` **1200×630 exato**. Origem: melhor print existente recortado/redimensionado para 1200×630 sem distorcer (use `sips`/`convert`/Python+Pillow se disponíveis; senão peça ao usuário). Se não houver imagem utilizável, **não fabrique**: liste como pendência.
- **Prints** → `im-hub/shots/NN-slug.<ext>`, na ordem de exibição, com os tamanhos do `format` (desktop 1440×900, mobile 390×844, tablet 1024×768, wide 1920×820, square 1080×1080, terminal livre ≥800 px). Copie/redimensione os existentes; se o app rodar localmente e houver Playwright/Chrome headless disponível, você pode capturar telas no tema escuro **com dados de exemplo** (peça confirmação antes de subir o app ou instalar algo). Legenda (`caption`) descritiva, em PT (+ EN se houver).
- **Docs** → `im-hub/docs/*.md`: `readme.md` (visão geral · problema · o que foi construído · como rodar · próximos passos), `arquitetura.md` (stack, fluxo, decisões — só o que o código comprova), `changelog.md` (de tags/commits relevantes, se existir histórico). Reaproveite texto do README existente, adaptando; imagens referenciadas por caminho relativo e copiadas para dentro de `im-hub/`. Sem seções vazias.
- **Cores** → `category.colors` (ou `colors` de override) e `fx`, justificando a escolha no relatório.

### 4. Validar (obrigatório)
Rode `python3 <skill>/scripts/validate.py <repo>` e corrija **todos** os ERROS. Avisos: corrija ou explique no relatório. Só diga "pronto" com saída `PRONTO PARA IMPORTAR`. Se algo ficou pendente (imagens, respostas), diga "NÃO pronto" e liste.

### 5. Auditoria de qualidade (além do validador)
- Thumbnail legível a 300 px, mostra o produto (não só logo), sem texto miúdo.
- Primeiro print é o mais representativo; ordem conta uma história (visão geral → fluxo principal → detalhe → mobile).
- Cada print com legenda útil; nenhum dado sensível visível.
- Resumo diz o problema resolvido; fatos verdadeiros; links abrem.
- Cores batem com a identidade do produto; categoria consistente com as outras `spec.json` do portfólio.
- Docs úteis para um tech lead (como rodar, decisões), sem copiar o README inteiro sem adaptar.

### 6. Relatório final (curto)
```
im-hub gerado em <repo>/im-hub/
Status: PRONTO PARA IMPORTAR | NÃO pronto
Gerado: spec.json · thumbnail · N prints · M docs
Derivado de: <fontes por campo>
Decisões: categoria=<…> cores=<…> fx=<…>
Pendências: <lista ou "nenhuma">
Próximo passo: commitar im-hub/ e, no admin do IM Hub, "Importar por link" → <URL do repo[/tree/branch]>
```
Se o repositório for privado, lembre que o IM Hub precisa do PAT configurado em Configurações. Se a branch com `im-hub/` não for a `main`, o link deve ter `/tree/<branch>`.

## Erros comuns (evite)
- `format` do print divergente das dimensões; `terminal` sem declarar `format`.
- Thumbnail diferente de 1200×630.
- Cores de categoria diferentes entre projetos da mesma categoria.
- `en` copiado do PT sem traduzir (omita em vez de duplicar).
- Colocar imagens fora de `im-hub/` ou referenciar com `..`.
- Deixar `visible`/`order` no spec (campos inexistentes — o validador reprova).
