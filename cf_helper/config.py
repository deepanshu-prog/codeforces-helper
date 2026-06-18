import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".cfhelper")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
ARCHIVE_FILE = os.path.join(CONFIG_DIR, "archive.json")

DEFAULTS = {
    "language": "cpp",
    "compiler": {
        "cpp": "g++",
        "java": "javac",
        "python": "python3",
    },
    "compiler_flags": {
        "cpp": ["-std=c++17", "-O2", "-Wall", "-Wextra"],
        "java": [],
        "python": [],
    },
    "run_command": {
        "cpp_win": "a.exe",
        "cpp_unix": "./a.out",
        "java": "java Solution",
        "python_win": "python solution.py",
        "python_unix": "python3 solution.py",
    },
    "time_limit": 3.0,
    "template_dir": "",
    "output_dir": ".",
    "auto_open_editor": False,
    "editor": "",
}

LANGUAGE_EXTENSIONS = {
    "cpp": ".cpp",
    "python": ".py",
    "java": ".java",
}

SOLUTION_FILENAMES = {
    "cpp": "solution.cpp",
    "python": "solution.py",
    "java": "Solution.java",
}


def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config():
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            user_cfg = json.load(f)
        merged = {**DEFAULTS, **user_cfg}
        for key in ("compiler", "compiler_flags", "run_command"):
            if key in DEFAULTS and isinstance(DEFAULTS[key], dict):
                merged[key] = {**DEFAULTS[key], **user_cfg.get(key, {})}
        return merged
    return DEFAULTS.copy()


def save_config(cfg):
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def get_compiler(cfg, lang=None):
    lang = lang or cfg["language"]
    return cfg["compiler"].get(lang, "")


def get_compiler_flags(cfg, lang=None):
    lang = lang or cfg["language"]
    return cfg["compiler_flags"].get(lang, [])


def get_run_command(cfg, lang=None):
    lang = lang or cfg["language"]
    is_win = os.name == "nt"
    key = f"{lang}_win" if is_win else f"{lang}_unix"
    if key in cfg["run_command"]:
        return cfg["run_command"][key]
    return cfg["run_command"].get(lang, "")


def get_solution_filename(cfg, lang=None):
    lang = lang or cfg["language"]
    return SOLUTION_FILENAMES.get(lang, f"solution{LANGUAGE_EXTENSIONS.get(lang, '')}")
