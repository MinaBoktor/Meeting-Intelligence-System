

import json

try:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    count_tokens = lambda s: len(enc.encode(s))
    METHOD = "tiktoken (cl100k_base)"
except Exception:
    # Claude's sandbox couldn't reach openaipublic.blob.core.windows.net to
    # download the tiktoken encoding, so this fell back to an estimate.
    # On your machine (normal internet access) this will use real tiktoken counts.
    count_tokens = lambda s: max(1, len(s) // 4)
    METHOD = "estimate (len/4) — install tiktoken + allow network for exact counts"


def to_toon(rows: list[dict]) -> str:
    if not rows:
        return ""
    keys = list(rows[0].keys())
    out = [f"[{len(rows)}]{{{','.join(keys)}}}:"]
    for row in rows:
        vals = []
        for k in keys:
            v = row[k]
            if isinstance(v, list):
                v = ";".join(v) if v else "-"
            vals.append(str(v))
        out.append("  " + ",".join(vals))
    return "\n".join(out)


if __name__ == "__main__":
    data = json.load(open("data/eval/gold_action_items.json"))
    all_items = []
    for d in data:
        all_items.extend(d["gold_action_items"])

    js = json.dumps(all_items)
    tn = to_toon(all_items)
    j_tok, t_tok = count_tokens(js), count_tokens(tn)

    print(f"Method: {METHOD}")
    print(f"Real action items tested: {len(all_items)} (from {len(data)} real eval transcripts)\n")
    print("--- JSON (first 3 items) ---")
    print(json.dumps(all_items[:3], indent=2))
    print(f"\nFull JSON: {j_tok} tokens, {len(js)} chars\n")
    print("--- TOON (first 3 items) ---")
    print(to_toon(all_items[:3]))
    print(f"\nFull TOON: {t_tok} tokens, {len(tn)} chars\n")
    print(f"Saving: {round(100*(j_tok-t_tok)/j_tok, 1)}% fewer tokens with TOON")

    # Per-meeting average (closer to real usage: one meeting's items sent at a time)
    per_meeting = []
    for d in data:
        items = d["gold_action_items"]
        j = count_tokens(json.dumps(items))
        t = count_tokens(to_toon(items))
        per_meeting.append((j, t))
    avg_j = sum(x[0] for x in per_meeting) / len(per_meeting)
    avg_t = sum(x[1] for x in per_meeting) / len(per_meeting)
    print(f"\nAvg JSON tokens per meeting: {avg_j:.1f}")
    print(f"Avg TOON tokens per meeting: {avg_t:.1f}")
    print(f"Avg saving per meeting: {round(100*(avg_j-avg_t)/avg_j, 1)}%")

    json.dump({
        "method": METHOD, "n_items": len(all_items),
        "json_tokens": j_tok, "toon_tokens": t_tok,
        "json_chars": len(js), "toon_chars": len(tn),
        "saving_pct_total": round(100*(j_tok-t_tok)/j_tok, 1),
        "avg_json_tokens_per_meeting": round(avg_j, 1),
        "avg_toon_tokens_per_meeting": round(avg_t, 1),
        "avg_saving_pct_per_meeting": round(100*(avg_j-avg_t)/avg_j, 1),
    }, open("real_toon_result.json", "w"), indent=2)
    print("\nSaved: real_toon_result.json")
