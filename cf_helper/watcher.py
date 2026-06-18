import os
import time

from .colors import print_info, print_header, print_warn, bold, dim, cyan
from .runner import run_tests
from .config import load_config, LANGUAGE_EXTENSIONS


WATCH_EXTENSIONS = set(LANGUAGE_EXTENSIONS.values())


def get_file_mtimes(directory):
    mtimes = {}
    for f in os.listdir(directory):
        if any(f.endswith(ext) for ext in WATCH_EXTENSIONS):
            path = os.path.join(directory, f)
            try:
                mtimes[path] = os.path.getmtime(path)
            except OSError:
                pass
    return mtimes


def watch(problem_dir, cfg=None, interval=1.0):
    if cfg is None:
        cfg = load_config()

    problem_dir = os.path.abspath(problem_dir)
    problem_name = os.path.basename(problem_dir)

    print_header(f"Watching Problem {problem_name.upper()}")
    print_info(f"Monitoring {problem_dir} for changes...")
    print_info(f"Press Ctrl+C to stop\n")

    last_mtimes = get_file_mtimes(problem_dir)
    run_tests(problem_dir, cfg)

    try:
        while True:
            time.sleep(interval)
            current_mtimes = get_file_mtimes(problem_dir)

            changed = False
            for path, mtime in current_mtimes.items():
                if path not in last_mtimes or last_mtimes[path] != mtime:
                    changed = True
                    print_info(f"Change detected: {os.path.basename(path)}")
                    break

            if changed:
                last_mtimes = current_mtimes
                print()
                run_tests(problem_dir, cfg)
                print(dim(f"\n  Watching for changes... (Ctrl+C to stop)"))

    except KeyboardInterrupt:
        print(f"\n{cyan('  Stopped watching.')}")
