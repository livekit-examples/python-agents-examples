#!/usr/bin/env python3
"""Generate an index of example docs with YAML frontmatter."""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

def extract_frontmatter(file_path: Path) -> Optional[Dict[str, Any]]:
    """Extract YAML frontmatter from page.mdoc or Python module docstring."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading file {file_path}: {exc}")
        return None

    if file_path.suffix == ".mdoc":
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*", content, re.DOTALL)
        if not fm_match:
            return None
        fm_body = fm_match.group(1)
    elif file_path.suffix == ".py":
        docstring_match = re.match(r'^\s*("""|\'\'\')(.*?)\1', content, re.DOTALL)
        if not docstring_match:
            return None
        docstring_content = docstring_match.group(2)
        fm_match = re.search(r"^---\s*\n(.*?)\n---\s*$", docstring_content, re.MULTILINE | re.DOTALL)
        if not fm_match:
            return None
        fm_body = fm_match.group(1)
    else:
        return None

    try:
        metadata = yaml.safe_load(fm_body)
        if not isinstance(metadata, dict):
            print(f"Frontmatter in {file_path} is not a mapping, skipping.")
            return None
        return metadata
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML in {file_path}: {exc}")
        return None

def scan_page_docs(root_path: Path) -> List[Dict[str, Any]]:
    """Scan docs/examples for page.mdoc frontmatter."""
    entries: List[Dict[str, Any]] = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", ".env", "tests"}

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for filename in filenames:
            if filename != "page.mdoc":
                continue
            file_path = Path(dirpath) / filename
            metadata = extract_frontmatter(file_path)
            if metadata:
                relative_path = file_path.relative_to(root_path)
                entries.append({"file_path": str(relative_path), **metadata})
                print(f"✓ Found frontmatter in: {relative_path}")
    return entries


def scan_complex_agents(root_path: Path, base_path: Path) -> List[Dict[str, Any]]:
    """Scan complex-agents for Python files with docstring frontmatter."""
    entries: List[Dict[str, Any]] = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", ".env", "tests"}

    if not root_path.exists():
        return entries

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for filename in filenames:
            if not filename.endswith(".py") or filename.startswith("test_"):
                continue
            file_path = Path(dirpath) / filename
            metadata = extract_frontmatter(file_path)
            if metadata:
                relative_path = file_path.relative_to(base_path)
                entries.append({"file_path": str(relative_path), **metadata})
                print(f"✓ Found frontmatter in: {relative_path}")
    return entries

def generate_index(base_path: Path, output_path: Path):
    """
    Generate index.yaml file containing all frontmatter data.

    Args:
        base_path: Repository root
        output_path: Path where the index should be written
    """
    docs_examples = base_path / "docs" / "examples"
    complex_agents = base_path / "complex-agents"

    print(f"Scanning for page.mdoc files with frontmatter in: {docs_examples}")
    print(f"Scanning for complex agent Python files in: {complex_agents}")
    print("-" * 60)

    entries = []
    entries.extend(scan_page_docs(docs_examples))
    entries.extend(scan_complex_agents(complex_agents, base_path))

    if not entries:
        print("\nNo files with frontmatter found!")
        return

    entries.sort(key=lambda x: (x.get("category", ""), x.get("title", "")))

    index_data = {
        "version": "1.0",
        "description": "Index of all LiveKit Agent examples with metadata",
        "total_examples": len(entries),
        "examples": entries,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(index_data, f, default_flow_style=False, sort_keys=False, width=120)

    print("\n" + "-" * 60)
    print(f"✅ Successfully generated index with {len(entries)} examples")
    print(f"📄 Index file: {output_path}")

    categories = {}
    for entry in entries:
        category = entry.get("category", "uncategorized")
        categories[category] = categories.get(category, 0) + 1

    print("\nExamples by category:")
    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count}")

if __name__ == "__main__":
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]
    docs_dir = script_path.parents[1]
    output_file = docs_dir / "index.yaml"

    generate_index(repo_root, output_file)
