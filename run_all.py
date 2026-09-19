"""Single entrypoint for a scheduled run: score every team in one challenge,
then rank them.

Whatever ends up triggering this on a schedule (GitHub Actions, a cron job,
a scheduled agent) just needs to run this one command per challenge, e.g.:

    python run_all.py --challenge challenge_1

Submissions are scoped per challenge (teams/<challenge>/<team>/skill.md),
so this only ever grades one challenge at a time; run it again with a
different --challenge for another one. score_submission.py's own hash check
skips any team whose skill/cases/grading code hasn't changed since its last
graded run, so repeated scheduled runs only pay for API calls on submissions
that actually changed.
"""

import argparse
import glob
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--challenge", required=True, help="e.g. challenge_1")
    parser.add_argument("--teams-root", default="teams")
    parser.add_argument("--cases-root", default="test_cases")
    parser.add_argument("--out-root", default="results")
    parser.add_argument("--force", action="store_true", help="Re-grade every team, ignoring cached results")
    args = parser.parse_args()

    teams_dir = os.path.join(args.teams_root, args.challenge)
    cases_dir = os.path.join(args.cases_root, args.challenge)
    out_dir = os.path.join(args.out_root, args.challenge)

    team_dirs = sorted(
        d for d in glob.glob(os.path.join(teams_dir, "*"))
        if os.path.isdir(d) and os.path.basename(d) != "_template"
    )

    for team_dir in team_dirs:
        skill_path = os.path.join(team_dir, "skill.md")
        if not os.path.isfile(skill_path):
            print(f"Skipping {team_dir}: no skill.md")
            continue

        cmd = [sys.executable, "score_submission.py", "--skill", skill_path, "--cases", cases_dir, "--out", out_dir]
        if args.force:
            cmd.append("--force")
        subprocess.run(cmd, check=False)

    subprocess.run([sys.executable, "run_competition.py", "--results", out_dir], check=False)


if __name__ == "__main__":
    main()
