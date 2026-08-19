import chromadb
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore



Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
chroma_client = chromadb.EphemeralClient()
chroma_collection = chroma_client.get_or_create_collection("task2_kb")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = None

def read_documents(file_contents: dict[str, str]):
    global index
    documents = [
        Document(text=text, metadata={"source": name}) 
        for name, text in file_contents.items()
    ]

    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)

    index = VectorStoreIndex(nodes, storage_context=storage_context)
    print(f"Indexed {len(nodes)} chunks into the knowledge base.")

def retrieve_context(query: str, top_k: int = 3):
    if not index:
        return "No documents have been uploaded to the knowledge base.", []

    retriever = index.as_retriever(similarity_top_k=top_k)
    hits = retriever.retrieve(query)

    ctx = "\n".join(f"[{h.node.metadata['source']}] {h.node.text}" for h in hits)
    srcs = sorted({h.node.metadata["source"] for h in hits})

    return ctx, srcs