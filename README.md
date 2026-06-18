# Codeforces Helper v2.0

A powerful CLI tool for competitive programmers on [Codeforces](https://codeforces.com). Automates the tedious parts — scraping test cases, running solutions, stress testing — so you can focus on solving problems.

## Features

| Feature | Description |
|---|---|
| **Test Case Scraping** | Auto-extract sample inputs/outputs from any contest, gym, or problemset URL |
| **Multi-Language** | C++, Python, and Java templates with per-language compiler config |
| **Auto Test Runner** | Compile & run your solution against all test cases with colored pass/fail output |
| **Time Tracking** | Measures execution time per test case, flags potential TLE |
| **Diff Highlighting** | Side-by-side expected vs actual output on wrong answers |
| **Stress Testing** | Generate random inputs, compare fast solution against brute force |
| **Watch Mode** | Auto-recompile & retest whenever you save your solution file |
| **Custom Test Cases** | Add your own test cases beyond the scraped samples |
| **Codeforces API** | View standings, submissions, contest info directly from the terminal |
| **Problem Archive** | Track your solved/attempted problems across contests |
| **Config System** | Persistent settings for language, compiler, flags, time limits |
| **Cross-Platform** | Works on Windows, Linux, and macOS |

## Installation

**Requirements:** Python 3.8+ and a compiler for your language (g++, javac, etc.)

```bash
git clone https://github.com/deepanshu-prog/codeforces-helper-.git
cd codeforces-helper-
pip install -e .
```

Or install dependencies manually:
```bash
pip install -r requirements.txt
```

After installation, the `cf` command is available globally.

## Quick Start

```bash
# Scrape a contest
cf fetch 1234

# Test your solution
cf test example_contest/A

# Watch mode — auto-retest on save
cf watch example_contest/A

# Stress test
cf stress example_contest/A
```

## Usage

### Scraping Test Cases

Supports contest IDs, contest URLs, gym URLs, problemset URLs, and group contests.

```bash
# By contest ID
cf fetch 1234

# By URL
cf fetch https://codeforces.com/contest/1234

# Gym contest
cf fetch https://codeforces.com/gym/104000

# Single problem from problemset
cf fetch https://codeforces.com/problemset/problem/1234/A

# Use Python template instead of C++
cf fetch 1234 --lang python

# Output to a specific directory
cf fetch 1234 --output ~/contests/
```

This creates a directory named after the contest ID:
```
<contest_id>/
├── A/
│   ├── solution.cpp      (from template)
│   ├── input1.txt
│   ├── output1.txt
│   ├── input2.txt
│   └── output2.txt
├── B/
│   ├── solution.cpp
│   ├── input1.txt
│   └── output1.txt
└── ...
```

See [example_contest/](example_contest/) for a real example generated from contest 1234.

### Running Tests

```bash
# Test all sample cases for problem A
cf test example_contest/A

# Test with a different language
cf test example_contest/A --lang python

# Run only specific test cases
cf test example_contest/A --tests 1 3
```

Output example:
```
──────────────────────────────────────────────────
  Testing Problem A (cpp)
──────────────────────────────────────────────────
  ℹ Compiling solution.cpp with g++...
  ✓ Compilation successful
  ℹ Running 3 test case(s)...

  ✓ Test 1: PASSED [12ms]
  ✗ Test 2: WRONG ANSWER [8ms]
  Expected                                 Got
  ──────────────────────────────────────── ────────────────────────────────────────
  5                                        4
  ✓ Test 3: PASSED [15ms]

──────────────────────────────────────────────────
  2/3 test(s) passed
  Avg: 12ms | Max: 15ms
──────────────────────────────────────────────────
```

### Watch Mode

Automatically recompiles and retests whenever you modify your solution file:

```bash
cf watch example_contest/A

# Custom poll interval (default: 1 second)
cf watch example_contest/A --interval 0.5
```

### Stress Testing

Find counter-examples by comparing your optimized solution against a brute-force one:

```bash
cf stress example_contest/A
cf stress example_contest/A --iterations 5000
cf stress example_contest/A --generator custom_gen.cpp --brute slow.cpp
```

**Setup:** Create these files in your problem directory:
- `gen.cpp` — Generates random test input (takes seed as argv[1])
- `brute.cpp` — Correct but possibly slow brute-force solution

If `gen.cpp` doesn't exist, a sample generator template is created for you.

When a mismatch is found, the failing input is saved to `stress_fail_input.txt`.

### Custom Test Cases

```bash
# Interactive — type input, then Ctrl+D (Linux) or Ctrl+Z (Windows)
cf add-test example_contest/A

# Inline
cf add-test example_contest/A --input "5\n1 2 3 4 5" --output "15"
```

### Codeforces API

```bash
# Contest info with problem list and ratings
cf info 1234

# Live standings
cf standings 1234
cf standings 1234 --count 50

# Your recent submissions
cf status your_handle
cf status your_handle --contest 1234
```

### Problem Archive

Track which problems you've solved across contests:

```bash
# Mark a problem as solved
cf solved 1234 A
cf solved 1234 B --lang python

# View your archive
cf archive
cf archive --contest 1234
```

### Configuration

Settings persist in `~/.cfhelper/config.json`:

```bash
# Show current config
cf config

# Set default language
cf config --lang python

# Set compiler
cf config --compiler g++-12

# Set time limit
cf config --time-limit 5

# Set custom template directory
cf config --template-dir ~/my-templates/
```

## Supported Languages

| Language | Template | Compiler | Solution File |
|---|---|---|---|
| C++ | `solution.cpp` | `g++` with `-std=c++17 -O2 -Wall` | `solution.cpp` |
| Python | `solution.py` | `python3` (no compilation) | `solution.py` |
| Java | `Solution.java` | `javac` | `Solution.java` |

## Project Structure

```
codeforces-helper-/
├── cf_helper/               # Core package
│   ├── __init__.py          # Version
│   ├── __main__.py          # python -m cf_helper
│   ├── cli.py               # Argument parsing & command dispatch
│   ├── scraper.py           # Web scraping with retry logic
│   ├── runner.py            # Test compilation & execution
│   ├── stress.py            # Stress testing engine
│   ├── watcher.py           # File change detection & auto-retest
│   ├── api.py               # Codeforces API integration
│   ├── archive.py           # Problem tracking/history
│   ├── config.py            # Persistent configuration
│   └── colors.py            # Terminal colors & formatting
├── templates/               # Language templates
│   ├── solution.cpp         # C++ template
│   ├── solution.py          # Python template
│   └── Solution.java        # Java template
├── example_contest/         # Sample output from contest 1234
│   ├── A/ ... F/            # Problem directories with test cases
│   └── README.md
├── pyproject.toml           # Package metadata & install config
├── requirements.txt
└── README.md
```

## Running Without Install

If you don't want to install globally, you can run directly:

```bash
python -m cf_helper fetch 1234
python -m cf_helper test example_contest/A
```

Or use the legacy scripts (still included for backwards compatibility):
```bash
python app.py 1234
python runtests.py A
```

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

