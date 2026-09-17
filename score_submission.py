import argparse
import csv
import glob
import os

import yaml

from constants import DEFAULT_CASE_POINTS, DIFFICULTY_POINTS, MODEL, REQUIRED_SKILL_FIELDS, client
from graders import GRADERS


def load_skill(skill_path):
    with open(skill_path, "r") as f:
        skill = yaml.safe_load(f)

    skill_dir = os.path.dirname(skill_path)
    team_name = os.path.basename(os.path.normpath(skill_dir)) if skill_dir else "Unknown Team"

    return {
        "team_name": team_name,
        "instructions": skill.get("instructions", "") if skill else "",
        "raw": skill or {},
    }


def validate_skill(skill):
    for field in REQUIRED_SKILL_FIELDS:
        if not skill["raw"].get(field):
            return False, f"Missing required field: {field}"
    return True, None


def load_cases(cases_path):
    if os.path.isfile(cases_path):
        case_files = [cases_path]
    else:
        case_files = sorted(glob.glob(os.path.join(cases_path, "*.yaml")))

    cases = []
    for case_file in case_files:
        with open(case_file, "r") as f:
            case = yaml.safe_load(f)
        if not case:
            print(f"Skipping empty/invalid case file: {case_file}")
            continue
        cases.append(case)
    return cases


def call_model(prompt):
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


def score_case(case, skill):
    grader = GRADERS.get(case.get("category"))
    if grader is None:
        raise ValueError(f"no grader registered for category '{case.get('category')}'")

    # Building the prompt is deterministic (case + skill only) so a failure
    # here (e.g. a missing placeholder) will fail identically every trial —
    # raise once instead of burning retries on it. Only the network call
    # itself gets per-trial tolerance, since that's where transient
    # failures (timeouts, rate limits) actually happen.
    prompt = grader.build_prompt(case, skill["instructions"])

    trials = case.get("trials", 1)
    best_fraction = 0.0
    best_response = ""
    for _ in range(trials):
        try:
            response_text = call_model(prompt)
        except Exception as e:
            print(f"Trial failed for case {case.get('case_id')}: {e}")
            continue
        fraction = grader.score(case, response_text)
        if fraction >= best_fraction:
            best_fraction = fraction
            best_response = response_text
    return best_fraction, best_response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True)
    parser.add_argument("--cases", default="cases")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()

    skill = load_skill(args.skill)
    is_valid, error = validate_skill(skill)

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
        if case.get("practice"):
            print(f"Skipping practice case {case['case_id']} (not graded)")
            continue

        max_points = DIFFICULTY_POINTS.get(case.get("difficulty"), DEFAULT_CASE_POINTS)

        try:
            best_fraction, best_response = score_case(case, skill)
        except Exception as e:
            print(f"Error processing case {case['case_id']}: {e}")
            rows.append({"case_id": case["case_id"], "score": 0, "max_points": max_points, "response": ""})
            continue

        rows.append({
            "case_id": case["case_id"],
            "score": round(best_fraction * max_points),
            "max_points": max_points,
            "response": best_response,
        })

    os.makedirs(args.out, exist_ok=True)

    output_path = os.path.join(args.out, f"{skill['team_name']}.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "score", "max_points", "response"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
