import chromadb
from pathlib import Path
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever


current_dir = Path(__file__).parent
kb_path = current_dir.parent / "agent"
db_path = kb_path / "chroma_db"

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Persistent Storage
chroma_client = chromadb.PersistentClient(path=str(db_path))
chroma_collection = chroma_client.get_or_create_collection("meeting")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = None
bm25_retriever = None

def read_documents(file_contents: dict[str, str]):
    global index, bm25_retriever

    documents = [
        Document(text=text, metadata={"source": name}) 
        for name, text in file_contents.items()
    ]

    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)

    index = VectorStoreIndex(nodes, storage_context=storage_context)

    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=3)

    print(f"Indexed {len(nodes)} chunks into Vector.")

def retrieve_context(query: str, top_k: int = 3):
    global index, bm25_retriever

    if not index or not bm25_retriever:
        return "No documents have been uploaded to the knowledge base.", []

    vector_retriever = index.as_retriever(similarity_top_k=top_k)


    hybrid_retriever = QueryFusionRetriever(
        [vector_retriever, bm25_retriever],
        similarity_top_k=top_k,
        num_queries=1,
        mode="reciprocal_rerank"
    )

    hits = hybrid_retriever.retrieve(query)

    ctx = "\n".join(f"[{h.node.metadata['source']}] {h.node.text}" for h in hits)
    srcs = sorted({h.node.metadata["source"] for h in hits})

    return ctx, srcs