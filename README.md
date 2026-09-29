# Leaderboard

Grades team-submitted skills against a challenge's test cases
and ranks teams on a leaderboard. One repo, one folder per challenge.

## Layout

```
teams/<challenge>/<team>/skill.md    # a team's submission
test_cases/<challenge>/*.yaml        # that challenge's graded cases
graders/grader_<challenge>.py        # grading logic for that challenge's category
results/<challenge>/                 # per-team CSVs, .invalid files, history.jsonl
```

A challenge is just a folder name shared across `teams/`, `test_cases/`,
and `results/`. Adding a new challenge means adding a new folder under
each, plus a matching grader module registered in `graders/__init__.py`.

## Submitting a skill

A skill needs to have `name`, `description`,
and `instructions` filled out. `instructions` must contain the literal placeholder
that the case's grader expects (e.g. `{tickets}` for `challenge_1`), since
that's where the real test data gets substituted in before your prompt runs.

## Grading

**One team, one challenge:**
```
python score_submission.py --skill teams/challenge_1/your-team/skill.md --cases test_cases/challenge_1
```
Writes `results/<challenge>/<team>.csv` (or `.invalid` if the skill fails
validation). Requires `OPENROUTER_API_KEY` in the environment. Re-running with
nothing changed (skill, cases, or grading code) costs zero API calls — add
`--force` to override that cache.

**Everyone, one challenge, plus the leaderboard:**
```
python run_all.py --challenge challenge_1
```

**Best-ever standings** (each team's highest score across every day this has
been run, not just today) — run this instead of/after `run_all.py` when you
want the leaderboard to reflect history, not a single day:
```
python run_all.py --challenge challenge_1
python update_history.py --challenge challenge_1
```
`update_history.py` appends today's result to `results/<challenge>/history.jsonl`
and reports each team's best day so far. Ties are shown as ties (equal
scores share a rank).

## Practicing locally (no effect on the real leaderboard)

```
npm install
OPENROUTER_API_KEY=... npm run benchmark -- --skill teams/challenge_1/your-team/skill.md --challenge challenge_1
```
Runs your skill against that challenge's practice cases on your own
machine — free, unlimited, never touches the real leaderboard.
First run finds and uses a local Python venv automatically.

## Daily automation

`.github/workflows/daily-leaderboard.yml` runs `run_all.py` +
`update_history.py` once a day (schedule is UTC — check the cron comment
for the intended local time) and publishes the standings as the workflow's
job summary. Trigger it manually via `workflow_dispatch` to test, or to
grade a specific challenge by name (defaults to `challenge_1` otherwise).
Needs `OPENROUTER_API_KEY` set as a repo secret. Not included yet.

## Adding a new challenge

1. `test_cases/<new-challenge>/*.yaml` — the graded cases, each with a
   `category` field.
2. `graders/grader_<new-challenge>.py` — exposing `build_prompt(case, instructions)`
   and `score(case, response_text)`; register it in `graders/__init__.py`
   under that `category` name.
3. `teams/<new-challenge>/_template/skill.md` — the submission template.

Nothing in `score_submission.py`, `run_competition.py`, `run_all.py`, or
`update_history.py` needs to change — they're all challenge-agnostic.
