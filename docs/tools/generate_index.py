#!/usr/bin/env python3
"""
Script to extract frontmatter from all Python files in the project
and generate an index.yaml file for LLM consumption.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

def extract_frontmatter(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract YAML frontmatter from a Python file's module docstring.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary containing the frontmatter data, or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match module docstring with YAML frontmatter
        # Look for triple quotes at the start of the file (after optional whitespace)
        docstring_match = re.match(r'^\s*"""(.*?)"""', content, re.DOTALL)
        if not docstring_match:
            # Try single quotes
            docstring_match = re.match(r"^\s*'''(.*?)'''", content, re.DOTALL)
        
        if not docstring_match:
            return None
            
        docstring_content = docstring_match.group(1)
        
        # Look for YAML frontmatter between --- markers
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*$', docstring_content, re.MULTILINE | re.DOTALL)
        if not frontmatter_match:
            return None
            
        yaml_content = frontmatter_match.group(1)
        
        try:
            metadata = yaml.safe_load(yaml_content)
            return metadata
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in {file_path}: {e}")
            return None
            
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def scan_directory(root_path: Path, base_path: Path) -> List[Dict[str, Any]]:
    """
    Recursively scan directory for Python files with frontmatter.
    
    Args:
        root_path: Directory to scan
        base_path: Base path for calculating relative paths
        
    Returns:
        List of dictionaries containing file metadata
    """
    entries = []
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env', '.env', 'tests'}
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Remove directories to skip from the search
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        for filename in filenames:
            if filename.endswith('.py') and not filename.startswith('test_'):
                file_path = Path(dirpath) / filename
                metadata = extract_frontmatter(file_path)
                
                if metadata:
                    # Calculate relative path from base directory
                    relative_path = file_path.relative_to(base_path)
                    
                    # Add file path to metadata
                    entry = {
                        'file_path': str(relative_path),
                        **metadata
                    }
                    entries.append(entry)
                    print(f"✓ Found frontmatter in: {relative_path}")
    
    return entries

def generate_index(base_path: Path, output_path: Path):
    """
    Generate index.yaml file containing all frontmatter data.
    
    Args:
        base_path: Base directory to scan (demo-monolith)
        output_path: Path where index.yaml should be written
    """
    print(f"Scanning for Python files with frontmatter in: {base_path}")
    print("-" * 60)
    
    entries = scan_directory(base_path, base_path)
    
    if not entries:
        print("\nNo files with frontmatter found!")
        return
    
    # Sort entries by category and then by title
    entries.sort(key=lambda x: (x.get('category', ''), x.get('title', '')))
    
    # Create the index structure
    index_data = {
        'version': '1.0',
        'description': 'Index of all LiveKit Agent examples with metadata',
        'total_examples': len(entries),
        'examples': entries
    }
    
    # Write to YAML file
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(index_data, f, default_flow_style=False, sort_keys=False, width=120)
    
    print("\n" + "-" * 60)
    print(f"✅ Successfully generated index with {len(entries)} examples")
    print(f"📄 Index file: {output_path}")
    
    # Print summary by category
    categories = {}
    for entry in entries:
        category = entry.get('category', 'uncategorized')
        categories[category] = categories.get(category, 0) + 1
    
    print("\nExamples by category:")
    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count}")

if __name__ == "__main__":
    # Resolve paths relative to this script's new location (docs/tools)
    script_path = Path(__file__).resolve()
    # demo-monolith repo root is two levels up from this file
    base_dir = script_path.parents[2]
    # Write the index into the docs directory (one level up from this file)
    docs_dir = script_path.parents[1]
    output_file = docs_dir / "index.yaml"

    generate_index(base_dir, output_file)
