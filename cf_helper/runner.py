import os
import re
import subprocess
import time

from .colors import (
    print_success, print_fail, print_warn, print_info, print_header,
    print_diff, green, red, yellow, bold, dim, cyan
)
from .config import load_config, get_compiler, get_compiler_flags, get_run_command, get_solution_filename


class TestResult:
    def __init__(self, test_num, passed, expected, actual, time_elapsed, status="ok"):
        self.test_num = test_num
        self.passed = passed
        self.expected = expected
        self.actual = actual
        self.time_elapsed = time_elapsed
        self.status = status  # ok, tle, rte, ce


def find_solution_file(problem_dir, cfg):
    for lang in ["cpp", "python", "java"]:
        filename = get_solution_filename(cfg, lang)
        path = os.path.join(problem_dir, filename)
        if os.path.exists(path):
            return path, lang
    return None, None


def compile_solution(problem_dir, lang, cfg):
    if lang == "python":
        return True

    solution_file = get_solution_filename(cfg, lang)
    compiler = get_compiler(cfg, lang)
    flags = get_compiler_flags(cfg, lang)

    if lang == "cpp":
        output = "a.exe" if os.name == "nt" else "a.out"
        cmd = [compiler] + flags + [solution_file, "-o", output]
    elif lang == "java":
        cmd = [compiler] + flags + [solution_file]
    else:
        return True

    print_info(f"Compiling {solution_file} with {compiler}...")

    try:
        result = subprocess.run(
            cmd,
            cwd=problem_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print_fail("Compilation failed:")
            print(red(result.stderr))
            return False
        print_success("Compilation successful")
        return True
    except FileNotFoundError:
        print_fail(f"Compiler '{compiler}' not found. Install it or update config.")
        return False
    except subprocess.TimeoutExpired:
        print_fail("Compilation timed out (30s)")
        return False


def run_single_test(problem_dir, input_file, lang, cfg):
    run_cmd = get_run_command(cfg, lang)
    time_limit = cfg.get("time_limit", 3.0)

    input_path = os.path.join(problem_dir, input_file)
    with open(input_path, "r") as f:
        input_data = f.read()

    if os.name == "nt":
        if lang == "cpp":
            cmd = [os.path.join(problem_dir, "a.exe")]
        elif lang == "python":
            cmd = ["python", os.path.join(problem_dir, "solution.py")]
        elif lang == "java":
            cmd = ["java", "-cp", problem_dir, "Solution"]
        else:
            cmd = run_cmd.split()
    else:
        if lang == "cpp":
            cmd = [os.path.join(problem_dir, "a.out")]
        elif lang == "python":
            cmd = ["python3", os.path.join(problem_dir, "solution.py")]
        elif lang == "java":
            cmd = ["java", "-cp", problem_dir, "Solution"]
        else:
            cmd = run_cmd.split()

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=time_limit,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return result.stdout, elapsed, "rte", result.stderr
        return result.stdout, elapsed, "ok", ""

    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return "", elapsed, "tle", ""
    except FileNotFoundError:
        return "", 0, "rte", f"Executable not found: {cmd[0]}"


def run_tests(problem_dir, cfg=None, specific_tests=None):
    if cfg is None:
        cfg = load_config()

    problem_dir = os.path.abspath(problem_dir)
    problem_name = os.path.basename(problem_dir)

    solution_path, lang = find_solution_file(problem_dir, cfg)
    if not solution_path:
        print_fail(f"No solution file found in {problem_dir}")
        return []

    print_header(f"Testing Problem {problem_name.upper()} ({lang})")

    if not compile_solution(problem_dir, lang, cfg):
        return []

    files = os.listdir(problem_dir)
    input_files = sorted(
        [f for f in files if re.match(r"input\d+\.txt$", f)],
        key=lambda x: int(re.search(r"\d+", x).group())
    )

    if specific_tests:
        input_files = [f for f in input_files if re.search(r"\d+", f).group() in specific_tests]

    if not input_files:
        print_warn("No test case files found")
        return []

    print_info(f"Running {len(input_files)} test case(s)...\n")

    results = []
    time_limit = cfg.get("time_limit", 3.0)

    for input_file in input_files:
        test_num = re.search(r"\d+", input_file).group()
        output_file = f"output{test_num}.txt"
        output_path = os.path.join(problem_dir, output_file)

        if not os.path.exists(output_path):
            print_warn(f"Test {test_num}: No expected output file ({output_file}), skipping")
            continue

        with open(output_path, "r") as f:
            expected = f.read().strip()

        actual, elapsed, status, stderr = run_single_test(problem_dir, input_file, lang, cfg)
        actual = actual.strip()

        time_str = f"{elapsed * 1000:.0f}ms"
        time_color = red if elapsed > time_limit * 0.8 else (yellow if elapsed > time_limit * 0.5 else green)

        if status == "tle":
            print_fail(f"Test {test_num}: {red('TIME LIMIT EXCEEDED')} [{red(time_str)}]")
            result = TestResult(test_num, False, expected, actual, elapsed, "tle")
        elif status == "rte":
            print_fail(f"Test {test_num}: {red('RUNTIME ERROR')} [{time_color(time_str)}]")
            if stderr:
                print(dim(f"    {stderr[:200]}"))
            result = TestResult(test_num, False, expected, actual, elapsed, "rte")
        elif expected == actual:
            print_success(f"Test {test_num}: {green('PASSED')} [{time_color(time_str)}]")
            result = TestResult(test_num, True, expected, actual, elapsed)
        else:
            print_fail(f"Test {test_num}: {red('WRONG ANSWER')} [{time_color(time_str)}]")
            print_diff(expected, actual)
            result = TestResult(test_num, False, expected, actual, elapsed)

        results.append(result)

    _print_summary(results)
    return results


def _print_summary(results):
    if not results:
        return

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    avg_time = sum(r.time_elapsed for r in results) / total * 1000
    max_time = max(r.time_elapsed for r in results) * 1000

    print(f"\n{'─' * 50}")
    if passed == total:
        print(green(bold(f"  All {total} test(s) passed!")))
    else:
        print(red(bold(f"  {passed}/{total} test(s) passed")))
    print(dim(f"  Avg: {avg_time:.0f}ms | Max: {max_time:.0f}ms"))
    print(f"{'─' * 50}")


def add_custom_test(problem_dir, input_data, expected_output=None):
    files = os.listdir(problem_dir)
    existing = [f for f in files if re.match(r"input\d+\.txt$", f)]
    next_num = len(existing) + 1

    input_file = os.path.join(problem_dir, f"input{next_num}.txt")
    with open(input_file, "w", newline="\n") as f:
        f.write(input_data if input_data.endswith("\n") else input_data + "\n")
    print_success(f"Created {input_file}")

    if expected_output is not None:
        output_file = os.path.join(problem_dir, f"output{next_num}.txt")
        with open(output_file, "w", newline="\n") as f:
            f.write(expected_output if expected_output.endswith("\n") else expected_output + "\n")
        print_success(f"Created {output_file}")

    return next_num
