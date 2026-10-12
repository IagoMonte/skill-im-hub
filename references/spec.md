# Contrato `im-hub/` v1

Fonte de verdade da importação do IM Hub. O importador lê **somente** a pasta `im-hub/` na raiz do repositório (na branch do link; sem `/tree/<branch>` no link = `main`). Nada fora dela é lido: nem README da raiz, nem `docs/` do projeto, nem topics. Regras de formato: `../schema/spec.schema.json` (fonte única). Verificação: `python3 scripts/validate.py <repo>`.

## 1. Layout

```
<raiz-do-repo>/
└── im-hub/
    ├── spec.json                  # obrigatório — todos os dados (ver §2)
    ├── thumbnail.png|jpg|webp     # obrigatório — capa 1200×630
    ├── shots/                     # obrigatório — 1 a 12 prints
    │   ├── 01-dashboard.png       #   nome: NN-slug.ext (ordem = ordem de exibição)
    │   └── 02-cotacao-mobile.png
    └── docs/                      # obrigatório — 1 a 8 documentos markdown
        ├── readme.md              #   aba "README"
        ├── readme.en.md           #   (opcional) versão EN referenciada em file_en
        ├── arquitetura.md
        └── changelog.md
```

Arquivos dentro de `im-hub/` que o spec não referencia são **ignorados** (o validador avisa). Caminhos no spec são sempre relativos a `im-hub/`, sem `..`.

## 2. `spec.json`

Textos traduzíveis são objetos `{ "pt": "...", "en": "..." }`: `pt` obrigatório, `en` opcional (sem `en`, o site cai no PT; o admin oferece "Gerar EN"). Nenhum campo aceita placeholder (`[SEU ...]`, `TODO`, `FIXME`, `Lorem ipsum`) — **o que não for sabido, não entra: pergunte ao dono**.

| Campo | Obrig. | Regra |
| --- | --- | --- |
| `version` | sim | sempre `1` |
| `slug` | sim | kebab-case ≤80; identifica o projeto no site (`/projetos/{slug}`) e no upsert |
| `title` | sim | i18n, ≤80 |
| `summary` | sim | i18n, ≤280; o problema que resolve, em 1–2 frases, sem adjetivo vazio |
| `status` | sim | `live` (em produção/usável), `dev` (em desenvolvimento), `archived` |
| `category` | sim | objeto: `slug` (kebab ≤40), `name` (i18n ≤40), `tagline` (i18n ≤160), `colors` (§3), `fx` (§3) |
| `colors` | não | override do projeto (1–4 hex); ausente = herda da categoria |
| `fx` | não | override do efeito; ausente = herda da categoria |
| `stack` | sim | 1–12 tecnologias, caixa do design (ex. Laravel, SQL Server), sem repetir |
| `facts` | sim | `role` (i18n ≤80), `period` `{start:"AAAA-MM", end:"AAAA-MM"\|"atual"}`, `context` (i18n ≤80: "projeto de trabalho", "projeto pessoal", "faculdade"…) |
| `links` | sim | 1–10 de `{kind, url, label?}`; `url` sempre `https://`; `kind` ∈ `case demo video repo roadmap site docs play view benchmark dotfiles build_log` |
| `thumbnail` | sim | `thumbnail.png\|jpg\|jpeg\|webp` (§4) |
| `shots` | sim | 1–12 de `{file, caption, format?}` (§4) |
| `docs` | sim | 1–8 de `{name, file, file_en?}`; `name` ≤30 vira a aba; `file` em `docs/*.md` |

Não existe `visible`, `order` nem `featured`: **publicar e ordenar é decisão do admin** (revisão obrigatória).

### Categoria vem do spec
`category.slug` identifica a categoria no site. Se ela já existe no IM Hub, o projeto entra nela e os dados da categoria **não** são sobrescritos pelo spec (a categoria é do admin). Se não existe, é criada com `name`, `tagline`, `colors` e `fx` do spec. Por isso **repita exatamente os mesmos dados da categoria em todos os projetos dela**; diferença é reportada na revisão.

## 3. Cores e efeito

- `colors`: 1 a 4 hex `#RRGGBB` **nesta ordem**: 1ª **principal** (a cor que identifica o produto/categoria), 2ª **fundo** (cor de fundo do app/atmosfera), 3ª e 4ª **acentos** (opcionais). O resto (texto, superfícies, versões com contraste) é calculado pelo site.
- Como escolher (nessa prioridade):
  1. Cores de marca/tema do próprio projeto: `tailwind.config.*`, `theme.*`, variáveis CSS (`:root`/`--primary`), `colors` do Filament/Vuetify/Material, logo SVG.
  2. Cores dominantes dos prints (fundo = a mais frequente; principal = a mais saturada).
  3. Se a categoria já tem cores (consulte as outras `spec.json` ou pergunte), **não invente cores novas por projeto**: omita `colors` e herde.
- A principal precisa ter contraste ≥3,2:1 com o fundo para brilhar; abaixo disso o validador avisa.
- `fx` ∈ `grid` (padrão técnico/gestão), `pipeline` (automação/fluxos), `circuit` (hardware/IoT), `network` (ia/redes), `tiling` (sistema operacional/ambiente), `glitch` (jogos/entretenimento). Escolha pelo assunto, não por gosto.
- Categorias em uso no IM Hub (reutilize antes de criar): gestão, automação, hardware, ia, sistema operacional, entretenimento.

## 4. Imagens — onde e como

| Arquivo | Onde | Tamanho exigido | Notas |
| --- | --- | --- | --- |
| **Thumbnail** (capa de card, OG) | `im-hub/thumbnail.<ext>` | **1200×630 exato** | produto real ou composição limpa; legível em 300 px de largura; sem texto miúdo; preferir tema escuro |
| **Print** | `im-hub/shots/NN-slug.<ext>` | `desktop` 1440×900 · `mobile` 390×844 · `tablet` 1024×768 · `wide` 1920×820 · `square` 1080×1080 · `terminal` livre (≥ 800 px de largura) | tolerância de 5%; `format` é inferido pelas dimensões, **exceto `terminal`, que deve ser declarado** |

Regras: PNG/JPG/WebP; **≤10 MB** cada; **máx. 12** prints; nomes `NN-slug` em ordem de exibição; primeiro print = o mais representativo; prints no **tema escuro** quando o app tiver; `caption` descreve a tela ("dashboard de cotações"), nunca "print 1".
**Privacidade:** nada de dados reais de clientes, e-mails, tokens, URLs internas ou chaves — borre ou use dados de exemplo (projetos de uso interno: dizer isso em `docs`).

## 5. Documentos

Markdown em `im-hub/docs/`, ≤200 KB cada, ≤8. Sugeridos: `readme.md` (visão geral, problema, o que foi construído, como rodar, próximos passos), `arquitetura.md` (stack, diagrama, decisões), `changelog.md`. Imagens dentro do markdown: caminho relativo a `im-hub/` (ex.: `![fluxo](../shots/03-fluxo.png)` ou `docs/img/fluxo.png`) — serão copiadas; URLs externas só de `https://` e **não** são baixadas (viram texto/link). HTML cru e `<script>` são removidos na renderização. Blocos permitidos: títulos, parágrafo, listas, imagem, código com linguagem, citação/nota, tabela.

## 6. Importação (o que o IM Hub faz)

1. Você cola um **link**: `https://github.com/owner/repo` (branch `main`) ou `.../tree/<branch>` (branch pode ter `/`). Repositório privado: o PAT configurado nas Configurações do IM Hub é usado.
2. Sem `im-hub/spec.json` na branch: **erro** "faltou o im-hub — gere com a skill im-hub" e nada é gravado.
3. `spec.json` inválido ou arquivo referenciado ausente: **erro por campo**, nada é gravado.
4. Válido: cria o projeto (ou atualiza o de mesmo `slug`), cria a categoria se faltar, baixa thumbnail/prints/docs para o storage local (sem hotlink) e coloca tudo **aguardando revisão** — nunca publica sozinho. Em projeto já publicado, a atualização fica como revisão pendente até você aprovar.
5. Re-importar é manual (mesmo link, botão "sincronizar"). Nada sincroniza sozinho.
