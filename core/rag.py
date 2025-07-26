"""
Serviço RAG (Retrieval‑Augmented Generation):
• Carrega documentos (CSV, MD, TXT)
• Gera embeddings multilíngues com MiniLM
• Persiste vetor‑store com Chroma
• Fornece busca semântica e contexto concatenado
"""

from __future__ import annotations
import os    
from pathlib import Path
from typing import List, Dict, Any

# Imports tardios para evitar custo em import global
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


class RAGService:
    def __init__(self, data_dir: Path, persist_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.persist_dir = Path(persist_dir)

        print("🏗️  Inicializando RAG Service…")
        print(f"📁 Data:    {self.data_dir}")
        print(f"💾 Vetores: {self.persist_dir}")

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Diretório de dados não existe: {self.data_dir}")

        # Embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("✅  Embeddings configurados (MiniLM)")

        # Vetor‑store
        if self.persist_dir.exists() and any(self.persist_dir.iterdir()):
            print("📂  Carregando vetor‑store existente…")
            try:
                self.vector_store = Chroma(
                    persist_directory=str(self.persist_dir),
                    embedding_function=self.embeddings,
                )
                print("✅  Vetor‑store carregado")
                return
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️  Falha ao carregar vetor‑store: {exc}, recriando…")

        self._create_vector_store()

    # --------------------------------------------------------------------- #
    # Criação do vetor‑store
    # --------------------------------------------------------------------- #
    def _create_vector_store(self) -> None:
        documents = self._load_documents()
        chunks = self._split_documents(documents)

        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(self.persist_dir),
        )

        # ▶️  Persistir apenas se o método existir (compatibilidade versões)
        if hasattr(self.vector_store, "persist"):
            self.vector_store.persist()

        print(f"✅  Vetor‑store criado ({len(chunks)} chunks)")


    def _load_documents(self) -> List:
        files = list(self.data_dir.glob("*"))
        print(f"📄  Encontrados {len(files)} arquivos na pasta de dados")

        documents: List = []
        for file_path in files:
            if not file_path.is_file():
                continue

            loader_cls = CSVLoader if file_path.suffix.lower() == ".csv" else TextLoader
            loader = loader_cls(str(file_path), encoding="utf-8")
            docs = loader.load()
            documents.extend(docs)
            print(f"  • {file_path.name}: {len(docs)} docs")

        if not documents:
            raise RuntimeError("Nenhum documento válido encontrado para o RAG.")
        return documents

    @staticmethod
    def _split_documents(documents: List) -> List:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            add_start_index=True,
        )
        chunks = splitter.split_documents(documents)
        print(f"🧩  {len(chunks)} chunks gerados")
        return chunks

    # --------------------------------------------------------------------- #
    # API pública
    # --------------------------------------------------------------------- #
    def search(self, query: str, k: int = 4) -> List[str]:
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

    def get_context(self, query: str, max_chars: int = 1_500) -> str:
        results = self.vector_store.similarity_search(query, k=6)
        context_parts: list[str] = []
        curr = 0
        for doc in results:
            txt = doc.page_content.strip()
            if not txt:
                continue
            if curr + len(txt) > max_chars:
                break
            context_parts.append(txt)
            curr += len(txt)
        return "\n\n".join(context_parts)

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #
    def is_available(self) -> bool:
        return hasattr(self, "vector_store") and self.vector_store is not None

    def get_status(self) -> Dict[str, Any]:
        data_files = [f.name for f in self.data_dir.glob("*") if f.is_file()]
        vector_files = [f.name for f in self.persist_dir.glob("*")] if self.persist_dir.exists() else []
        return {
            "disponivel": self.is_available(),
            "embeddings": "MiniLM",
            "vector_store": "Chroma",
            "data_dir": str(self.data_dir),
            "persist_dir": str(self.persist_dir),
            "arquivos_dados": data_files,
            "arquivos_vetores": len(vector_files),
        }


# -----------------------------------------------------------------------------
# Instância global (somente se permitido)
# -----------------------------------------------------------------------------
if os.getenv("DISABLE_RAG_AUTOLOAD") != "1":
    DATA_DIR = Path("rag/igor/data")
    PERSIST_DIR = Path("rag/igor/vectors")
    try:
        rag_service = RAGService(data_dir=DATA_DIR, persist_dir=PERSIST_DIR)
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  Falha ao iniciar RAG global: {exc}")
        rag_service = None
else:
    # Modo ingestão – não carrega automaticamente
    rag_service = None