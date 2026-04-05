import json
import os
import logging
import textstat
from app.config import settings

logger = logging.getLogger(__name__)

_llama_available = False
_langchain_available = False

try:
    from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings as LlamaSettings
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.openai import OpenAIEmbedding
    import chromadb
    _llama_available = True
except ImportError:
    logger.warning("llama-index not installed, using fallback")

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    _langchain_available = True
except ImportError:
    logger.warning("langchain not installed, using fallback")


class RAGService:
    def __init__(self):
        self.index = None
        self.fallback_kb = {}
        self.ready = False
        self._load_kb()

    def _load_kb(self):
        kb_path = os.path.join(settings.data_dir, "knowledge_base.json")
        try:
            with open(kb_path) as f:
                entries = json.load(f)
        except FileNotFoundError:
            logger.error(f"kb not found at {kb_path}")
            entries = []

        for entry in entries:
            self.fallback_kb[entry["term"].lower()] = entry

        if settings.openai_api_key and _llama_available:
            try:
                self._build_index(entries)
                self.ready = True
                logger.info("rag ready (llamaindex + chromadb)")
            except Exception as e:
                logger.error(f"vector store init failed: {e}")
        else:
            if not settings.openai_api_key:
                logger.info("no openai key, running fallback")

    def _build_index(self, entries):
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection("medical_knowledge")

        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=settings.openai_api_key)

        # seed if empty
        if collection.count() == 0:
            logger.info(f"seeding {len(entries)} kb entries")
            docs = []
            for entry in entries:
                text = f"{entry['title']}\n\n{entry['explanation']}"
                if entry.get("what_it_means"):
                    text += f"\n\nwhat it means for you: {entry['what_it_means']}"
                if entry.get("normal_range"):
                    text += f"\n\nnormal range: {entry['normal_range']}"
                if entry.get("when_to_worry"):
                    text += f"\n\nwhen to call your doctor: {entry['when_to_worry']}"
                if entry.get("tips"):
                    text += "\n\ntips:\n" + "\n".join(f"- {t}" for t in entry["tips"])

                docs.append(Document(
                    text=text,
                    metadata={
                        "term": entry["term"],
                        "category": entry["category"],
                        "sources": ", ".join(entry.get("sources", [])),
                    },
                ))

            self.index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)
        else:
            logger.info(f"loaded existing collection ({collection.count()} docs)")
            self.index = VectorStoreIndex.from_vector_store(vector_store)

    def explain(self, term: str, context: str = "") -> dict:
        if self.index and settings.openai_api_key and _langchain_available:
            try:
                return self._rag_explain(term, context)
            except Exception as e:
                logger.error(f"rag failed, using fallback: {e}")

        return self._fallback_explain(term)

    def _rag_explain(self, term: str, context: str) -> dict:
        # retrieve from chromadb via llamaindex
        retriever = self.index.as_retriever(similarity_top_k=3)
        query = f"explain: {term}"
        if context:
            query += f" (context: {context})"

        nodes = retriever.retrieve(query)
        chunks = "\n\n---\n\n".join([n.text for n in nodes])

        sources = []
        for n in nodes:
            src = n.metadata.get("sources", "")
            if src:
                sources.extend([s.strip() for s in src.split(",")])
        sources = list(set(sources)) or ["Medical Reference"]

        # generate with langchain + openai
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "you explain medical terms in plain language a regular person can "
             "understand. target a 6th grade reading level. only use info from "
             "the reference material. keep it to 2-3 sentences."),
            ("human",
             "reference material:\n\n{chunks}\n\n"
             "explain this in simple words: {term}\n{ctx}\n"
             "just give the explanation, nothing else."),
        ])

        ctx = f"patient context: {context}" if context else ""
        chain = prompt | llm
        resp = chain.invoke({"chunks": chunks, "term": term, "ctx": ctx})

        explanation = resp.content
        score = textstat.flesch_kincaid_grade(explanation)

        return {
            "plain_language": explanation,
            "sources": sources,
            "readability_score": round(score, 1),
        }

    def _fallback_explain(self, term: str) -> dict:
        t = term.lower().strip()

        # exact
        if t in self.fallback_kb:
            entry = self.fallback_kb[t]
            return {
                "plain_language": entry["explanation"],
                "sources": entry.get("sources", ["Medical Reference"]),
                "readability_score": round(textstat.flesch_kincaid_grade(entry["explanation"]), 1),
            }

        # partial
        for key, entry in self.fallback_kb.items():
            if key in t or t in key:
                return {
                    "plain_language": entry["explanation"],
                    "sources": entry.get("sources", ["Medical Reference"]),
                    "readability_score": round(textstat.flesch_kincaid_grade(entry["explanation"]), 1),
                }

        return {
            "plain_language": f"'{term}' is a medical term. ask your doctor or nurse to explain what this means for you.",
            "sources": ["General"],
            "readability_score": 6.0,
        }
