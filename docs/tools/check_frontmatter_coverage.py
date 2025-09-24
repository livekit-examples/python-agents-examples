#!/usr/bin/env python
"""
check_frontmatter_coverage.py
─────────────────────────────────
Scan every .py file beneath the current directory (or the paths you provide)
and report which Python agent example files have frontmatter.

USAGE
=====

    # Scan the whole repo (default behavior)
    python docs/tools/check_frontmatter_coverage.py

    # Or cherry-pick folders
    python check_frontmatter_coverage.py basics/ pipeline-stt/

    # Just print warnings for files missing frontmatter
    python check_frontmatter_coverage.py --warn-only

    # Return non-zero exit code if coverage incomplete (for CI)
    python check_frontmatter_coverage.py --fail-on-incomplete

The report looks like:

Frontmatter Coverage (15/20 files have frontmatter)
  ✔ basics/echo_bot.py
  ✔ basics/listen_and_respond.py
  ✘ basics/function_calling.py
  …

"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from collections import defaultdict


EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "build",
    "dist",
    "docs",
    "tests",
    "test",
}

# Pattern to detect frontmatter (YAML between --- markers)
# Can be at the start of file or within a docstring at the beginning
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL | re.MULTILINE)
FRONTMATTER_IN_DOCSTRING_PATTERN = re.compile(
    r'^["\'\x22\x27]{3}\s*\n---\s*\n(.*?)\n---\s*', re.DOTALL | re.MULTILINE
)

def _has_frontmatter(file_path: Path) -> bool:
    """Check if a Python file has frontmatter (either raw or in a docstring)."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # Check if the file starts with frontmatter (raw or in docstring)
        return (FRONTMATTER_PATTERN.match(content) is not None or 
                FRONTMATTER_IN_DOCSTRING_PATTERN.match(content) is not None)
    except Exception:
        return False


def _is_agent_example(file_path: Path) -> bool:
    """Check if a Python file appears to be an agent example."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # Look for common patterns in agent examples
        agent_patterns = [
            "from livekit.agents import",
            "import livekit.agents",
            "livekit.agents",
            "Agent(",
            "AgentSession(",
            "cli.run_app",
            "@WorkerHost.generate_app",
        ]
        return any(pattern in content for pattern in agent_patterns)
    except Exception:
        return False


def _scan(paths: list[Path]) -> dict[str, bool]:
    """Return a dict {file_path: has_frontmatter} for all agent example files."""
    found = {}

    for base in paths:
        for py in base.rglob("*.py"):
            # Skip excluded directories
            if any(part in EXCLUDE_DIRS for part in py.parts):
                continue
            
            # Skip files in docs/tools directory
            if "docs/tools" in str(py):
                continue
            
            # Only check files that appear to be agent examples
            if not _is_agent_example(py):
                continue
            
            # Make path relative for cleaner output
            try:
                rel_path = py.relative_to(Path.cwd())
            except ValueError:
                rel_path = py
            
            found[str(rel_path)] = _has_frontmatter(py)

    return found


def _report(found: dict[str, bool], warn_only=False):
    """Generate report of frontmatter coverage."""
    if not found:
        print("\nNo agent example files found.")
        return False, []
    
    total = len(found)
    with_frontmatter = sum(found.values())
    incomplete = with_frontmatter < total
    files_without_frontmatter = []

    if not warn_only:
        print(f"\nFrontmatter Coverage ({with_frontmatter}/{total} files have frontmatter)")
        
        # Sort files by path
        sorted_files = sorted(found.items())
        
        # Group by directory for better readability
        current_dir = None
        for file_path, has_fm in sorted_files:
            dir_path = str(Path(file_path).parent)
            if dir_path != current_dir:
                current_dir = dir_path
                print(f"\n  {dir_path}/")
            
            tick = "✔" if has_fm else "✘"
            file_name = Path(file_path).name
            print(f"    {tick} {file_name}")
            
            if not has_fm:
                files_without_frontmatter.append(file_path)
    
    elif incomplete:
        print(f"\nWARNING: {total - with_frontmatter} agent example files are missing frontmatter ({with_frontmatter}/{total} have frontmatter)")
        for file_path in sorted(found.keys()):
            if not found[file_path]:
                print(f"  Missing: {file_path}")
                files_without_frontmatter.append(file_path)
    
    return incomplete, files_without_frontmatter


def _show_frontmatter_example():
    """Display an example of frontmatter format."""
    example = """
Example frontmatter format (in a docstring at the top of the file):
────────────────────────────────────────────────────────────────────
\"\"\"
---
title: Listen and Respond
category: basics
tags: [listen, respond, openai, deepgram]
difficulty: beginner
description: Shows how to create an agent that can listen to the user and respond.
demonstrates:
  - This is the most basic agent that can listen to the user and respond.
---
\"\"\"

# Rest of your Python code...
import logging
from livekit.agents import ...
"""
    print(example)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check frontmatter coverage in agent examples")
    # By default, scan from the repository root (parent of the docs directory)
    # so this tool can be run from anywhere (including docs/tools).
    script_path = Path(__file__).resolve()
    # Go up two levels: docs/tools/check_frontmatter_coverage.py -> repo root
    default_base = script_path.parents[2] if len(script_path.parents) >= 2 else Path.cwd()
    parser.add_argument("paths", nargs="*", default=[default_base],
                        help=f"Paths to scan (default: {default_base})")
    parser.add_argument("--warn-only", action="store_true",
                        help="Only show warnings for files missing frontmatter")
    parser.add_argument("--fail-on-incomplete", action="store_true",
                        help="Return non-zero exit code if coverage is incomplete")
    parser.add_argument("--show-example", action="store_true",
                        help="Show an example of frontmatter format")

    args = parser.parse_args()

    if args.show_example:
        _show_frontmatter_example()
        sys.exit(0)

    bases = [Path(p) for p in args.paths]
    coverage = _scan(bases)
    incomplete, missing = _report(coverage, warn_only=args.warn_only)

    if incomplete and args.fail_on_incomplete:
        print(f"\nERROR: Found {len(missing)} files without frontmatter. Add frontmatter to these agent examples.")
        print("\nRun with --show-example to see the expected format.")
        sys.exit(1)
    
    if incomplete and not args.warn_only:
        print("\nTip: Run with --show-example to see the expected frontmatter format.")
