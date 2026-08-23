import json
import time
import sys
from pathlib import Path
from typing import List, Dict

# Project root setup using your exact path structure
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.retrieval.retriever import retrieve_context, read_documents

def calculate_mrr(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    for rank, source in enumerate(retrieved_sources, start=1):
        clean_source = Path(source).stem.lower()
        for expected in expected_sources:
            clean_expected = Path(expected).stem.lower()
            if clean_source in clean_expected or clean_expected in clean_source:
                return 1.0 / rank
    return 0.0

def calculate_recall(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    clean_retrieved = [Path(src).stem.lower() for src in retrieved_sources]
    clean_expected = [Path(ext).stem.lower() for ext in expected_sources]
    
    hits = sum(1 for expected in clean_expected if any(expected in ret or ret in expected for ret in clean_retrieved))
    return hits / len(clean_expected) if clean_expected else 0.0

def load_knowledge_base():
    """Loads all knowledge base and markdown files into the retriever."""
    print("Loading knowledge base documents...")
    kb_dir = project_root / "data" / "knowledge_base" / "transcripts"
    file_contents = {}
    
    # Load transcript text files
    for file_path in kb_dir.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            file_contents[file_path.name] = f.read()
            
    # Load markdown documents (like context.md and past_decision.md) if they exist
    for file_path in kb_dir.glob("*.md"):
        with open(file_path, "r", encoding="utf-8") as f:
            file_contents[file_path.name] = f.read()
            
    if not file_contents:
        print(f"Warning: No files found in {kb_dir}")
        return
        
    read_documents(file_contents)

def run_evaluation(gold_file_path: str, top_k: int = 5):
    load_knowledge_base()
    
    print(f"\n--- Starting Retrieval Evaluation (Top-{top_k}) ---")
    
    try:
        with open(gold_file_path, 'r', encoding='utf-8') as f:
            gold_data: List[Dict] = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {gold_file_path}")
        return

    total_mrr = 0.0
    total_recall = 0.0
    total_queries = len(gold_data)
    start_time = time.time()

    for item in gold_data:
        query = item.get("query", "")
        expected = item.get("relevant_sources", []) # Updated to match your JSON key
        
        _, retrieved_srcs = retrieve_context(query, top_k=top_k)
        
        mrr = calculate_mrr(retrieved_srcs, expected)
        recall = calculate_recall(retrieved_srcs, expected)
        
        total_mrr += mrr
        total_recall += recall
        
        print(f"Query: '{query[:35]}...' | Expected: {expected} | Retrieved: {retrieved_srcs} | MRR: {mrr:.2f}")

    elapsed_time = time.time() - start_time
    
    print("\n" + "="*40)
    print("FINAL RETRIEVAL METRICS")
    print("="*40)
    print(f"Total Queries: {total_queries}")
    print(f"Mean Reciprocal Rank (MRR): {total_mrr / total_queries:.4f}")
    print(f"Average Recall@{top_k}: {total_recall / total_queries:.4f}")
    print(f"Avg Latency per Query: {(elapsed_time / total_queries) * 1000:.2f} ms")
    print("="*40)

if __name__ == "__main__":
    gold_path = project_root / "data" / "eval" / "retrieval_gold.json"
    run_evaluation(str(gold_path), top_k=5)