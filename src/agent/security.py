"""Transcript-injection defences.

A transcript is untrusted input: it is a recording of what people said, and
anyone who can get text into it (a participant, an ASR error, a pasted note)
can try to address the model directly. This module keeps transcript content
as *data*:

  1. scan/sanitize - instruction-shaped lines are quarantined before the
     model ever sees them, and recorded so the attempt is visible.
  2. classify_owner - the roster is trusted config; an identity that is not
     on it cannot be introduced by transcript text.
  3. screen_item    - extracted records are re-checked on the way out, so a
     payload that survived the model still cannot reach the report.
"""
import difflib
import json
import re

# Generic org words that legitimately appear as an "owner" when a team rather
# than a person is accountable. These resolve to null later; they are not
# injected identities.
TEAM_WORDS = frozenset({
    "product", "engineering", "design", "qa", "marketing", "sales",
    "finance", "operations", "security", "support", "customer", "success",
    "team", "everyone", "all", "tbd", "unassigned", "none",
})

# Line-level patterns. Each is an attempt to speak to the model rather than
# to the meeting.
INJECTION_PATTERNS = [
    (r"\b(?:ignore|disregard|forget)\s+(?:all\s+|any\s+)?(?:previous|prior|above|earlier|the)\b",
     "instruction_override"),
    (r"\b(?:important\s+)?system\s+(?:instruction|prompt|message|note)\b", "system_spoof"),
    (r"<\|?im_(?:start|end)\|?>|<\|\s*system\s*\|>|\[/?INST\]|###\s*system", "role_marker"),
    (r"\b(?:you are now|act as|from now on|new instructions)\b", "persona_override"),
    (r"^\W*(?:assistant|ai|model|llm|bot|system)\s*[,:]\s", "assistant_address"),
    (r"\bnote to (?:the )?assistant\b", "assistant_address"),
    (r"\bskip\s+(?:the\s+)?human\s+(?:review|approval)\b", "hitl_bypass"),
    (r"\bauto[-\s]?approve\b|\bapproval has already been granted\b", "hitl_bypass"),
    (r"\broster\s+(?:also\s+)?includes?\b|\btreat\s+\w+\s+as\s+(?:a\s+)?valid\s+owners?\b",
     "roster_spoof"),
    (r"\boverride\s+the\s+\w+\s+(?:validation|rule|check)\b", "authority_claim"),
    (r"\bauthoris(?:e|es|ed)\s+you\b|\bauthoriz(?:e|es|ed)\s+you\b", "authority_claim"),
    (r"\b(?:email|send|post|upload|exfiltrate|leak|forward)\b[^.\n]{0,60}"
     r"\b(?:credential|password|api\s*key|secret|token|roster|records)\b", "exfiltration"),
    (r"\breturn\s+(?:exactly\s+)?(?:only\s+)?this\b|\breturn\s+the\s+following\s+(?:json|array)\b",
     "output_hijack"),
    (r"\bregardless of the transcript\b|\bset\s+(?:the\s+)?(?:priority|confidence)\s+to\b",
     "field_manipulation"),
]
_COMPILED = [(re.compile(p, re.I), label) for p, label in INJECTION_PATTERNS]

# Payload markers that must never reach an extracted record, whatever route
# they took to get there.
_EXFIL_MARKERS = re.compile(
    r"https?://\S+"
    r"|\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b"
    r"|\b(?:api[\s_-]?key|credential|password|secret\s+key|access\s+token)s?\b",
    re.I,
)

def _is_embedded_json(line: str) -> bool:
    """A transcript line that actually parses as a JSON object/array is not
    speech - it is a payload aimed at the output format. Shape alone is not
    enough: real transcripts contain lines like
    "[transcription note: one speaker boundary was uncertain]".
    """
    text = line.strip().rstrip(",")
    if not text.startswith(("[", "{")):
        return False
    try:
        return isinstance(json.loads(text), (list, dict))
    except (ValueError, TypeError):
        return False

QUARANTINE_MARKER = "[QUARANTINED: instruction-like content removed by the security layer]"


def scan_line(line: str) -> list[str]:
    """Injection techniques detected in one line."""
    found = [label for pattern, label in _COMPILED if pattern.search(line)]
    if _is_embedded_json(line):
        found.append("output_hijack")
    if _EXFIL_MARKERS.search(line):
        found.append("exfiltration")
    return sorted(set(found))


def sanitize_transcript(transcript: str) -> tuple[str, list[dict]]:
    """Replace instruction-shaped lines with a marker before the model sees
    them. The line is replaced rather than deleted so speaker turns keep their
    positions and a human reviewing the minutes can see something was removed.
    """
    findings: list[dict] = []
    cleaned: list[str] = []

    for number, line in enumerate(transcript.splitlines(), start=1):
        techniques = scan_line(line)
        if techniques:
            findings.append({
                "line": number,
                "techniques": techniques,
                "quarantined_text": line.strip()[:300],
            })
            cleaned.append(QUARANTINE_MARKER)
        else:
            cleaned.append(line)

    return "\n".join(cleaned), findings


def classify_owner(owner, roster: list[str]) -> str:
    """'empty' | 'roster' | 'team' | 'unknown'.

    'unknown' means the transcript named an identity that is not on the
    roster - the shape of a roster-spoofing attack.
    """
    if owner is None or not str(owner).strip():
        return "empty"

    name = str(owner).strip()
    lowered = name.lower()

    if any(lowered == person.lower() for person in roster):
        return "roster"
    # A near miss is a typo of a real person; the repair loop resolves it.
    if difflib.get_close_matches(name, roster, n=1, cutoff=0.75):
        return "roster"
    # People are often referred to by first name alone ("Nour", "Karim").
    for person in roster:
        parts = [part.lower() for part in person.split()]
        if lowered in parts:
            return "roster"

    if lowered in TEAM_WORDS or any(word in TEAM_WORDS for word in lowered.split()):
        return "team"
    return "unknown"


def screen_item(raw: dict, roster: list[str], strict_owner: bool = False) -> str | None:
    """Reason to reject an extracted record, or None to let it through.

    Applied to the *raw* model output, before schema validation, so an
    injected identity is dropped with its task rather than being quietly
    downgraded to an unowned item.
    """
    if not isinstance(raw, dict):
        return None  # the repair loop reports this one

    ownership = classify_owner(raw.get("owner"), roster)
    if ownership == "unknown":
        return f"owner {str(raw.get('owner')).strip()!r} is not on the roster"

    # Escalation: once this transcript has tried to redefine the roster, an
    # unattributable task is more likely to be the injected payload than a real
    # commitment - the model may strip the fake owner and leave the task behind.
    # Only applies to transcripts where a spoof was actually detected, and the
    # rejected record is still shown to the human at the approval gate.
    if strict_owner and ownership == "empty":
        return ("unowned task rejected: this transcript attempted to redefine "
                "the roster, so ownerless items cannot be trusted")

    text = " ".join(str(part) for part in (
        raw.get("task") or "",
        raw.get("owner") or "",
        *(raw.get("dependencies") or []),
    ))
    marker = _EXFIL_MARKERS.search(text)
    if marker:
        return f"record carries an exfiltration marker ({marker.group(0)!r})"

    if any(pattern.search(text) for pattern, _ in _COMPILED):
        return "record repeats instruction-like injected text"

    return None
