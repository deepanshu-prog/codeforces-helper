import argparse
import os
import sys

from . import __version__
from .colors import print_header, print_info, print_success, print_fail, print_warn, bold, cyan, dim


def create_parser():
    parser = argparse.ArgumentParser(
        prog="cf",
        description="Codeforces Helper — scrape test cases, run solutions, stress test, and more",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  cf fetch 1234                   Scrape contest 1234
  cf fetch https://codeforces.com/gym/104000
  cf test 1234/A                  Run tests for problem A
  cf test 1234/A -l python        Test Python solution
  cf watch 1234/B                 Auto-retest on file changes
  cf stress 1234/C                Stress test with gen.cpp + brute.cpp
  cf add-test 1234/A              Add a custom test case
  cf standings 1234               Show contest standings
  cf info 1234                    Show contest info & problems
  cf status yourhandle            Show your recent submissions
  cf status yourhandle -c 1234    Filter by contest
  cf archive                      Show your solved/attempted problems
  cf solved 1234 A                Mark problem as solved
  cf config                       Show current config
  cf config --lang python         Set default language
""",
    )

    parser.add_argument("-v", "--version", action="version", version=f"cf-helper {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # fetch
    fetch = subparsers.add_parser("fetch", help="Scrape test cases from a contest")
    fetch.add_argument("contest", help="Contest ID or full URL")
    fetch.add_argument("-l", "--lang", choices=["cpp", "python", "java"], help="Language for solution template")
    fetch.add_argument("-o", "--output", help="Output directory")

    # test
    test = subparsers.add_parser("test", help="Run tests for a problem")
    test.add_argument("problem", help="Path to problem directory (e.g., 1234/A)")
    test.add_argument("-l", "--lang", choices=["cpp", "python", "java"], help="Language override")
    test.add_argument("-t", "--tests", nargs="+", help="Specific test numbers to run")

    # watch
    watch = subparsers.add_parser("watch", help="Watch for changes and auto-retest")
    watch.add_argument("problem", help="Path to problem directory (e.g., 1234/A)")
    watch.add_argument("-i", "--interval", type=float, default=1.0, help="Poll interval in seconds")

    # stress
    stress = subparsers.add_parser("stress", help="Stress test: compare solution against brute force")
    stress.add_argument("problem", help="Path to problem directory")
    stress.add_argument("-g", "--generator", help="Path to generator file (default: gen.cpp)")
    stress.add_argument("-b", "--brute", help="Path to brute force file (default: brute.cpp)")
    stress.add_argument("-n", "--iterations", type=int, default=1000, help="Number of iterations (default: 1000)")

    # add-test
    addtest = subparsers.add_parser("add-test", help="Add a custom test case")
    addtest.add_argument("problem", help="Path to problem directory")
    addtest.add_argument("-i", "--input", help="Input data (or reads from stdin)")
    addtest.add_argument("-o", "--output", help="Expected output (optional)")

    # standings
    standings = subparsers.add_parser("standings", help="Show contest standings via Codeforces API")
    standings.add_argument("contest", help="Contest ID")
    standings.add_argument("-n", "--count", type=int, default=15, help="Number of rows to show")

    # info
    info = subparsers.add_parser("info", help="Show contest info and problem list")
    info.add_argument("contest", help="Contest ID")

    # status
    status = subparsers.add_parser("status", help="Show user's recent submissions")
    status.add_argument("handle", help="Codeforces handle")
    status.add_argument("-c", "--contest", help="Filter by contest ID")

    # archive
    archive = subparsers.add_parser("archive", help="Show your solved/attempted problems")
    archive.add_argument("-c", "--contest", help="Filter by contest ID")

    # solved
    solved = subparsers.add_parser("solved", help="Mark a problem as solved")
    solved.add_argument("contest", help="Contest ID")
    solved.add_argument("problem", help="Problem ID (e.g., A, B1)")
    solved.add_argument("-l", "--lang", default="cpp", help="Language used")

    # config
    config = subparsers.add_parser("config", help="Show or update configuration")
    config.add_argument("--lang", choices=["cpp", "python", "java"], help="Set default language")
    config.add_argument("--compiler", help="Set compiler (e.g., g++-12)")
    config.add_argument("--time-limit", type=float, help="Set time limit in seconds")
    config.add_argument("--template-dir", help="Set custom template directory")
    config.add_argument("--show", action="store_true", help="Show current config")

    return parser


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    from .config import load_config, save_config

    cfg = load_config()

    if args.command == "fetch":
        if args.lang:
            cfg["language"] = args.lang
        if args.output:
            cfg["output_dir"] = args.output
        from .scraper import scrape_contest
        scrape_contest(args.contest, cfg)

    elif args.command == "test":
        if args.lang:
            cfg["language"] = args.lang
        from .runner import run_tests
        run_tests(args.problem, cfg, specific_tests=args.tests)

    elif args.command == "watch":
        from .watcher import watch
        watch(args.problem, cfg, interval=args.interval)

    elif args.command == "stress":
        from .stress import stress_test
        stress_test(
            args.problem,
            generator_file=args.generator,
            brute_file=args.brute,
            iterations=args.iterations,
            cfg=cfg,
        )

    elif args.command == "add-test":
        from .runner import add_custom_test
        if args.input:
            input_data = args.input
        else:
            print_info("Enter test input (Ctrl+D / Ctrl+Z to finish):")
            input_data = sys.stdin.read()
        add_custom_test(args.problem, input_data, args.output)

    elif args.command == "standings":
        from .api import show_standings
        show_standings(args.contest, count=args.count)

    elif args.command == "info":
        from .api import show_contest_info
        show_contest_info(args.contest)

    elif args.command == "status":
        from .api import show_user_status
        show_user_status(args.handle, contest_id=args.contest)

    elif args.command == "archive":
        from .archive import show_archive
        show_archive(contest_id=args.contest)

    elif args.command == "solved":
        from .archive import mark_solved
        mark_solved(args.contest, args.problem.upper(), args.lang)

    elif args.command == "config":
        _handle_config(args, cfg)


def _handle_config(args, cfg):
    from .config import save_config

    changed = False

    if args.lang:
        cfg["language"] = args.lang
        changed = True
        print_success(f"Default language set to: {args.lang}")

    if args.compiler:
        lang = cfg["language"]
        cfg["compiler"][lang] = args.compiler
        changed = True
        print_success(f"Compiler for {lang} set to: {args.compiler}")

    if args.time_limit:
        cfg["time_limit"] = args.time_limit
        changed = True
        print_success(f"Time limit set to: {args.time_limit}s")

    if args.template_dir:
        path = os.path.abspath(args.template_dir)
        if os.path.isdir(path):
            cfg["template_dir"] = path
            changed = True
            print_success(f"Template directory set to: {path}")
        else:
            print_fail(f"Directory not found: {args.template_dir}")

    if changed:
        save_config(cfg)
    elif args.show or not changed:
        print_header("Current Configuration")
        import json
        for key, value in cfg.items():
            if isinstance(value, dict):
                print(f"  {bold(key)}:")
                for k, v in value.items():
                    print(f"    {k}: {cyan(str(v))}")
            else:
                print(f"  {bold(key)}: {cyan(str(value))}")
