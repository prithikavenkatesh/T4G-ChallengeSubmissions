import argparse
import datetime
import json
import os

from run_competition import compute_totals, print_ranked_results


def append_to_history(history_path, totals):
    today = datetime.date.today().isoformat()
    os.makedirs(os.path.dirname(history_path), exist_ok=True)

    with open(history_path, "a") as f:
        for team, data in totals.items():
            f.write(json.dumps({
                "date": today,
                "team": team,
                "score": data["score"],
                "raw_total": data["raw_total"],
                "raw_possible": data["raw_possible"],
            }) + "\n")


def load_best_per_team(history_path):
    best_per_team = {}

    if not os.path.exists(history_path):
        return best_per_team

    with open(history_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            team = entry["team"]
            if team not in best_per_team or entry["score"] > best_per_team[team]["score"]:
                best_per_team[team] = entry

    return best_per_team


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--challenge", required=True)
    parser.add_argument("--results-root", default="results")
    args = parser.parse_args()

    results_dir = os.path.join(args.results_root, args.challenge)
    history_path = os.path.join(results_dir, "history.jsonl")

    totals, invalid_results, csv_teams = compute_totals(results_dir)

    # Record today's snapshot before reading the best-ever standings back out,
    # so a new personal best set today shows up immediately instead of only
    # after tomorrow's run reads the file again.
    append_to_history(history_path, totals)

    best_totals = load_best_per_team(history_path)
    print_ranked_results(best_totals)

    if invalid_results:
        print("\nINVALID SUBMISSIONS (today):")
        for invalid in invalid_results:
            print(f"{invalid['team']}: {invalid['error']}")

    no_graded_cases = sorted(csv_teams - set(totals.keys()))
    if no_graded_cases:
        print("\nNO GRADED CASES TODAY (submitted, but nothing counted toward today's score):")
        for team in no_graded_cases:
            print(team)


if __name__ == "__main__":
    main()
