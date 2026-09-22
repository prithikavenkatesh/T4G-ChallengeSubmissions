import argparse
import csv
import glob
import os

def compute_totals(results_dir):
    result_files = sorted(glob.glob(os.path.join(results_dir, "*")))

    valid_results = []
    invalid_results = []
    csv_teams = set()

    for result_path in result_files:
        if result_path.endswith(".invalid"):
            team = os.path.basename(result_path).replace(".invalid", "")
            with open(result_path) as f:
                error = f.read()
            invalid_results.append({"team": team, "error": error})

        elif result_path.endswith(".csv"):
            team = os.path.basename(result_path).replace(".csv", "")
            csv_teams.add(team)
            with open(result_path) as f:
                for row in csv.DictReader(f):
                    valid_results.append({
                        "team": team,
                        "case_id": row["case_id"],
                        "score": row["score"],
                        "max_points": row["max_points"],
                    })

    totals = {}
    for result in valid_results:
        team = result["team"]
        if team not in totals:
            totals[team] = {"raw_total": 0, "raw_possible": 0}
        totals[team]["raw_total"] += int(result["score"])
        totals[team]["raw_possible"] += int(result["max_points"])

    for team in totals:
        possible = totals[team]["raw_possible"]
        totals[team]["score"] = (totals[team]["raw_total"] / possible) if possible > 0 else 0

    return totals, invalid_results, csv_teams

def print_ranked_results(totals):
    ranked = sorted(totals.items(), key=lambda x: (-x[1]["score"], x[0]))
    print("LEADERBOARD:")
    previous_score = None
    rank = 0
    for index, (team, data) in enumerate(ranked):
        if data["score"] != previous_score:
            rank = index + 1
        print(f"{rank}. {team}: {data['score']:.2%} ({data['raw_total']}/{data['raw_possible']})")
        previous_score = data["score"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()

    totals, invalid_results, csv_teams = compute_totals(args.results)

    print_ranked_results(totals)
   
    if invalid_results:
        print("\nINVALID SUBMISSIONS:")
        for invalid in invalid_results:
            print(f"{invalid['team']}: {invalid['error']}")

    no_graded_cases = sorted(csv_teams - set(totals.keys()))
    if no_graded_cases:
        print("\nNO GRADED CASES (submitted, but nothing counted toward a score):")
        for team in no_graded_cases:
            print(team)


if __name__ == "__main__":
    main()
