# skill-im-hub

Skill `im-hub` para Claude / OpenCode: gera, atualiza e audita a pasta `im-hub/` que o IM Hub importa por link.

## O que é

O IM Hub importa um projeto lendo **apenas** `im-hub/` na raiz do repositório (`spec.json`, `thumbnail`, `shots/`, `docs/`). Esta skill descreve como descobrir os dados do projeto, gerar essa pasta e validá-la sem inventar dados.

## Estrutura

```
.
├── SKILL.md              # instrução da skill (ponto de entrada)
├── references/spec.md    # contrato im-hub/ v1 (layout, campos, cores, importação)
├── schema/spec.schema.json
├── scripts/validate.py   # validador (só biblioteca padrão)
└── examples/spec.example.json
```

## Uso

No Claude Code / OpenCode com skills habilitadas, peça:

- "gerar o im-hub"
- "preparar o projeto para o portfólio/IM Hub"
- "importar este projeto no hub"

Ou valide manualmente:

```bash
python3 scripts/validate.py /caminho/do/repo
```

Saída `PRONTO PARA IMPORTAR` = pode importar. `NÃO pronto` = corrija os ERROS listados.

## Instalação

Copie esta pasta para o diretório de skills:

- Claude: `~/.claude/skills/im-hub/`
- OpenCode: `~/.config/opencode/skills/im-hub/`

## Origem

Extraída do projeto IM Hub (portfólio de Iago Monte). Contém **somente** a skill — sem o código do Hub.
