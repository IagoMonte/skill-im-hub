#!/usr/bin/env python3
"""Valida a pasta im-hub/ de um repositório contra o contrato v1.

Uso: python3 validate.py [caminho-do-repo-ou-da-pasta-im-hub]
Saída: lista de ERROS (bloqueiam a importação) e AVISOS (não bloqueiam).
Código de saída: 0 sem erros, 1 com erros, 2 uso incorreto.
Só biblioteca padrão. O schema (../schema/spec.schema.json) é a fonte única das regras de formato.
"""
import json
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE.parent / "schema" / "spec.schema.json").read_text())

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_DOC_BYTES = 200 * 1024
THUMB_SIZE = (1200, 630)
PLACEHOLDER_BRACKET = re.compile(r"\[[A-ZÀ-Ú][A-ZÀ-Ú0-9 _\-—/]{2,}\]")
PLACEHOLDER_WORDS = re.compile(r"\bTODO\b|\bLorem ipsum\b|\bFIXME\b", re.I)
FORMATS = {  # formato -> (largura, altura) de referência, tolerância de 5%
    "desktop": (1440, 900), "mobile": (390, 844), "tablet": (1024, 768),
    "wide": (1920, 820), "square": (1080, 1080),
}


# ---------- mini validador de JSON Schema (só as palavras-chave que o schema usa) ----------
def resolve(ref):
    node = SCHEMA
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def check(value, schema, path, errors):
    if "$ref" in schema:
        return check(value, resolve(schema["$ref"]), path, errors)
    for sub in schema.get("allOf", []):
        check(value, sub, path, errors)
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: deve ser {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} fora de {schema['enum']}")
    t = schema.get("type")
    kinds = {"object": dict, "array": list, "string": str}
    if t in kinds and not isinstance(value, kinds[t]):
        errors.append(f"{path}: esperado {t}")
        return
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: vazio ou curto demais")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: {len(value)} caracteres (máx. {schema['maxLength']})")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: formato inválido ({value!r})")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: mínimo de {schema['minItems']} item(ns)")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: máximo de {schema['maxItems']} item(ns)")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errors.append(f"{path}: itens repetidos")
        for i, item in enumerate(value):
            if "items" in schema:
                check(item, schema["items"], f"{path}[{i}]", errors)
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: campo obrigatório ausente")
        for key, val in value.items():
            if key in props:
                check(val, props[key], f"{path}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}.{key}: campo desconhecido")


# ---------- imagens (dimensões sem dependências) ----------
def image_size(p: Path):
    d = p.read_bytes()
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", d[16:24])
    if d[:2] == b"\xff\xd8":
        i = 2
        while i < len(d) - 9:
            if d[i] != 0xFF:
                i += 1
                continue
            marker = d[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", d[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
        kind = d[12:16]
        if kind == b"VP8X":
            return 1 + int.from_bytes(d[24:27], "little"), 1 + int.from_bytes(d[27:30], "little")
        if kind == b"VP8 ":
            w, h = struct.unpack("<HH", d[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if kind == b"VP8L":
            b = int.from_bytes(d[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    return None


def infer_format(w, h):
    for name, (fw, fh) in FORMATS.items():
        if abs(w - fw) <= fw * 0.05 and abs(h - fh) <= fh * 0.05:
            return name
    return None


# ---------- contraste (mesma fórmula WCAG do ThemeDeriver) ----------
def lum(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def safe_path(root: Path, rel: str):
    p = (root / rel).resolve()
    return p if root.resolve() in p.parents else None


def main():
    arg = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    root = arg if arg.name == "im-hub" else arg / "im-hub"
    errors, warns = [], []

    if not root.is_dir():
        print(f"ERRO: pasta im-hub/ não encontrada em {arg}. Gere-a com a skill im-hub.")
        return 1
    spec_path = root / "spec.json"
    if not spec_path.is_file():
        print("ERRO: im-hub/spec.json não encontrado.")
        return 1
    try:
        spec = json.loads(spec_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERRO: spec.json não é JSON válido: {e}")
        return 1

    check(spec, SCHEMA, "spec", errors)

    # texto: sem placeholders
    def scan(node, path):
        if isinstance(node, str):
            if PLACEHOLDER_BRACKET.search(node) or PLACEHOLDER_WORDS.search(node):
                errors.append(f"{path}: placeholder/TODO não é permitido ({node[:40]!r})")
        elif isinstance(node, dict):
            for k, v in node.items():
                scan(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                scan(v, f"{path}[{i}]")
    scan(spec, "spec")

    # arquivos referenciados
    def need_file(rel, label, max_bytes):
        p = safe_path(root, rel) if isinstance(rel, str) else None
        if p is None:
            errors.append(f"{label}: caminho inválido ({rel!r})")
            return None
        if not p.is_file():
            errors.append(f"{label}: arquivo não existe em im-hub/{rel}")
            return None
        if p.stat().st_size > max_bytes:
            errors.append(f"{label}: {p.stat().st_size // 1024} KB (máx. {max_bytes // 1024} KB)")
        return p

    thumb = spec.get("thumbnail")
    if isinstance(thumb, str):
        p = need_file(thumb, "thumbnail", MAX_IMAGE_BYTES)
        if p:
            size = image_size(p)
            if size is None:
                errors.append("thumbnail: não consegui ler as dimensões (PNG/JPG/WebP válido?)")
            elif size != THUMB_SIZE:
                errors.append(f"thumbnail: {size[0]}×{size[1]} (exigido {THUMB_SIZE[0]}×{THUMB_SIZE[1]})")

    seen_files = set()
    for i, shot in enumerate(spec.get("shots", []) if isinstance(spec.get("shots"), list) else []):
        if not isinstance(shot, dict) or "file" not in shot:
            continue
        label = f"shots[{i}]"
        if shot["file"] in seen_files:
            errors.append(f"{label}: arquivo repetido {shot['file']}")
        seen_files.add(shot["file"])
        p = need_file(shot["file"], label, MAX_IMAGE_BYTES)
        if not p:
            continue
        size = image_size(p)
        if size is None:
            errors.append(f"{label}: não consegui ler as dimensões")
            continue
        w, h = size
        if min(w, h) < 320:
            warns.append(f"{label}: {w}×{h} é pequeno; prefira capturas nítidas (≥ 320 px no menor lado)")
        declared = shot.get("format")
        inferred = infer_format(w, h)
        if declared == "terminal":
            pass
        elif declared and inferred and declared != inferred:
            errors.append(f"{label}: format={declared!r} mas {w}×{h} parece {inferred!r}")
        elif declared and not inferred:
            warns.append(f"{label}: {w}×{h} não bate com o formato {declared!r}")
        elif not declared and not inferred:
            errors.append(f"{label}: {w}×{h} não reconhecido; informe \"format\" (terminal exige explícito)")

    for i, doc in enumerate(spec.get("docs", []) if isinstance(spec.get("docs"), list) else []):
        if not isinstance(doc, dict):
            continue
        for key in ("file", "file_en"):
            if key in doc:
                p = need_file(doc[key], f"docs[{i}].{key}", MAX_DOC_BYTES)
                text = p.read_text(errors="replace") if p else ""
                if p and not text.strip():
                    errors.append(f"docs[{i}].{key}: arquivo vazio")
                if p and (PLACEHOLDER_BRACKET.search(text) or PLACEHOLDER_WORDS.search(text)):
                    errors.append(f"docs[{i}].{key}: contém placeholder/TODO")

    # cores
    def colors_ok(cols, label):
        if not isinstance(cols, list) or not cols:
            return
        if len(cols) >= 2 and re.fullmatch(r"#[0-9a-fA-F]{6}", cols[0]) and re.fullmatch(r"#[0-9a-fA-F]{6}", cols[1]):
            ratio = contrast(cols[0], cols[1])
            if ratio < 3.2:
                warns.append(f"{label}: principal × fundo com contraste {ratio:.1f}:1 (<3,2); o site ajusta o texto, mas o brilho fica fraco")
    colors_ok((spec.get("category") or {}).get("colors"), "category.colors")
    colors_ok(spec.get("colors"), "colors")

    # arquivos soltos em im-hub/ que o importador ignora
    known = {"spec.json", spec.get("thumbnail")}
    known |= {s.get("file") for s in spec.get("shots", []) if isinstance(s, dict)}
    for d in spec.get("docs", []) if isinstance(spec.get("docs"), list) else []:
        if isinstance(d, dict):
            known |= {d.get("file"), d.get("file_en")}
    for f in sorted(root.rglob("*")):
        if f.is_file() and str(f.relative_to(root)) not in known:
            warns.append(f"im-hub/{f.relative_to(root)}: não referenciado no spec (será ignorado)")

    for e in errors:
        print("ERRO:", e)
    for w in warns:
        print("AVISO:", w)
    print(f"\n{len(errors)} erro(s), {len(warns)} aviso(s) — " + ("PRONTO PARA IMPORTAR" if not errors else "NÃO importa até corrigir"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
