"""Document store for managing uploaded documents and Vector Store indexing.

Handles document upload, normalisation, metadata extraction, and indexing
into OpenAI Vector Stores for RAG-based search.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from backend import AppConfig

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "project_data.db"
DOCS_DIR = BASE_DIR / "Data" / "documents"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def ensure_document_tables() -> None:
    """Create document-related tables if they don't exist."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL,
                version TEXT,
                effective_from TEXT,
                department TEXT,
                confidentiality TEXT DEFAULT 'internal',
                file_path TEXT,
                file_name TEXT,
                file_hash TEXT,
                mime_type TEXT,
                openai_file_id TEXT,
                vector_store_id TEXT,
                vector_store_file_id TEXT,
                indexed_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mail_metadata (
                document_id INTEGER PRIMARY KEY,
                sender TEXT,
                recipients TEXT,
                sent_at TEXT,
                subject TEXT,
                thread_id TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
            """
        )
        conn.commit()


def _file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _extract_text_from_file(file_path: str) -> str:
    """Extract plain text from various file formats."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".txt" or ext == ".md":
        return path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".msg":
        try:
            import extract_msg

            msg = extract_msg.Message(str(path))
            parts = []
            if msg.subject:
                parts.append(f"Subject: {msg.subject}")
            if msg.sender:
                parts.append(f"From: {msg.sender}")
            if msg.to:
                parts.append(f"To: {msg.to}")
            if msg.date:
                parts.append(f"Date: {msg.date}")
            parts.append("")
            if msg.body:
                parts.append(msg.body)
            return "\n".join(parts)
        except Exception:
            return path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".html" or ext == ".htm":
        try:
            from bs4 import BeautifulSoup

            html = path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            return soup.get_text(separator="\n")
        except ImportError:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            return re.sub(r"<[^>]+>", " ", raw)

    if ext == ".pdf":
        try:
            import subprocess

            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        return f"[PDF file: {path.name} – text extraction requires pdftotext]"

    if ext in (".docx", ".doc"):
        return f"[Word file: {path.name} – text extraction not yet supported]"

    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_mail_metadata(file_path: str) -> dict[str, Any]:
    """Extract mail metadata from .msg files."""
    path = Path(file_path)
    if path.suffix.lower() != ".msg":
        return {}
    try:
        import extract_msg

        msg = extract_msg.Message(str(path))
        return {
            "sender": msg.sender or "",
            "recipients": msg.to or "",
            "sent_at": str(msg.date) if msg.date else "",
            "subject": msg.subject or "",
            "thread_id": "",
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# DocumentStore class
# ---------------------------------------------------------------------------

class DocumentStore:
    """Manages document lifecycle: upload → normalise → index → search."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key) if config.openai_api_key else None
        ensure_document_tables()

    # ------------------------------------------------------------------
    # Upload / register
    # ------------------------------------------------------------------

    def upload_document(
        self,
        file_storage: Any,
        source_type: str,
        title: str,
        version: str | None = None,
        effective_from: str | None = None,
        department: str | None = None,
        confidentiality: str = "internal",
    ) -> dict[str, Any]:
        """Upload and index a document from a Werkzeug FileStorage object."""
        from werkzeug.utils import secure_filename as _sec

        filename = _sec(file_storage.filename or "unknown")
        dest = DOCS_DIR / filename

        counter = 1
        while dest.exists():
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            dest = DOCS_DIR / f"{stem}_{counter}{suffix}"
            counter += 1

        file_storage.save(str(dest))
        fhash = _file_hash(str(dest))

        with sqlite3.connect(DB_PATH) as conn:
            dup = conn.execute(
                "SELECT id FROM documents WHERE file_hash = ?", (fhash,)
            ).fetchone()
            if dup:
                os.unlink(str(dest))
                return {"id": dup[0], "status": "duplicate", "message": "동일한 파일이 이미 존재합니다."}

        mime = self._guess_mime(str(dest))

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                """
                INSERT INTO documents
                    (source_type, title, version, effective_from, department,
                     confidentiality, file_path, file_name, file_hash, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_type, title, version, effective_from, department,
                    confidentiality, str(dest), filename, fhash, mime,
                ),
            )
            doc_id = cur.lastrowid
            conn.commit()

        if source_type == "email":
            mail_meta = _extract_mail_metadata(str(dest))
            if mail_meta:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO mail_metadata
                            (document_id, sender, recipients, sent_at, subject, thread_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            doc_id,
                            mail_meta.get("sender", ""),
                            mail_meta.get("recipients", ""),
                            mail_meta.get("sent_at", ""),
                            mail_meta.get("subject", ""),
                            mail_meta.get("thread_id", ""),
                        ),
                    )
                    conn.commit()

        indexed = self._index_to_vector_store(doc_id, str(dest), source_type, {
            "title": title,
            "source_type": source_type,
            "version": version or "",
            "effective_from": effective_from or "",
            "department": department or "",
            "confidentiality": confidentiality,
        })

        return {
            "id": doc_id,
            "status": "indexed" if indexed else "uploaded",
            "file_name": filename,
            "source_type": source_type,
            "title": title,
        }

    # ------------------------------------------------------------------
    # Vector Store indexing
    # ------------------------------------------------------------------

    def _index_to_vector_store(
        self,
        doc_id: int,
        file_path: str,
        source_type: str,
        attributes: dict[str, str],
    ) -> bool:
        """Upload file to OpenAI and add to the appropriate Vector Store."""
        if not self.client:
            return False

        vs_id = self._get_vector_store_id(source_type)
        if not vs_id:
            vs_id = self._create_vector_store(source_type)
            if not vs_id:
                return False

        try:
            with open(file_path, "rb") as f:
                uploaded = self.client.files.create(file=f, purpose="assistants")

            clean_attrs: dict[str, str | int | float | bool] = {}
            for k, v in attributes.items():
                if isinstance(v, str) and v:
                    clean_attrs[k] = v

            vs_file = self.client.vector_stores.files.create(
                vector_store_id=vs_id,
                file_id=uploaded.id,
                attributes=clean_attrs if clean_attrs else None,
            )

            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    """
                    UPDATE documents
                    SET openai_file_id = ?, vector_store_id = ?,
                        vector_store_file_id = ?, indexed_at = ?
                    WHERE id = ?
                    """,
                    (uploaded.id, vs_id, vs_file.id, datetime.now().isoformat(), doc_id),
                )
                conn.commit()

            return True

        except Exception as exc:
            print(f"[DocumentStore] Index failed for doc {doc_id}: {exc}")
            return False

    def _get_vector_store_id(self, source_type: str) -> str | None:
        """Get an existing Vector Store ID from env or DB."""
        env_map = {
            "spec": "OPENAI_VECTOR_STORE_SPEC",
            "regulation": "OPENAI_VECTOR_STORE_REG",
            "email": "OPENAI_VECTOR_STORE_EMAIL",
        }
        env_key = env_map.get(source_type, "")
        vs_id = os.environ.get(env_key, "").strip()
        if vs_id:
            return vs_id

        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT vector_store_id FROM documents WHERE source_type = ? AND vector_store_id IS NOT NULL LIMIT 1",
                (source_type,),
            ).fetchone()
            if row:
                return row[0]

        return None

    def _create_vector_store(self, source_type: str) -> str | None:
        """Create a new Vector Store for the given source type."""
        if not self.client:
            return None
        try:
            vs = self.client.vector_stores.create(
                name=f"atlassian_access_{source_type}",
            )
            print(f"[DocumentStore] Created Vector Store: {vs.id} for {source_type}")
            return vs.id
        except Exception as exc:
            print(f"[DocumentStore] Failed to create Vector Store: {exc}")
            return None

    # ------------------------------------------------------------------
    # Query / list
    # ------------------------------------------------------------------

    def list_documents(
        self, source_type: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """List uploaded documents."""
        ensure_document_tables()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if source_type:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE source_type = ? ORDER BY id DESC LIMIT ?",
                    (source_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, doc_id: int) -> dict[str, Any] | None:
        """Get a single document by ID."""
        ensure_document_tables()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def reindex_document(self, doc_id: int) -> dict[str, Any]:
        """Re-index a document into Vector Store."""
        doc = self.get_document(doc_id)
        if not doc:
            return {"error": "Document not found"}

        if doc.get("openai_file_id") and doc.get("vector_store_id"):
            try:
                self.client.vector_stores.files.delete(
                    vector_store_id=doc["vector_store_id"],
                    file_id=doc["openai_file_id"],
                )
            except Exception:
                pass
            try:
                self.client.files.delete(file_id=doc["openai_file_id"])
            except Exception:
                pass

        indexed = self._index_to_vector_store(
            doc_id, doc["file_path"], doc["source_type"],
            {
                "title": doc.get("title", ""),
                "source_type": doc.get("source_type", ""),
                "version": doc.get("version", ""),
                "effective_from": doc.get("effective_from", ""),
                "department": doc.get("department", ""),
                "confidentiality": doc.get("confidentiality", "internal"),
            },
        )
        return {"id": doc_id, "status": "reindexed" if indexed else "failed"}

    def get_vector_store_ids(self, source_types: list[str] | None = None) -> list[str]:
        """Get all known Vector Store IDs, optionally filtered by source type."""
        ensure_document_tables()
        with sqlite3.connect(DB_PATH) as conn:
            if source_types:
                placeholders = ",".join("?" for _ in source_types)
                rows = conn.execute(
                    f"SELECT DISTINCT vector_store_id FROM documents WHERE source_type IN ({placeholders}) AND vector_store_id IS NOT NULL",
                    source_types,
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT DISTINCT vector_store_id FROM documents WHERE vector_store_id IS NOT NULL"
                ).fetchall()
        return [row[0] for row in rows if row[0]]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _guess_mime(file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".htm": "text/html",
            ".msg": "application/vnd.ms-outlook",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".csv": "text/csv",
            ".json": "application/json",
        }
        return mime_map.get(ext, "application/octet-stream")
