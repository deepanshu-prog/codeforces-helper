import os
import sys


def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")  # enable ANSI on Windows 10+
        return True
    return True


USE_COLOR = _supports_color()


def _wrap(code, text):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def green(text):
    return _wrap("32", text)


def red(text):
    return _wrap("31", text)


def yellow(text):
    return _wrap("33", text)


def cyan(text):
    return _wrap("36", text)


def bold(text):
    return _wrap("1", text)


def dim(text):
    return _wrap("2", text)


def green_bg(text):
    return _wrap("42;30", text)


def red_bg(text):
    return _wrap("41;37", text)


def print_success(msg):
    print(green(f"  ✓ {msg}"))


def print_fail(msg):
    print(red(f"  ✗ {msg}"))


def print_warn(msg):
    print(yellow(f"  ⚠ {msg}"))


def print_info(msg):
    print(cyan(f"  ℹ {msg}"))


def print_header(msg):
    print(bold(f"\n{'─' * 50}"))
    print(bold(f"  {msg}"))
    print(bold(f"{'─' * 50}"))


def print_diff(expected, actual):
    exp_lines = expected.strip().splitlines()
    act_lines = actual.strip().splitlines()
    max_lines = max(len(exp_lines), len(act_lines))

    print(f"  {'Expected':<40} {'Got':<40}")
    print(f"  {'─' * 40} {'─' * 40}")

    for i in range(max_lines):
        exp = exp_lines[i] if i < len(exp_lines) else ""
        act = act_lines[i] if i < len(act_lines) else ""
        if exp == act:
            print(f"  {dim(exp):<50} {dim(act):<50}")
        else:
            print(f"  {green(exp):<50} {red(act):<50}")
