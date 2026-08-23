

import re
import time
import json
import glob
from dateutil import parser as dateparser

# --- copied verbatim from src/agent/nodes.py ---
_DATE_HEADER = re.compile(r"^\s*Date:\s*(.+?)\s*$", re.I | re.M)
_MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December")
_DATE_PATTERN = re.compile(rf"\b(?:\d{{4}}-\d{{2}}-\d{{2}}|(?:{_MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?)\b", re.I)
_COMMITMENT = re.compile(r"\b(?:i['’]?ll|i will|i can|we['’]?ll|we will|will|going to|need to|needs to|must|should)\b", re.I)
_URGENT = re.compile(r"\b(?:urgent|asap|blocker|blocking|critical|immediately)\b", re.I)


def _header_date(transcript):
    match = _DATE_HEADER.search(transcript)
    if not match:
        return None
    try:
        return dateparser.parse(match.group(1)).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return None


def _heuristic_items(transcript, roster):
    items = []
    for line in transcript.splitlines():
        if _COMMITMENT.search(line):
            date_match = _DATE_PATTERN.search(line)
            items.append({
                "task": line.strip(), "owner": "Unknown (Offline Fallback)",
                "due_iso": date_match.group(0) if date_match else None,
                "priority": "high" if _URGENT.search(line) else "medium",
                "dependencies": [], "confidence": 0.5
            })
    return items


def ingestor(transcript):
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in transcript.splitlines()]
    return "\n".join([line for line in lines if line]).strip()


if __name__ == "__main__":
    results = []
    for path in sorted(glob.glob("data/eval/eval_*.txt")):
        raw = open(path).read()

        t0 = time.perf_counter()
        clean = ingestor(raw)
        t_ingest = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        _header_date(clean)
        items = _heuristic_items(clean, [])
        t_extract = (time.perf_counter() - t0) * 1000

        results.append({
            "file": path, "chars": len(raw),
            "ingestor_ms": round(t_ingest, 3),
            "heuristic_extractor_ms": round(t_extract, 3),
        })
        print(results[-1])

    avg_ingest = sum(r["ingestor_ms"] for r in results) / len(results)
    avg_extract = sum(r["heuristic_extractor_ms"] for r in results) / len(results)
    print(f"\nAvg ingestor latency: {avg_ingest:.3f} ms")
    print(f"Avg heuristic-extractor latency: {avg_extract:.3f} ms")

    json.dump({"per_file": results, "avg_ingestor_ms": round(avg_ingest, 3),
               "avg_heuristic_extractor_ms": round(avg_extract, 3)},
              open("real_latency_result.json", "w"), indent=2)
    print("\nSaved: real_latency_result.json")
