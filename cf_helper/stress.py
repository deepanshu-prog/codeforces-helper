import os
import subprocess
import time
import random
import tempfile

from .colors import print_success, print_fail, print_info, print_header, print_diff, green, red, yellow, bold, dim
from .config import load_config, get_compiler, get_compiler_flags
from .runner import compile_solution, find_solution_file


def compile_file(filepath, output_name, problem_dir, cfg, lang="cpp"):
    compiler = get_compiler(cfg, lang)
    flags = get_compiler_flags(cfg, lang)

    if lang == "cpp":
        cmd = [compiler] + flags + [filepath, "-o", output_name]
    else:
        return True

    result = subprocess.run(cmd, cwd=problem_dir, capture_output=True, text=True, timeout=30)
    return result.returncode == 0


def run_executable(exe_path, input_data, time_limit=3.0):
    try:
        result = subprocess.run(
            [exe_path],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=time_limit,
        )
        return result.stdout.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "", False


def stress_test(problem_dir, generator_file=None, brute_file=None, iterations=1000, cfg=None):
    if cfg is None:
        cfg = load_config()

    problem_dir = os.path.abspath(problem_dir)
    print_header("Stress Testing")

    solution_path, lang = find_solution_file(problem_dir, cfg)
    if not solution_path:
        print_fail("No solution file found")
        return False

    if lang != "cpp":
        print_fail("Stress testing currently supports C++ only")
        return False

    if not generator_file:
        generator_file = os.path.join(problem_dir, "gen.cpp")
    if not brute_file:
        brute_file = os.path.join(problem_dir, "brute.cpp")

    if not os.path.exists(generator_file):
        print_fail(f"Generator not found: {generator_file}")
        print_info("Create a gen.cpp that prints random test input to stdout")
        _write_sample_generator(os.path.join(problem_dir, "gen.cpp"))
        print_info("Sample generator created at gen.cpp — edit it and retry")
        return False

    if not os.path.exists(brute_file):
        print_fail(f"Brute force solution not found: {brute_file}")
        print_info("Create a brute.cpp with a correct (possibly slow) solution")
        return False

    is_win = os.name == "nt"
    ext = ".exe" if is_win else ""

    print_info("Compiling solutions...")

    sol_exe = os.path.join(problem_dir, f"sol_stress{ext}")
    gen_exe = os.path.join(problem_dir, f"gen_stress{ext}")
    brute_exe = os.path.join(problem_dir, f"brute_stress{ext}")

    compiler = get_compiler(cfg, "cpp")
    flags = get_compiler_flags(cfg, "cpp")

    for src, out, name in [
        (solution_path, sol_exe, "solution"),
        (generator_file, gen_exe, "generator"),
        (brute_file, brute_exe, "brute force"),
    ]:
        cmd = [compiler] + flags + [src, "-o", out]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print_fail(f"Failed to compile {name}: {result.stderr[:200]}")
            return False
        print_success(f"Compiled {name}")

    time_limit = cfg.get("time_limit", 3.0)
    print_info(f"Running {iterations} iterations (time limit: {time_limit}s)...\n")

    for i in range(1, iterations + 1):
        seed = str(random.randint(1, 10**9))

        try:
            gen_result = subprocess.run(
                [gen_exe, seed],
                capture_output=True, text=True, timeout=5,
            )
            test_input = gen_result.stdout
        except subprocess.TimeoutExpired:
            print_fail(f"Iteration {i}: Generator timed out")
            continue

        sol_out, sol_ok = run_executable(sol_exe, test_input, time_limit)
        brute_out, brute_ok = run_executable(brute_exe, test_input, time_limit * 3)

        if not sol_ok:
            print_fail(f"Iteration {i}: Solution crashed or TLE (seed={seed})")
            _save_failing_test(problem_dir, test_input, brute_out, i)
            return False

        if not brute_ok:
            print_fail(f"Iteration {i}: Brute force crashed or TLE (seed={seed})")
            continue

        if sol_out != brute_out:
            print_fail(f"\nIteration {i}: MISMATCH FOUND! (seed={seed})")
            print_info("Input:")
            print(dim(f"    {test_input[:500]}"))
            print_diff(brute_out, sol_out)
            _save_failing_test(problem_dir, test_input, brute_out, i)
            return False

        if i % 100 == 0 or i == iterations:
            print(f"  {green('✓')} {i}/{iterations} iterations passed", end="\r")

    print(f"\n")
    print_success(f"All {iterations} iterations passed! No counter-example found.")
    return True


def _save_failing_test(problem_dir, input_data, expected, iteration):
    input_file = os.path.join(problem_dir, "stress_fail_input.txt")
    output_file = os.path.join(problem_dir, "stress_fail_output.txt")

    with open(input_file, "w", newline="\n") as f:
        f.write(input_data)
    with open(output_file, "w", newline="\n") as f:
        f.write(expected + "\n" if expected else "")

    print_info(f"Failing test saved to {input_file} and {output_file}")


def _write_sample_generator(path):
    sample = """#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    mt19937 rng(atoi(argv[1]));

    // Customize your generator below
    int n = rng() % 10 + 1;  // n in [1, 10]
    cout << n << "\\n";
    for (int i = 0; i < n; i++) {
        cout << (int)(rng() % 100 + 1);  // values in [1, 100]
        if (i < n - 1) cout << " ";
    }
    cout << "\\n";
    return 0;
}
"""
    with open(path, "w") as f:
        f.write(sample)
