"""Grader for challenge_1 (the ticket-triage benchmark)."""

import re

PLACEHOLDER = "{tickets}"


def build_prompt(case, instructions):
    if PLACEHOLDER not in instructions:
        raise ValueError(f"skill instructions must contain the literal placeholder {PLACEHOLDER}")
    tickets_text = "\n".join(f"{ticket['id']}: {ticket['text']}" for ticket in case["tickets"])
    return instructions.replace(PLACEHOLDER, tickets_text)


def _extract_bullet_ids(bullet_lines, valid_ids):
    found = []
    for line in bullet_lines:
        for ticket_id in valid_ids:
            if re.search(rf"\b{re.escape(ticket_id)}\b", line) and ticket_id not in found:
                found.append(ticket_id)
    return found


def _extract_count(response_text):
    """Read the count only from the actual last line — a match anywhere
    earlier (e.g. inside a bullet's own text) isn't the declared count."""
    lines = [line.strip() for line in response_text.strip().splitlines() if line.strip()]
    if not lines:
        return None
    match = re.search(r"(\d+)\s+of\s+(\d+)", lines[-1], re.IGNORECASE)
    return int(match.group(1)) if match else None


def _score_single_line_format(response_text, total_tickets):
    lines = [line.strip() for line in response_text.strip().splitlines() if line.strip()]
    if len(lines) != 1:
        return 0.0
    pattern = rf"^\d+ of {total_tickets} tickets are urgent\.?$"
    return 1.0 if re.fullmatch(pattern, lines[0], re.IGNORECASE) else 0.0


def _score_bulleted_format(lines, bullet_lines, total_tickets):
    if not lines:
        return 0.0
    count_line = lines[-1]
    has_count_line = re.search(rf"\d+\s+of\s+{total_tickets}\s+tickets", count_line, re.IGNORECASE) is not None
    body_lines = lines[:-1]
    non_bullet_junk = [line for line in body_lines if not line.startswith(("-", "*"))]

    score = 0.0
    if has_count_line:
        score += 0.5
    if not non_bullet_junk:
        score += 0.5
    return score


def _score_classification(predicted_ids, definite_ids, optional_ids):
    definite = set(definite_ids)
    optional = set(optional_ids)
    predicted = set(predicted_ids)

    if not definite:
        return 1.0 if not (predicted - optional) else 0.0

    correct = predicted & definite
    false_positives = predicted - definite - optional
    fraction = (len(correct) - 0.5 * len(false_positives)) / len(definite)
    return max(0.0, min(1.0, fraction))


def score(case, response_text):
    valid_ids = [ticket["id"] for ticket in case["tickets"]]
    total_tickets = len(case["tickets"])
    ground_truth = case["ground_truth"]

    lines = [line.strip() for line in response_text.strip().splitlines() if line.strip()]
    bullet_lines = [line for line in lines if line.startswith(("-", "*"))]
    predicted_ids = _extract_bullet_ids(bullet_lines, valid_ids)
    extracted_count = _extract_count(response_text)

    subscores = {}

    if "urgent_count" in ground_truth:
        subscores["format_compliance"] = _score_single_line_format(response_text, total_tickets)
        subscores["count_correct"] = 1.0 if extracted_count == ground_truth["urgent_count"] else 0.0
    else:
        definite = ground_truth.get("urgent_ids_definite", [])
        optional = ground_truth.get("urgent_ids_borderline", []) + ground_truth.get("urgent_ids_ambiguous", [])
        subscores["classification_accuracy"] = _score_classification(predicted_ids, definite, optional)
        subscores["format_compliance"] = _score_bulleted_format(lines, bullet_lines, total_tickets)

        if "urgent_count_accepted" in ground_truth:
            accepted = ground_truth["urgent_count_accepted"]
            subscores["count_matches_ground_truth"] = 1.0 if extracted_count in accepted else 0.0

        subscores["count_present_and_parseable"] = 1.0 if extracted_count is not None else 0.0
        subscores["count_matches_own_list"] = 1.0 if extracted_count == len(bullet_lines) else 0.0

    weights = case["grading_weights"]
    return sum(weights[key] * subscores.get(key, 0.0) for key in weights)
