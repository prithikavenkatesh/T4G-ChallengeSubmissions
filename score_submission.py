import frontmatter
from constants import REQUIRED_FRONTMATTER_FIELDS, MODEL, client
import yaml 
import json
import argparse
import csv
import os

parser = argparse.ArgumentParser()
parser.add_argument("--skill", required=True)
parser.add_argument("--cases", required=True)
parser.add_argument("--out", default="results")
args = parser.parse_args()

def parse_frontmatter(file_text):
    post = frontmatter.loads(file_text)
    return post.metadata, post.content

def validate_skill(frontmatter, body):
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in frontmatter or frontmatter[field] is None or frontmatter[field] == "":
            return False, f"Missing required frontmatter field: {field}"

    if body is None or body.strip() == "":
        return False, "Skill body is empty"

    return True, None

def load_skill(skill_path):
    with open(skill_path, "r") as f:
        file_text = f.read()

    metadata, body = parse_frontmatter(file_text)

    team_name = metadata.get("team_name", "Unknown Team")

    return {
        "team_name": team_name,
        "description": metadata.get("description", ""),
        "instructions": body,
        "frontmatter": metadata,
        "body": body
    } 

def load_cases(cases_path):
    with open(cases_path, "r") as f:
        return yaml.safe_load(f)


def run_case(case, skill):

    response = client.models.generate_content(
        model=MODEL,
        contents=case["user_message"],
        config = {
            "system_instruction": skill["instructions"]
        }
    )
    return response.text

def score_deterministic(case, response_text):
    match_type = case["match_type"]
    ground_truth = case["ground_truth"]

    if match_type == "exact":
        met = (response_text.strip() == ground_truth.strip())
    elif match_type == "contains":
        met = (ground_truth.strip() in response_text.strip())
    elif match_type == "regex":
        import re
        met = (re.search(ground_truth.strip(), response_text.strip()) is not None)
    else:
        raise ValueError(f"Unknown match_type: {match_type}")

    return case["max_points"] if met else 0

def score_rubric_judge(case, response_text):
    rubric_lines = "\n".join(case["rubric"])
    judge_prompt = (
        "You are grading an AI response against a fixed rubric.\n\n"
        + "RUBRIC:\n" + rubric_lines + "\n\n"
        + "MAX POINTS: " + str(case["max_points"]) + "\n\n"
        + "RESPONSE TO GRADE:\n" + response_text + "\n\n"
        + "Return ONLY JSON in this shape: {\"score\": <integer 0 to max points>}"
    )

    judge_response = client.models.generate_content(
        model=MODEL,
        contents=judge_prompt,
        config = {
            "response_mime_type": "application/json"
        }
    )

    try:
        parsed = json.loads(judge_response.text)
        return parsed.get("score", 0)
    except json.JSONDecodeError:
        return 0
    
def main():
    skill = load_skill(args.skill)
    is_valid, error = validate_skill(skill["frontmatter"], skill["body"])

    if not is_valid:
        os.makedirs(args.out, exist_ok=True)
        invalid_path = os.path.join(args.out, f"{skill['team_name']}.invalid")
        with open(invalid_path, "w") as f:
            f.write(error)
        print(f"Skill validation failed: {error}")
        return

    cases = load_cases(args.cases)
    rows = []

    for case in cases:
        try:
            response_text = run_case(case, skill)
            if case["case_type"] == "deterministic":
                score = score_deterministic(case, response_text)
            elif case["case_type"] == "rubric_judge":
                score = score_rubric_judge(case, response_text)
        except Exception as e:
            print(f"Error processing case {case['id']}: {e}")
            rows.append({"case_id": case["id"], "score": 0, "max_points": case["max_points"], "response": ""})
            continue

        rows.append({
            "case_id": case["id"],
            "score": score,
            "max_points": case["max_points"],
            "response": response_text
        })

    os.makedirs(args.out, exist_ok=True)

    output_path = os.path.join(args.out, f"{skill['team_name']}.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "score", "max_points", "response"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")

            


