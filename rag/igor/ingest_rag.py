#!/usr/bin/env python3
"""
Execute:  python rag/igor/ingest_rag.py
• Remove vetor‑store antigo
• Carrega todos os .md .csv .txt em rag/igor/data
• Cria vetor‑store Chroma persistente
"""

from __future__ import annotations
import os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # raiz do projeto
sys.path.insert(0, str(ROOT))

# Evita que core.rag carregue a Chroma enquanto deletamos
os.environ["DISABLE_RAG_AUTOLOAD"] = "1"

from core.rag import RAGService  # noqa: E402

DATA_DIR   = Path(__file__).parent / "data"
PERSIST_DIR = Path(__file__).parent / "vectors"

def main() -> None:
    print("== Ingestão RAG ==")
    if PERSIST_DIR.exists():
        shutil.rmtree(PERSIST_DIR)
        print("🗑️  Vetor‑store antigo removido.")

    rag = RAGService(data_dir=DATA_DIR, persist_dir=PERSIST_DIR)
    if rag.is_available():
        st = rag.get_status()
        print(f"✅  Vetor‑store criado com {st['arquivos_vetores']} arquivos.")
    else:
        print("❌  Falha ao criar vetor‑store.")

if __name__ == "__main__":
    main()
