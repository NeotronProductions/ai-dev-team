"""
Extract acceptance criteria and definition-of-done from issue body;
check whether a plan satisfies those requirements (semantic validation).
Project-agnostic: works for any GitHub issue format.
"""

import re
from typing import List, Tuple


def extract_requirements(issue_body: str, issue_title: str = "") -> List[str]:
    """
    Parse issue body (and optionally title) for acceptance criteria and
    definition-of-done items. Returns a deduplicated list of requirement strings.
    Works for any project and common issue formats.
    """
    if not issue_body and not issue_title:
        return []

    text = (issue_body or "").strip()
    requirements: List[str] = []

    # Section headers that typically list requirements (match ## or ###)
    section_pattern = re.compile(
        r"(?m)^#{2,3}\s*(?:Acceptance\s+[Cc]riteria|Definition\s+of\s+[Dd]one|Requirements|Done\s+when|Scope|Must\s+have|Done|Criteria)\s*$",
        re.IGNORECASE
    )
    positions = [(m.start(), m.end()) for m in section_pattern.finditer(text)]
    positions.append((len(text), len(text)))  # end sentinel

    for i in range(len(positions) - 1):
        start = positions[i][1]
        end = positions[i + 1][0]
        section_text = text[start:end]
        # Extract bullets: - item or * item or - [ ] item
        for line in section_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            bullet_match = re.match(r"^[-*•]\s*(?:\[\s*\]\s*)?(.+)$", line)
            if bullet_match:
                req = bullet_match.group(1).strip()
                if len(req) > 3 and req not in requirements:
                    requirements.append(req)
            num_match = re.match(r"^\d+[.)]\s*(.+)$", line)
            if num_match:
                req = num_match.group(1).strip()
                if len(req) > 3 and req not in requirements:
                    requirements.append(req)

    # Fallback: if no structured sections, take first 15 bullet lines from body
    if not requirements and text:
        for line in text.split("\n")[:40]:
            line = line.strip()
            bullet_match = re.match(r"^[-*•]\s*(.+)$", line)
            if bullet_match:
                req = bullet_match.group(1).strip()
                if len(req) > 5 and req not in requirements:
                    requirements.append(req)
                    if len(requirements) >= 15:
                        break

    # If we have a title but no requirements, use title as a single high-level requirement
    if not requirements and issue_title and len(issue_title.strip()) > 5:
        requirements.append(issue_title.strip())

    return requirements


def check_requirements_satisfied(
    requirement_list: List[str],
    plan_text: str,
    min_keyword_overlap: int = 2,
) -> Tuple[bool, List[str]]:
    """
    Check whether the plan (or implementation output) text clearly addresses
    each requirement. Uses keyword overlap; if a requirement has no significant
    overlap with the plan, it is considered unsatisfied.
    Returns (all_satisfied, unsatisfied_list).
    """
    if not requirement_list:
        return True, []

    plan_lower = plan_text.lower()
    unsatisfied: List[str] = []

    stop = {"the", "a", "an", "to", "of", "and", "or", "in", "on", "for", "is", "be", "can", "that", "this", "with", "so", "when", "if", "as"}
    for req in requirement_list:
        words = [w.lower() for w in re.findall(r"\b\w+\b", req) if len(w) > 1 and w.lower() not in stop]
        if not words:
            if req.strip().lower() not in plan_lower:
                unsatisfied.append(req)
            continue
        found = sum(1 for w in words if w in plan_lower)
        if found < min(min_keyword_overlap, len(words)):
            unsatisfied.append(req)

    return (len(unsatisfied) == 0, unsatisfied)
