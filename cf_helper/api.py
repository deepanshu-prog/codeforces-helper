import json
import time
import urllib.request
import urllib.error

from .colors import print_success, print_fail, print_info, print_header, print_warn
from .colors import green, red, yellow, bold, dim, cyan

CF_API = "https://codeforces.com/api"


class APIError(Exception):
    pass


def _api_call(method, params=None):
    url = f"{CF_API}/{method}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        url = f"{url}?{query}"

    try:
        response = urllib.request.urlopen(url, timeout=15)
        data = json.loads(response.read())
        if data.get("status") != "OK":
            raise APIError(data.get("comment", "Unknown API error"))
        return data.get("result")
    except urllib.error.HTTPError as e:
        raise APIError(f"HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise APIError(f"Connection error: {e.reason}")
    except json.JSONDecodeError:
        raise APIError("Invalid API response")


def get_contest_info(contest_id):
    contests = _api_call("contest.list")
    for c in contests:
        if c["id"] == int(contest_id):
            return c
    return None


def get_standings(contest_id, handle=None, count=10):
    params = {"contestId": contest_id, "count": count}
    if handle:
        params["handles"] = handle
    return _api_call("contest.standings", params)


def get_user_submissions(handle, contest_id=None, count=50):
    params = {"handle": handle, "count": count}
    result = _api_call("user.status", params)
    if contest_id:
        result = [s for s in result if s.get("contestId") == int(contest_id)]
    return result


def get_user_info(handle):
    result = _api_call("user.info", {"handles": handle})
    return result[0] if result else None


def get_contest_problems(contest_id):
    result = _api_call("contest.standings", {"contestId": contest_id, "count": 1})
    return result.get("problems", [])


def show_standings(contest_id, count=15):
    print_header(f"Contest {contest_id} Standings")
    try:
        data = get_standings(contest_id, count=count)
        problems = data.get("problems", [])
        rows = data.get("rows", [])

        problem_indices = [p["index"] for p in problems]
        header = f"  {'#':<5} {'Handle':<25} {'Score':<8} " + " ".join(f"{p:>4}" for p in problem_indices)
        print(bold(header))
        print(f"  {'─' * len(header)}")

        for i, row in enumerate(rows[:count], 1):
            party = row["party"]["members"][0]["handle"] if row["party"]["members"] else "?"
            points = int(row.get("points", 0))
            results = row.get("problemResults", [])

            result_strs = []
            for r in results:
                pts = int(r.get("points", 0))
                rejected = r.get("rejectedAttemptCount", 0)
                if pts > 0:
                    result_strs.append(green(f"{pts:>4}"))
                elif rejected > 0:
                    result_strs.append(red(f"  -{rejected}"))
                else:
                    result_strs.append(dim(f"   ."))

            print(f"  {i:<5} {party:<25} {points:<8} " + " ".join(result_strs))

    except APIError as e:
        print_fail(f"API error: {e}")


def show_user_status(handle, contest_id=None):
    print_header(f"Submissions for {handle}")
    try:
        submissions = get_user_submissions(handle, contest_id)

        if not submissions:
            print_info("No submissions found")
            return

        for sub in submissions[:20]:
            problem = sub.get("problem", {})
            pid = f"{problem.get('contestId', '?')}{problem.get('index', '?')}"
            verdict = sub.get("verdict", "TESTING")
            lang = sub.get("programmingLanguage", "?")
            time_ms = sub.get("timeConsumedMillis", 0)
            mem_kb = sub.get("memoryConsumedBytes", 0) // 1024

            if verdict == "OK":
                v_str = green("AC")
            elif verdict == "WRONG_ANSWER":
                v_str = red("WA")
            elif verdict == "TIME_LIMIT_EXCEEDED":
                v_str = yellow("TLE")
            elif verdict == "RUNTIME_ERROR":
                v_str = red("RTE")
            elif verdict == "COMPILATION_ERROR":
                v_str = red("CE")
            elif verdict == "MEMORY_LIMIT_EXCEEDED":
                v_str = yellow("MLE")
            else:
                v_str = dim(verdict[:6])

            test_count = sub.get("passedTestCount", 0)
            print(f"  {pid:<8} {v_str:<16} {lang:<20} {time_ms:>5}ms {mem_kb:>6}KB  (test {test_count})")

    except APIError as e:
        print_fail(f"API error: {e}")


def show_contest_info(contest_id):
    try:
        info = get_contest_info(contest_id)
        if not info:
            print_fail(f"Contest {contest_id} not found")
            return

        name = info.get("name", "Unknown")
        phase = info.get("phase", "UNKNOWN")
        duration = info.get("durationSeconds", 0)
        start = info.get("startTimeSeconds", 0)

        phase_color = green if phase == "FINISHED" else (yellow if phase == "CODING" else dim)

        print_header(f"Contest {contest_id}")
        print(f"  Name:     {bold(name)}")
        print(f"  Phase:    {phase_color(phase)}")
        print(f"  Duration: {duration // 3600}h {(duration % 3600) // 60}m")

        if start:
            start_str = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(start))
            print(f"  Start:    {start_str}")

        print_info(f"URL: https://codeforces.com/contest/{contest_id}")

        try:
            problems = get_contest_problems(contest_id)
            if problems:
                print(f"\n  {'Idx':<5} {'Name':<40} {'Rating':<8}")
                print(f"  {'─' * 55}")
                for p in problems:
                    rating = p.get("rating", "?")
                    tags = ", ".join(p.get("tags", []))
                    print(f"  {p['index']:<5} {p['name']:<40} {str(rating):<8} {dim(tags)}")
        except APIError:
            pass

    except APIError as e:
        print_fail(f"API error: {e}")


def get_editorial_url(contest_id):
    return f"https://codeforces.com/blog/entry/{contest_id}"
