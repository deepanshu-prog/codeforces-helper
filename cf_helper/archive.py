import json
import os
import time

from .config import ARCHIVE_FILE, ensure_config_dir
from .colors import print_success, print_info, print_header, green, red, yellow, bold, dim


def load_archive():
    ensure_config_dir()
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r") as f:
            return json.load(f)
    return {"contests": {}, "problems": {}}


def save_archive(archive):
    ensure_config_dir()
    with open(ARCHIVE_FILE, "w") as f:
        json.dump(archive, f, indent=2)


def mark_solved(contest_id, problem_id, language="cpp"):
    archive = load_archive()
    key = f"{contest_id}/{problem_id}"
    archive["problems"][key] = {
        "status": "solved",
        "language": language,
        "solved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if str(contest_id) not in archive["contests"]:
        archive["contests"][str(contest_id)] = {
            "first_attempt": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    save_archive(archive)
    print_success(f"Marked {key} as solved ({language})")


def mark_attempted(contest_id, problem_id):
    archive = load_archive()
    key = f"{contest_id}/{problem_id}"
    if key not in archive["problems"]:
        archive["problems"][key] = {
            "status": "attempted",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_archive(archive)


def show_archive(contest_id=None):
    archive = load_archive()

    if not archive["problems"]:
        print_info("No problems tracked yet. Solve some problems first!")
        return

    print_header("Problem Archive")

    problems = archive["problems"]
    if contest_id:
        problems = {k: v for k, v in problems.items() if k.startswith(f"{contest_id}/")}

    solved = sum(1 for v in problems.values() if v.get("status") == "solved")
    attempted = sum(1 for v in problems.values() if v.get("status") == "attempted")
    total = len(problems)

    print(f"  Total: {bold(str(total))} | {green(f'Solved: {solved}')} | {yellow(f'Attempted: {attempted}')}\n")

    current_contest = None
    for key in sorted(problems.keys()):
        contest, problem = key.split("/")
        if contest != current_contest:
            current_contest = contest
            print(f"  {bold(f'Contest {contest}')}")

        info = problems[key]
        status = info.get("status", "unknown")
        lang = info.get("language", "")
        date = info.get("solved_at", info.get("started_at", ""))

        if status == "solved":
            icon = green("✓")
            status_str = green("solved")
        else:
            icon = yellow("○")
            status_str = yellow("attempted")

        lang_str = dim(f"({lang})") if lang else ""
        date_str = dim(date) if date else ""
        print(f"    {icon} {problem:<5} {status_str:<12} {lang_str:<10} {date_str}")

    print()


def get_stats():
    archive = load_archive()
    problems = archive["problems"]
    return {
        "total": len(problems),
        "solved": sum(1 for v in problems.values() if v.get("status") == "solved"),
        "attempted": sum(1 for v in problems.values() if v.get("status") == "attempted"),
        "contests": len(archive["contests"]),
    }
