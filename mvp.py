#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import click
import requests
from rich.console import Console
from rich.table import Table

try:
    from PIL import ExifTags, Image, ImageEnhance, ImageOps, ImageFilter  # type: ignore
except Exception as e:  # pragma: no cover
    raise SystemExit(
        f"Pillow is required. Install with: pip install Pillow\nError: {e}"
    ) from e

try:
    import easyocr  # type: ignore
except Exception:
    easyocr = None  # type: ignore


console = Console()

SCHEMA_META = "snap_to_task.image_metadata.v1"
SCHEMA_AST = "snap_to_task.ast.v2"
SCHEMA_RUN_MANIFEST = "snap_to_task.run_manifest.v1"


@dataclass(frozen=True)
class Env:
    vault_path: Path
    llm_endpoint: str
    llm_model: str
    state_dir: Path
    runs_dir: Path
    ocr_langs: Tuple[str, ...] = ("en",)


# -----------------------------
# Time / ids / hashing
# -----------------------------


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def gen_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{secrets.token_hex(3)}"


def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def safe_slug(s: str) -> str:
    out: List[str] = []
    for ch in s.strip():
        if ch.isalnum() or ch in ("-", "_"):
            out.append(ch)
        elif ch.isspace():
            out.append("-")
    slug = "".join(out).strip("-")
    return slug or "note"


# -----------------------------
# Env
# -----------------------------


def load_env() -> Env:
    vault = Path(os.getenv("OBISIDIAN_VAULT_PATH", "")).expanduser()
    if not str(vault).strip():
        vault = Path.home() / "ObsidianVault"

    state_dir = Path(os.getenv("SNAP_STATE_DIR", ".snap_to_task")).expanduser()
    runs_dir = state_dir / "runs"

    llm_endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/chat")
    llm_model = os.getenv("LLM_MODEL", "qwen2.5vl:latest")

    return Env(
        vault_path=vault,
        llm_endpoint=llm_endpoint,
        llm_model=llm_model,
        state_dir=state_dir,
        runs_dir=runs_dir,
    )


# -----------------------------
# HEIC/HEIF support
# -----------------------------


def register_heif_if_available() -> None:
    try:
        import pillow_heif  # type: ignore

        pillow_heif.register_heif_opener()
    except Exception:
        return


def image_open(path: Path) -> Image.Image:
    register_heif_if_available()
    try:
        return Image.open(path)
    except Exception as e:
        msg = (
            f"Failed to open image: {path}\n"
            f"- If this is HEIC/HEIF, install: pip install pillow-heif\n"
            f"- Otherwise ensure the file is a valid image.\n"
            f"Error: {e}"
        )
        raise RuntimeError(msg) from e


def apply_exif_orientation(img: Image.Image) -> Image.Image:
    """
    Normalize orientation so OCR sees upright text.
    """
    try:
        exif = img.getexif()
        if not exif:
            return img
        orient_tag = None
        for k, v in ExifTags.TAGS.items():
            if v == "Orientation":
                orient_tag = k
                break
        if orient_tag is None:
            return img
        orientation = exif.get(orient_tag)
        if orientation == 3:
            return img.rotate(180, expand=True)
        if orientation == 6:
            return img.rotate(270, expand=True)
        if orientation == 8:
            return img.rotate(90, expand=True)
        return img
    except Exception:
        return img


def preprocess_for_ocr(img: Image.Image, max_dim: int = 2200) -> Image.Image:
    """
    Whiteboard-friendly preprocessing:
    - exif orientation
    - downscale to max_dim (keeps text legible; improves OCR stability)
    - grayscale, autocontrast, slight sharpness
    """
    img = apply_exif_orientation(img)

    w, h = img.size
    scale = min(1.0, float(max_dim) / float(max(w, h)))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))

    if img.mode != "L":
        img = img.convert("L")

    img = ImageOps.autocontrast(img)

    # gentle sharpening
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    # slight contrast bump
    img = ImageEnhance.Contrast(img).enhance(1.15)

    return img


def image_to_png_bytes(img: Image.Image) -> bytes:
    from io import BytesIO

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def detect_image_ext(p: Path) -> str:
    return p.suffix.lower().lstrip(".")


def extract_exif_pillow(img: Image.Image) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        exif = img.getexif()
        if not exif:
            return out
        for tag_id, value in exif.items():
            name = ExifTags.TAGS.get(tag_id, str(tag_id))
            try:
                json.dumps(value)
                out[name] = value
            except Exception:
                out[name] = str(value)
        dt = out.get("DateTimeOriginal") or out.get("DateTime")
        if dt:
            out["_datetime_raw"] = str(dt)
    except Exception:
        return out
    return out


# -----------------------------
# IO
# -----------------------------


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def write_bytes(path: Path, b: bytes) -> None:
    ensure_dir(path.parent)
    path.write_bytes(b)


def read_text_if_exists(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


# -----------------------------
# Run workspace + metadata
# -----------------------------


def prepare_run_workspace(env: Env, run_id: str) -> Path:
    run_dir = env.runs_dir / run_id
    ensure_dir(run_dir / "source")
    ensure_dir(run_dir / "normalized")
    ensure_dir(run_dir / "extract")
    ensure_dir(run_dir / "debug")
    return run_dir


def build_metadata(
    src_path: Path,
    src_bytes: bytes,
    normalized_png_bytes: bytes,
    img: Image.Image,
    run_id: str,
) -> Dict[str, Any]:
    src_sha = sha256_bytes(src_bytes)
    png_sha = sha256_bytes(normalized_png_bytes)
    meta: Dict[str, Any] = {
        "schema": SCHEMA_META,
        "run_id": run_id,
        "captured_at_utc": now_utc_iso(),
        "source": {
            "path": str(src_path),
            "filename": src_path.name,
            "ext": detect_image_ext(src_path),
            "bytes": len(src_bytes),
            "sha256": src_sha,
        },
        "normalized": {
            "format": "png",
            "bytes": len(normalized_png_bytes),
            "sha256": png_sha,
            "size_px": {"width": img.size[0], "height": img.size[1]},
            "mode": img.mode,
        },
        "exif": extract_exif_pillow(img),
        "tooling": {
            "snap_to_task": "mvp",
            "python": sys.version.split()[0],
        },
    }
    return meta


def normalize_to_run(env: Env, run_dir: Path, src_path: Path) -> Tuple[str, Path, Path, Path]:
    """
    Returns (content_id, source_copy_path, normalized_png_path, metadata_json_path).
    content_id is sha256(source bytes).
    """
    src_bytes = src_path.read_bytes()
    content_id = sha256_bytes(src_bytes)

    img0 = image_open(src_path)
    img = preprocess_for_ocr(img0)
    png_bytes = image_to_png_bytes(img)

    src_copy = run_dir / "source" / src_path.name
    png_path = run_dir / "normalized" / f"{content_id}.png"
    meta_path = run_dir / "metadata.json"

    write_bytes(src_copy, src_bytes)
    write_bytes(png_path, png_bytes)
    meta = build_metadata(src_path, src_bytes, png_bytes, img, run_dir.name)
    write_json(meta_path, meta)

    # Save a debug preview for inspection
    try:
        (run_dir / "debug" / f"{content_id}.preprocessed.png").write_bytes(png_bytes)
    except Exception:
        pass

    return content_id, src_copy, png_path, meta_path


# -----------------------------
# Extraction: EasyOCR + Ollama
# -----------------------------


def easyocr_extract_lines(image_path: Path, langs: Tuple[str, ...]) -> List[str]:
    if easyocr is None:
        raise RuntimeError("EasyOCR not installed. Install with: pip install easyocr")

    console.log(f"[bold]EasyOCR[/bold] reading {image_path.name} ...")
    reader = easyocr.Reader(list(langs), gpu=False)
    try:
        lines = reader.readtext(str(image_path), detail=0)
    except Exception as e:
        console.log(f"[red]EasyOCR failed:[/red] {e}")
        return []
    out: List[str] = []
    for ln in lines:
        if isinstance(ln, str):
            s = ln.strip()
            if s:
                out.append(s)
    return out


def ollama_chat(env: Env, messages: List[Dict[str, str]], timeout_s: int = 180) -> Optional[str]:
    payload = {"model": env.llm_model, "messages": messages, "stream": False}
    try:
        resp = requests.post(env.llm_endpoint, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        console.log(f"[yellow]Ollama call failed:[/yellow] {e}")
        return None

    if isinstance(data, dict):
        if isinstance(data.get("response"), str):
            return data["response"]
        msg = data.get("message")
        if isinstance(msg, dict) and isinstance(msg.get("content"), str):
            return msg["content"]
    return None


def ollama_extract_lines(env: Env, image_png_path: Path) -> List[str]:
    raw_bytes = image_png_path.read_bytes()
    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    text = ollama_chat(
        env,
        [
            {
                "role": "user",
                "content": (
                    "Extract text from this image. Return one item per line. "
                    "Prefer preserving intended words (tasks, project, due date). "
                    "No commentary."
                ),
            },
            {"role": "user", "content": b64},
        ],
        timeout_s=240,
    )
    if not text:
        return []
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


# -----------------------------
# Cleanup + quality gating
# -----------------------------


NOISE_RE = re.compile(r"^[\W_]{1,4}$")


def normalize_line(line: str) -> str:
    s = line.strip()
    s = s.replace("=>", "->")
    s = re.sub(r"\s+", " ", s)
    return s


def clean_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in lines:
        s = normalize_line(raw)
        if not s:
            continue
        if NOISE_RE.match(s):
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def ocr_quality_score(lines: List[str]) -> float:
    """
    Heuristic: score [0..1].
    High when lines look like words/sentences.
    Low when lines are mostly short glyph fragments.
    """
    if not lines:
        return 0.0
    cleaned = [normalize_line(x) for x in lines if normalize_line(x)]
    if not cleaned:
        return 0.0

    good = 0
    for ln in cleaned:
        # "good" line has >= 6 chars and at least one vowel or digit group
        if len(ln) >= 6 and (re.search(r"[aeiouAEIOU]", ln) or re.search(r"\d", ln)):
            good += 1
    return float(good) / float(len(cleaned))


# -----------------------------
# Parsing (conservative)
# -----------------------------


def heuristic_parse(lines: List[str]) -> Dict[str, Any]:
    ast: Dict[str, Any] = {
        "schema": SCHEMA_AST,
        "header": {"title": None, "project": None, "due": None},
        "projects": [],
        "tasks": [],
        "tags": [],
        "notes": [],
        "extraction": {"mode": "heuristic", "assumptions": [], "uncertain": []},
    }

    due: Optional[str] = None
    project: Optional[str] = None

    for ln in lines:
        m_due = re.search(r"\bDUE[:\s]+(\d{4}-\d{2}-\d{2})\b", ln, re.IGNORECASE)
        if m_due:
            due = m_due.group(1)

        m_proj = re.search(r"\bPROJECT[:\s]+([A-Za-z0-9_\-]+)\b", ln, re.IGNORECASE)
        if m_proj:
            project = m_proj.group(1)

        # too noisy? keep as uncertain
        if len(ln) <= 3 and not re.search(r"\d", ln):
            ast["extraction"]["uncertain"].append(ln)
            continue

        # task-ish
        if ln.startswith("- [ ]"):
            txt = ln[5:].strip()
            ast["tasks"].append({"status": "todo", "text": txt, "project": project, "due": due})
        elif ln.lower().startswith("- [x]"):
            txt = ln[5:].strip()
            ast["tasks"].append({"status": "done", "text": txt, "project": project, "due": due})
        elif ln.startswith("- "):
            ast["tasks"].append({"status": "todo", "text": ln[2:].strip(), "project": project, "due": due})
        elif ln.lower().startswith("x "):
            ast["tasks"].append({"status": "done", "text": ln[2:].strip(), "project": project, "due": due})
        else:
            # if it smells like a header token, treat as note
            if re.search(r"\b(snap|task|v\d|bundle|due|project)\b", ln, re.IGNORECASE):
                ast["notes"].append(ln)
            else:
                ast["tasks"].append({"status": "todo", "text": ln, "project": project, "due": due})

    if project:
        ast["header"]["project"] = project
        ast["projects"].append({"name": project})
    if due:
        ast["header"]["due"] = due

    return ast


def ollama_repair_and_segment(env: Env, cleaned_lines: List[str]) -> Optional[Dict[str, Any]]:
    prompt = {
        "role": "user",
        "content": (
            "Given OCR text lines from a whiteboard, produce structured JSON.\n"
            "Be conservative: do not invent missing content.\n"
            "If a line is unreadable, include it in extraction.uncertain.\n"
            "Return JSON only with this schema:\n"
            "{\n"
            '  "schema": "snap_to_task.ast.v2",\n'
            '  "header": { "title": string|null, "project": string|null, "due": "YYYY-MM-DD"|null },\n'
            '  "projects": [ { "name": string } ],\n'
            '  "tasks": [ { "status": "todo"|"done", "text": string, "project": string|null, "due": "YYYY-MM-DD"|null } ],\n'
            '  "tags": [string],\n'
            '  "notes": [string],\n'
            '  "extraction": { "mode": "ollama_repair", "assumptions": [string], "uncertain": [string] }\n'
            "}\n\n"
            "OCR lines:\n"
            + "\n".join(f"- {ln}" for ln in cleaned_lines)
        ),
    }

    text = ollama_chat(env, [prompt], timeout_s=180)
    if not text:
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    if data.get("schema") != SCHEMA_AST:
        return None
    if "tasks" not in data:
        return None
    return data


# -----------------------------
# Markdown rendering
# -----------------------------


def ast_to_obsidian_md(
    title: str,
    content_id: str,
    run_id: str,
    ast: Dict[str, Any],
    meta_path: Path,
    manifest_path: Path,
) -> str:
    header = ast.get("header") or {}
    due = header.get("due")
    project = header.get("project")
    tasks = ast.get("tasks", [])
    notes = ast.get("notes", [])
    tags = ast.get("tags", [])

    out: List[str] = []
    out.append("---")
    out.append(f"title: {title}")
    out.append(f"content_id: {content_id}")
    out.append(f"run_id: {run_id}")
    out.append(f"generated_at_utc: {now_utc_iso()}")
    out.append(f"metadata_json: {meta_path.as_posix()}")
    out.append(f"manifest_json: {manifest_path.as_posix()}")
    if project:
        out.append(f"project: {project}")
    if due:
        out.append(f"due: {due}")
    out.append("tags: [snap_to_task" + (", " + ", ".join(tags) if tags else "") + "]")
    out.append("---")
    out.append("")
    out.append("## Tasks")
    if not tasks:
        out.append("- [ ] (no tasks extracted)")
    else:
        for t in tasks:
            mark = "x" if t.get("status") == "done" else " "
            txt = (t.get("text") or "").strip()
            if txt:
                out.append(f"- [{mark}] {txt}")

    if notes:
        out.append("")
        out.append("## Notes")
        for n in notes:
            n2 = str(n).strip()
            if n2:
                out.append(f"- {n2}")

    out.append("")
    return "\n".join(out)


def print_lines_table(lines: List[str], title: str) -> None:
    table = Table(title=title)
    table.add_column("#", style="dim", justify="right")
    table.add_column("Line", style="bold")
    for i, ln in enumerate(lines, start=1):
        table.add_row(str(i), ln)
    console.print(table)


def append_note_section(existing: str, section: str) -> str:
    existing = existing.rstrip() + "\n"
    return existing + "\n" + section.strip() + "\n"


def write_vault_note(
    env: Env,
    image_stem: str,
    run_id: str,
    content_id: str,
    md: str,
    note_name: Optional[str],
    append: bool,
    overwrite: bool,
    run_dir: Path,
    manifest_path: Path,
) -> Path:
    ensure_dir(env.vault_path)

    default_name = f"{safe_slug(image_stem)}-{run_id}.md"
    vault_name = note_name or default_name
    dest = env.vault_path / vault_name
    ensure_dir(dest.parent)

    run_section = "\n".join(
        [
            f"## Run {run_id}",
            f"- content_id: `{content_id}`",
            f"- run_dir: `{run_dir.as_posix()}`",
            f"- manifest: `{manifest_path.as_posix()}`",
            "",
            md.strip(),
            "",
        ]
    )

    if append:
        if not note_name:
            raise SystemExit("--append requires --note <target>.md")
        merged = append_note_section(read_text_if_exists(dest), run_section)
        dest.write_text(merged, encoding="utf-8")
        return dest

    if dest.exists() and note_name and not overwrite:
        raise SystemExit(f"Refusing to overwrite existing note without --overwrite: {dest}")

    dest.write_text(run_section, encoding="utf-8")
    return dest


def write_run_manifest(run_dir: Path) -> Path:
    src_files = list((run_dir / "source").glob("*"))
    if not src_files:
        raise RuntimeError("run_dir has no source file")
    src_name = src_files[0].name

    normalized_files = list((run_dir / "normalized").glob("*.png"))
    if not normalized_files:
        raise RuntimeError("run_dir has no normalized png")
    norm_name = normalized_files[0].name

    extract_files = sorted((run_dir / "extract").glob("*.json"))
    extract_rel = [f"extract/{p.name}" for p in extract_files]

    content_id = sha256_file(run_dir / "source" / src_name)

    manifest = {
        "schema": SCHEMA_RUN_MANIFEST,
        "run_id": run_dir.name,
        "content_id": content_id,
        "generated_at_utc": now_utc_iso(),
        "files": {
            "source": f"source/{src_name}",
            "normalized_png": f"normalized/{norm_name}",
            "metadata_json": "metadata.json",
            "ast_json": "ast.json",
            "note_md": "note.md",
            "extract_json": extract_rel,
        },
        "hashes": {
            "source_sha256": sha256_file(run_dir / "source" / src_name),
            "normalized_png_sha256": sha256_file(run_dir / "normalized" / norm_name),
            "metadata_json_sha256": sha256_file(run_dir / "metadata.json"),
            "ast_json_sha256": sha256_file(run_dir / "ast.json"),
            "note_md_sha256": sha256_file(run_dir / "note.md"),
            **{f"extract/{p.name}_sha256": sha256_file(p) for p in extract_files},
        },
    }

    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    return manifest_path


# -----------------------------
# Input expansion (file/dir/glob)
# -----------------------------


def expand_inputs(input_arg: str) -> List[Path]:
    p = Path(input_arg)
    if p.exists() and p.is_dir():
        # directory: include common image types
        exts = {".png", ".jpg", ".jpeg", ".heic", ".heif"}
        files = [x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in exts]
        return sorted(files)
    if any(ch in input_arg for ch in ["*", "?", "["]):
        # glob pattern
        return sorted(Path(".").glob(input_arg))
    if p.exists() and p.is_file():
        return [p]
    raise FileNotFoundError(f"Input not found: {input_arg}")


# -----------------------------
# CLI
# -----------------------------


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input", type=str)
@click.option("--run-id", default=None, help="Override run id (default: auto).")
@click.option("--note", "note_name", default=None, help="Vault note filename. Default: <stem>-<run_id>.md")
@click.option("--append", is_flag=True, help="Append each run section to an existing vault note (requires --note).")
@click.option("--overwrite", is_flag=True, help="Overwrite vault note if it exists (only with --note).")
@click.option("--no-llm", is_flag=True, help="Disable Ollama usage.")
@click.option("--force-llm", is_flag=True, help="Skip OCR and force Ollama extraction.")
@click.option("--llm-repair", is_flag=True, help="Use Ollama to repair OCR + segment into structured AST JSON.")
@click.option("--min-ocr-quality", default=0.45, show_default=True, help="If OCR quality < threshold, prefer Ollama.")
def cli(
    input: str,
    run_id: Optional[str],
    note_name: Optional[str],
    append: bool,
    overwrite: bool,
    no_llm: bool,
    force_llm: bool,
    llm_repair: bool,
    min_ocr_quality: float,
) -> None:
    env = load_env()
    files = expand_inputs(input)
    if not files:
        raise SystemExit(f"No input files matched: {input}")

    console.rule("[bold]SnapToTask MVP[/bold]")
    console.log(f"Vault: {env.vault_path}")
    console.log(f"State: {env.state_dir}")
    console.log(f"Files: {len(files)}")

    for src in files:
        rid = run_id or gen_run_id()
        run_dir = prepare_run_workspace(env, rid)

        console.rule(f"[bold]{src.name}[/bold]")
        content_id, src_copy, png_path, meta_path = normalize_to_run(env, run_dir, src)
        console.log(f"run_id: {rid}")
        console.log(f"content_id: {content_id}")
        console.log(f"normalized_png: {png_path}")

        raw_easy: List[str] = []
        raw_llm: List[str] = []

        if force_llm:
            if no_llm:
                raise SystemExit("--force-llm requires Ollama (remove --no-llm).")
            raw_llm = ollama_extract_lines(env, png_path)
            write_json(run_dir / "extract" / "raw_lines.ollama.json", {"lines": raw_llm})
        else:
            raw_easy = easyocr_extract_lines(png_path, env.ocr_langs)
            write_json(run_dir / "extract" / "raw_lines.easyocr.json", {"lines": raw_easy})

        # Gate: if OCR looks bad, prefer Ollama even if OCR produced text
        if not no_llm and not force_llm:
            score = ocr_quality_score(raw_easy)
            console.log(f"OCR quality score: {score:.2f}")
            if score < float(min_ocr_quality):
                console.log("[yellow]OCR looks low-quality; using Ollama extraction.[/yellow]")
                raw_llm = ollama_extract_lines(env, png_path)
                write_json(run_dir / "extract" / "raw_lines.ollama.json", {"lines": raw_llm})

        raw = raw_llm if raw_llm else raw_easy
        if not raw:
            console.log("[red]No text extracted.[/red]")
            continue

        print_lines_table(raw, "Raw Extracted Lines")
        cleaned = clean_lines(raw)
        write_json(run_dir / "extract" / "clean_lines.json", {"lines": cleaned})
        print_lines_table(cleaned, "Cleaned Lines")

        if llm_repair and not no_llm:
            repaired = ollama_repair_and_segment(env, cleaned)
            ast = repaired if repaired else heuristic_parse(cleaned)
        else:
            ast = heuristic_parse(cleaned)

        write_json(run_dir / "ast.json", ast)

        placeholder_manifest = run_dir / "manifest.json"
        md = ast_to_obsidian_md(
            title=src.stem,
            content_id=content_id,
            run_id=rid,
            ast=ast,
            meta_path=meta_path,
            manifest_path=placeholder_manifest,
        )
        write_text(run_dir / "note.md", md)
        manifest_path = write_run_manifest(run_dir)

        # Update note.md now that manifest exists
        md = ast_to_obsidian_md(
            title=src.stem,
            content_id=content_id,
            run_id=rid,
            ast=ast,
            meta_path=meta_path,
            manifest_path=manifest_path,
        )
        write_text(run_dir / "note.md", md)

        saved = write_vault_note(
            env=env,
            image_stem=src.stem,
            run_id=rid,
            content_id=content_id,
            md=md,
            note_name=note_name,
            append=append,
            overwrite=overwrite,
            run_dir=run_dir,
            manifest_path=manifest_path,
        )
        console.log(f"[green]Wrote vault note:[/green] {saved}")
        console.log(f"[green]Run directory:[/green] {run_dir}")


if __name__ == "__main__":
    cli()
