import re
import os
import sys
import time
import urllib.request
import urllib.error
from shutil import copyfile

from bs4 import BeautifulSoup

from .colors import print_success, print_fail, print_warn, print_info, print_header
from .config import load_config, get_solution_filename

CODEFORCES_BASE = "https://codeforces.com"

URL_PATTERNS = {
    "contest": re.compile(r"https://codeforces\.com/contest/(\d+)"),
    "gym": re.compile(r"https://codeforces\.com/gym/(\d+)"),
    "problemset": re.compile(r"https://codeforces\.com/problemset/problem/(\d+)/([A-Z0-9]+)"),
    "group_contest": re.compile(r"https://codeforces\.com/group/\w+/contest/(\d+)"),
}


class ScraperError(Exception):
    pass


class NetworkError(ScraperError):
    pass


class ParseError(ScraperError):
    pass


def fetch_page(url, retries=3, delay=2.0):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; cf-helper/2.0)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, retries + 1):
        try:
            response = urllib.request.urlopen(req, timeout=15)
            html = response.read()
            return BeautifulSoup(html, "html.parser")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = delay * attempt * 2
                print_warn(f"Rate limited (429). Waiting {wait:.0f}s before retry...")
                time.sleep(wait)
            elif e.code == 404:
                raise NetworkError(f"Page not found (404): {url}")
            else:
                if attempt < retries:
                    print_warn(f"HTTP {e.code} on attempt {attempt}/{retries}. Retrying...")
                    time.sleep(delay * attempt)
                else:
                    raise NetworkError(f"HTTP error {e.code} after {retries} attempts: {url}")
        except urllib.error.URLError as e:
            if attempt < retries:
                print_warn(f"Connection error on attempt {attempt}/{retries}: {e.reason}")
                time.sleep(delay * attempt)
            else:
                raise NetworkError(f"Connection failed after {retries} attempts: {e.reason}")
        except Exception as e:
            if attempt < retries:
                print_warn(f"Error on attempt {attempt}/{retries}: {e}")
                time.sleep(delay * attempt)
            else:
                raise NetworkError(f"Failed after {retries} attempts: {e}")

    raise NetworkError(f"Failed to fetch {url}")


def parse_url(user_input):
    user_input = user_input.strip()

    if user_input.isdigit():
        return "contest", int(user_input), f"{CODEFORCES_BASE}/contest/{user_input}"

    for url_type, pattern in URL_PATTERNS.items():
        match = pattern.search(user_input)
        if match:
            return url_type, int(match.group(1)), user_input

    raise ScraperError(
        f"Invalid input: '{user_input}'\n"
        "  Accepted formats:\n"
        "    - Contest ID:    1234\n"
        "    - Contest URL:   https://codeforces.com/contest/1234\n"
        "    - Gym URL:       https://codeforces.com/gym/1234\n"
        "    - Problem URL:   https://codeforces.com/problemset/problem/1234/A\n"
        "    - Group contest: https://codeforces.com/group/xxx/contest/1234"
    )


def get_question_links(soup, url_type="contest"):
    links = []
    if url_type == "contest" or url_type == "gym" or url_type == "group_contest":
        pattern = re.compile(r"/(?:contest|gym)/\d+/problem/([A-Z0-9]+)")
    else:
        pattern = re.compile(r"/problemset/problem/\d+/([A-Z0-9]+)")

    for tag in soup.find_all("a"):
        href = tag.get("href", "")
        match = pattern.search(href)
        if match:
            problem_id = match.group(1)
            if problem_id not in links:
                links.append(problem_id)

    if not links:
        table = soup.find("table", {"class": "problems"})
        if table:
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if cells:
                    text = cells[0].get_text(strip=True)
                    if re.match(r"^[A-Z0-9]+$", text) and text not in links:
                        links.append(text)

    return links


def extract_test_cases(soup):
    sample_tests = soup.find("div", {"class": "sample-test"})
    if not sample_tests:
        return []

    inputs = sample_tests.find_all("div", {"class": "input"})
    outputs = sample_tests.find_all("div", {"class": "output"})

    test_cases = []
    for inp, out in zip(inputs, outputs):
        inp_pre = inp.find("pre")
        out_pre = out.find("pre")
        if inp_pre and out_pre:
            input_text = _extract_pre_text(inp_pre)
            output_text = _extract_pre_text(out_pre)
            test_cases.append((input_text, output_text))

    if not test_cases:
        raw = sample_tests.get_text("\n").strip() if sample_tests.find("br") else sample_tests.get_text().strip()
        test_cases = _parse_raw_test_cases(raw)

    return test_cases


def _extract_pre_text(pre_tag):
    for br in pre_tag.find_all("br"):
        br.replace_with("\n")
    lines = []
    for child in pre_tag.children:
        text = child.get_text() if hasattr(child, "get_text") else str(child)
        lines.append(text)
    return "\n".join(lines).strip() + "\n"


def _parse_raw_test_cases(raw):
    test_cases = []
    lines = raw.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].strip() == "Input":
            i += 1
            input_data = ""
            while i < len(lines) and lines[i].strip() != "Output":
                input_data += lines[i] + "\n"
                i += 1
            if i < len(lines) and lines[i].strip() == "Output":
                i += 1
                output_data = ""
                while i < len(lines) and lines[i].strip() != "Input":
                    output_data += lines[i] + "\n"
                    i += 1
                test_cases.append((input_data, output_data))
        else:
            i += 1
    return test_cases


def get_problem_url(base_url, url_type, problem_id):
    if url_type == "problemset":
        return f"{base_url}"
    return f"{base_url}/problem/{problem_id}"


def find_template(cfg, lang=None):
    lang = lang or cfg["language"]
    filename = get_solution_filename(cfg, lang)

    if cfg.get("template_dir"):
        path = os.path.join(cfg["template_dir"], filename)
        if os.path.exists(path):
            return path

    builtin = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", filename)
    if os.path.exists(builtin):
        return builtin

    legacy = os.path.join(os.path.dirname(os.path.dirname(__file__)), "template.cpp")
    if lang == "cpp" and os.path.exists(legacy):
        return legacy

    return None


def create_problem_files(contest_dir, problem_id, test_cases, cfg):
    lang = cfg.get("language", "cpp")
    problem_dir = os.path.join(contest_dir, problem_id)
    os.makedirs(problem_dir, exist_ok=True)

    for i, (inp, out) in enumerate(test_cases, 1):
        input_file = os.path.join(problem_dir, f"input{i}.txt")
        output_file = os.path.join(problem_dir, f"output{i}.txt")

        with open(input_file, "w", newline="\n") as f:
            f.write(inp)
        print_success(f"Written {input_file}")

        with open(output_file, "w", newline="\n") as f:
            f.write(out)
        print_success(f"Written {output_file}")

    solution_file = os.path.join(problem_dir, get_solution_filename(cfg, lang))
    if not os.path.exists(solution_file):
        template = find_template(cfg, lang)
        if template:
            copyfile(template, solution_file)
            print_success(f"Created {solution_file} from template")
        else:
            with open(solution_file, "w") as f:
                f.write("")
            print_warn(f"Created empty {solution_file} (no template found)")
    else:
        print_info(f"{solution_file} already exists, skipping")

    return problem_dir


def scrape_contest(user_input, cfg=None):
    if cfg is None:
        cfg = load_config()

    url_type, contest_id, base_url = parse_url(user_input)
    print_header(f"Fetching contest {contest_id} ({url_type})")

    if url_type == "problemset":
        match = URL_PATTERNS["problemset"].search(base_url)
        contest_dir = os.path.join(cfg.get("output_dir", "."), str(match.group(1)))
        os.makedirs(contest_dir, exist_ok=True)
        problem_id = match.group(2)

        print_info(f"Fetching problem {problem_id}...")
        soup = fetch_page(base_url)
        test_cases = extract_test_cases(soup)

        if not test_cases:
            print_fail(f"No test cases found for problem {problem_id}")
            return contest_dir

        print_success(f"Found {len(test_cases)} test case(s) for problem {problem_id}")
        create_problem_files(contest_dir, problem_id, test_cases, cfg)
        return contest_dir

    soup = fetch_page(base_url)
    problem_ids = get_question_links(soup, url_type)

    if not problem_ids:
        print_fail("No problems found. The contest may not have started yet.")
        sys.exit(1)

    print_success(f"Found {len(problem_ids)} problem(s): {', '.join(problem_ids)}")

    contest_dir = os.path.join(cfg.get("output_dir", "."), str(contest_id))
    os.makedirs(contest_dir, exist_ok=True)

    for pid in problem_ids:
        problem_url = get_problem_url(base_url, url_type, pid)
        print_info(f"Fetching problem {pid}...")

        try:
            problem_soup = fetch_page(problem_url)
            test_cases = extract_test_cases(problem_soup)

            if not test_cases:
                print_warn(f"No test cases found for problem {pid}")
                os.makedirs(os.path.join(contest_dir, pid), exist_ok=True)
                continue

            print_success(f"Found {len(test_cases)} test case(s) for problem {pid}")
            create_problem_files(contest_dir, pid, test_cases, cfg)

        except NetworkError as e:
            print_fail(f"Failed to fetch problem {pid}: {e}")
            continue

    print_header(f"Contest {contest_id} ready in ./{contest_id}/")
    return contest_dir
