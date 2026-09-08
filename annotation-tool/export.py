"""Build the final dataset JSON per docs/02 §Schema dữ liệu đề xuất, and assign
train/val/test splits by document. Pure functions (take a Session, return data)
so this is reusable from the Tuần 5 freeze script and unit-testable.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import shutil
import zipfile

from sqlalchemy import select
from sqlalchemy.orm import Session

from constants import SPLITS
from models import Chart, Document, Question

EXPORT_ELIGIBLE_STATUSES = {"active"}

ANNOTATION_ROOT = Path(__file__).resolve().parent
DEFAULT_IMAGES_DIR = ANNOTATION_ROOT / "data" / "images"


def assign_splits(session: Session, ratios: tuple[float, float, float] = (0.77, 0.10, 0.13), seed: int = 42) -> int:
    """Assigns split to documents that don't have one yet. Returns count assigned.
    Deterministic given `seed` — re-running is a no-op for already-split documents.
    """
    docs = session.scalars(select(Document).where(Document.split.is_(None)).order_by(Document.id)).all()
    if not docs:
        return 0
    rng = random.Random(seed)
    order = list(docs)
    rng.shuffle(order)
    n = len(order)
    n_train = round(n * ratios[0])
    n_val = round(n * ratios[1])
    for i, doc in enumerate(order):
        if i < n_train:
            doc.split = "train"
        elif i < n_train + n_val:
            doc.split = "val"
        else:
            doc.split = "test"
    return n


def normalize_image_path(raw_path: str | None) -> str:
    """Normalize internal image path (e.g. 'data/images/{hash}.png' or 'data\\images\\{hash}.png')
    to relative export path 'images/{hash}.png'.
    """
    if not raw_path:
        return ""
    cleaned = str(raw_path).strip()
    if not cleaned:
        return ""
    filename = Path(cleaned).name.strip()
    return f"images/{filename}" if filename else ""


def _export_document(doc: Document) -> dict | None:
    charts = sorted(doc.charts, key=lambda c: c.chart_id)
    chart_label_by_id = {c.id: c.chart_id for c in charts}

    eligible_questions = [q for q in doc.questions if q.status in EXPORT_ELIGIBLE_STATUSES]
    if not eligible_questions:
        return None

    eligible_questions = sorted(eligible_questions, key=lambda q: q.id)
    local_label_by_qid = {q.id: f"q{i + 1}" for i, q in enumerate(eligible_questions)}

    qa = []
    for q in eligible_questions:
        evidence = [
            {
                "hop": e.hop_order,
                "source": e.source,
                **({"chart_id": chart_label_by_id.get(e.chart_id)} if e.source == "chart" else {}),
                **({"description": e.description} if e.source == "chart" else {}),
                **({"quote": e.quote} if e.source == "text" else {}),
            }
            for e in sorted(q.evidence, key=lambda e: e.hop_order)
        ]
        qa.append(
            {
                "id": local_label_by_qid[q.id],
                "question": q.question_text,
                "answer": q.answer,
                "equivalent_answers": q.equivalent_answers or [],
                "answer_type": q.answer_type,
                "question_type": q.question_type,
                "hop_type": q.hop_type,
                "derivation": q.derivation or "",
                "choices": q.choices,
                "evidence": evidence,
            }
        )

    return {
        "id": f"vichartqa_{doc.source_domain}_{doc.id:05d}",
        "title": doc.title,
        "body_text": doc.body_text,
        "source": {
            "provider": doc.source_provider,
            "domain": doc.source_domain,
            "url": doc.source_url,
            "accessed_date": doc.source_accessed_date,
        },
        "charts": [
            {
                "chart_id": c.chart_id,
                "image": normalize_image_path(c.image_path),
                "chart_type": c.chart_type,
            }
            for c in charts
        ],
        "qa": qa,
        "split": doc.split,
    }


def build_dataset(session: Session, require_split: bool = True) -> list[dict]:
    """Returns one dict per document (docs/02 schema), skipping documents with no
    export-eligible question. If `require_split`, documents without a split are
    skipped too (use assign_splits() first for a real export)."""
    query = select(Document)
    if require_split:
        query = query.where(Document.split.isnot(None))
    docs = session.scalars(query.order_by(Document.id)).all()

    out = []
    for doc in docs:
        record = _export_document(doc)
        if record is not None:
            out.append(record)
    return out


def resolve_image_file(raw_path: str, images_dir: Path | str | None = None) -> Path | None:
    """Find the physical image file on disk given a raw DB image path.
    Checks images_dir, annotation-tool root, direct path, and subdirectories.
    Returns Path if file exists, else None.
    """
    if not raw_path:
        return None
    cleaned = str(raw_path).strip()
    if not cleaned:
        return None

    base_dir = Path(images_dir) if images_dir is not None else DEFAULT_IMAGES_DIR
    filename = Path(cleaned).name.strip()
    if not filename:
        return None

    # Check 1: inside images_dir (by filename)
    p1 = base_dir / filename
    if p1.is_file():
        return p1

    # Check 2: relative to annotation root (e.g. raw_path is 'data/images/...')
    annotation_root = (
        base_dir.parent.parent
        if base_dir.name == "images" and base_dir.parent.name == "data"
        else ANNOTATION_ROOT
    )
    p2 = annotation_root / cleaned
    if p2.is_file():
        return p2

    # Check 3: raw_path directly as path (e.g. absolute)
    try:
        p3 = Path(cleaned)
        if p3.is_file():
            return p3
    except Exception:
        pass

    # Check 4: base_dir / raw_path
    try:
        p4 = base_dir / cleaned
        if p4.is_file():
            return p4
    except Exception:
        pass

    # Check 5: search inside subdirectories of base_dir if filename exists there
    try:
        if base_dir.is_dir():
            found = next(base_dir.rglob(filename), None)
            if found is not None and found.is_file():
                return found
    except Exception:
        pass

    return None


def get_export_manifest(
    session: Session | None = None,
    dataset: list[dict] | None = None,
    require_split: bool = True,
    images_dir: Path | str | None = None,
) -> dict:
    """Collects export dataset, maps unique image assets, checks file integrity,
    and computes packaging metrics.
    """
    if dataset is None:
        if session is None:
            raise ValueError("Either session or dataset must be provided.")
        dataset = build_dataset(session, require_split=require_split)

    images: dict[str, Path] = {}
    missing_images: list[str] = []
    seen_missing: set[str] = set()

    for doc in dataset:
        for chart in doc.get("charts", []):
            img_rel = chart.get("image", "")
            if not img_rel:
                continue
            filename = Path(str(img_rel).strip()).name.strip()
            if not filename:
                continue
            archive_key = f"images/{filename}"

            if archive_key in images or archive_key in seen_missing:
                continue

            disk_path = resolve_image_file(img_rel, images_dir=images_dir)
            if disk_path is not None:
                images[archive_key] = disk_path
            else:
                seen_missing.add(archive_key)
                missing_images.append(archive_key)

    def _safe_size(p: Path) -> int:
        try:
            return p.stat().st_size
        except OSError:
            return 0

    total_image_bytes = sum(_safe_size(p) for p in images.values())
    num_questions = sum(len(d.get("qa", [])) for d in dataset)

    return {
        "dataset": dataset,
        "num_documents": len(dataset),
        "num_questions": num_questions,
        "images": images,
        "missing_images": missing_images,
        "unique_image_count": len(images),
        "total_image_bytes": total_image_bytes,
    }


def export_to_directory(
    output_dir: Path | str,
    session: Session | None = None,
    dataset: list[dict] | None = None,
    manifest: dict | None = None,
    require_split: bool = True,
    images_dir: Path | str | None = None,
) -> dict:
    """Export the complete dataset package (vichartqa.json + images/) to a local directory.
    Creates:
      output_dir/
      ├── vichartqa.json
      └── images/
          └── ...
    """
    out_path = Path(str(output_dir).strip())
    out_path.mkdir(parents=True, exist_ok=True)

    if manifest is None:
        manifest = get_export_manifest(
            session=session,
            dataset=dataset,
            require_split=require_split,
            images_dir=images_dir,
        )

    # 1. Write vichartqa.json
    json_path = out_path / "vichartqa.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest["dataset"], f, ensure_ascii=False, indent=2)

    # 2. Copy images
    images_dest_dir = out_path / "images"
    images_dest_dir.mkdir(parents=True, exist_ok=True)

    copy_errors: list[str] = []
    for archive_rel_path, src_path in manifest["images"].items():
        dest_path = images_dest_dir / Path(archive_rel_path).name
        try:
            if src_path.resolve() != dest_path.resolve():
                shutil.copy2(src_path, dest_path)
        except OSError as e:
            copy_errors.append(f"{archive_rel_path}: {e}")

    manifest["output_dir"] = str(out_path)
    manifest["json_path"] = str(json_path)
    manifest["images_dir"] = str(images_dest_dir)
    manifest["copy_errors"] = copy_errors
    return manifest


def export_to_zip(
    zip_path: Path | str,
    session: Session | None = None,
    dataset: list[dict] | None = None,
    manifest: dict | None = None,
    require_split: bool = True,
    images_dir: Path | str | None = None,
    root_dir_name: str = "vichartqa_export",
) -> dict:
    """Pack dataset into a self-contained ZIP file using disk-backed streaming.
    Package layout inside zip:
      {root_dir_name}/
      ├── vichartqa.json
      └── images/
          └── ...
    """
    dest_zip = Path(str(zip_path).strip())
    dest_zip.parent.mkdir(parents=True, exist_ok=True)

    if manifest is None:
        manifest = get_export_manifest(
            session=session,
            dataset=dataset,
            require_split=require_split,
            images_dir=images_dir,
        )

    prefix = f"{root_dir_name}/" if root_dir_name else ""

    zip_errors: list[str] = []
    with zipfile.ZipFile(dest_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Write vichartqa.json
        json_data = json.dumps(manifest["dataset"], ensure_ascii=False, indent=2).encode("utf-8")
        zf.writestr(f"{prefix}vichartqa.json", json_data)

        # Write images
        for archive_rel_path, src_path in manifest["images"].items():
            arcname = f"{prefix}{archive_rel_path}"
            try:
                zf.write(src_path, arcname=arcname)
            except OSError as e:
                zip_errors.append(f"{archive_rel_path}: {e}")

    manifest["zip_path"] = str(dest_zip)
    manifest["zip_bytes"] = dest_zip.stat().st_size
    manifest["zip_errors"] = zip_errors
    return manifest


def format_size(bytes_count: int | float) -> str:
    """Format bytes into human-readable string (B, KB, MB, GB)."""
    b = float(bytes_count)
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024.0 or unit == "GB":
            return f"{b:.1f} {unit}" if unit != "B" else f"{int(b)} B"
        b /= 1024.0
    return f"{b:.1f} GB"
