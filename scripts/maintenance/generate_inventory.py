#!/usr/bin/env python3
"""
scripts/maintenance/generate_inventory.py

Automatically generate FILE_INVENTORY.md with summaries of all project files.

Extracts:
- File purpose from docstrings/comments
- Key functions/classes
- Dependencies
- Last modified date
- Line count
- Usage examples

Usage:
    python scripts/maintenance/generate_inventory.py
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class FileInventory:
    def __init__(self, project_root="/Users/ryanranft/nba-simulator-aws"):
        self.project_root = Path(project_root)
        self.inventory_file = self.project_root / "FILE_INVENTORY.md"
        self.files_to_document = []

    def get_file_info(self, filepath: Path) -> Dict:
        """Extract metadata and content summary from a file."""
        stat = filepath.stat()
        line_count = len(filepath.read_text(encoding='utf-8', errors='ignore').splitlines())

        return {
            'path': filepath,
            'relative_path': filepath.relative_to(self.project_root),
            'name': filepath.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
            'lines': line_count,
            'type': self.get_file_type(filepath),
            'purpose': self.extract_purpose(filepath),
            'functions': self.extract_functions(filepath),
            'dependencies': self.extract_dependencies(filepath),
            'usage': self.extract_usage(filepath),
        }

    def get_file_type(self, filepath: Path) -> str:
        """Determine file type from extension."""
        suffix = filepath.suffix.lower()
        type_map = {
            '.py': 'Python script',
            '.sh': 'Bash script',
            '.sql': 'SQL script',
            '.md': 'Markdown documentation',
            '.yaml': 'YAML configuration',
            '.yml': 'YAML configuration',
            '.json': 'JSON data',
            '.txt': 'Text file',
        }
        return type_map.get(suffix, f'{suffix[1:].upper()} file' if suffix else 'File')

    def extract_purpose(self, filepath: Path) -> str:
        """Extract purpose from file header comments/docstrings."""
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()

            # Python docstrings
            if filepath.suffix == '.py':
                # Look for module-level docstring
                match = re.search(r'"""(.+?)"""', content, re.DOTALL)
                if match:
                    docstring = match.group(1).strip()
                    # Get first non-empty line after filename
                    for line in docstring.splitlines():
                        line = line.strip()
                        if line and not line.startswith('scripts/') and not line.startswith('docs/'):
                            return line

            # Shell script comments
            elif filepath.suffix == '.sh':
                for line in lines[1:10]:  # Skip shebang, check first 10 lines
                    if line.startswith('# ') and 'Purpose:' in line:
                        return line.split('Purpose:')[1].strip()
                    elif line.startswith('# ') and not line.startswith('#!/'):
                        clean_line = line.lstrip('# ').strip()
                        if clean_line and len(clean_line) > 10:
                            return clean_line

            # Markdown files
            elif filepath.suffix == '.md':
                for line in lines[1:10]:
                    if line.strip() and not line.startswith('#'):
                        return line.strip()

            # SQL files
            elif filepath.suffix == '.sql':
                for line in lines[:10]:
                    if line.strip().startswith('--') and len(line) > 5:
                        return line.lstrip('- ').strip()

        except Exception:
            pass

        return "No description available"

    def extract_functions(self, filepath: Path) -> List[str]:
        """Extract function/class names from file."""
        functions = []
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')

            if filepath.suffix == '.py':
                # Find functions
                func_matches = re.findall(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content, re.MULTILINE)
                functions.extend([f'{name}()' for name in func_matches[:5]])  # Limit to 5

                # Find classes
                class_matches = re.findall(r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
                functions.extend([f'{name} (class)' for name in class_matches[:3]])

            elif filepath.suffix == '.sh':
                # Find bash functions
                func_matches = re.findall(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)', content, re.MULTILINE)
                functions.extend([f'{name}()' for name in func_matches[:5]])

        except Exception:
            pass

        return functions[:8]  # Max 8 functions

    def extract_dependencies(self, filepath: Path) -> List[str]:
        """Extract dependencies (imports, required tools)."""
        deps = []
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')

            if filepath.suffix == '.py':
                # Find imports
                import_matches = re.findall(r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)', content, re.MULTILINE)
                from_matches = re.findall(r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)', content, re.MULTILINE)
                all_imports = list(set(import_matches + from_matches))
                # Filter to external packages
                external = [imp for imp in all_imports if imp not in ['os', 'sys', 're', 'datetime', 'pathlib', 'typing']]
                deps.extend(external[:5])

            elif filepath.suffix == '.sh':
                # Look for common tools
                if 'aws ' in content:
                    deps.append('AWS CLI')
                if 'psql' in content:
                    deps.append('PostgreSQL client')
                if 'conda' in content:
                    deps.append('Conda')
                if 'git ' in content:
                    deps.append('Git')

        except Exception:
            pass

        return deps[:5]

    def extract_usage(self, filepath: Path) -> Optional[str]:
        """Extract usage example from file."""
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')

            # Python: Look for __main__ or usage example
            if filepath.suffix == '.py':
                if 'if __name__' in content:
                    return f"python {filepath.relative_to(self.project_root)}"

            # Shell: Look for usage comment
            elif filepath.suffix == '.sh':
                match = re.search(r'Usage:\s*(.+)', content)
                if match:
                    return match.group(1).strip()
                return f"./{filepath.relative_to(self.project_root)}"

        except Exception:
            pass

        return None

    def scan_project(self):
        """Scan project for files to document."""
        patterns = [
            'scripts/**/*.py',
            'scripts/**/*.sh',
            'sql/**/*.sql',
            'docs/**/*.md',
            '*.md',
            'Makefile',
            '.env.example',
        ]

        exclude_patterns = [
            '__pycache__',
            '.git',
            'data/',
            '.idea',
            'backups',
        ]

        for pattern in patterns:
            for filepath in self.project_root.glob(pattern):
                # Check if file should be excluded
                should_exclude = any(excl in str(filepath) for excl in exclude_patterns)
                if not should_exclude and filepath.is_file():
                    self.files_to_document.append(filepath)

    def generate_markdown(self) -> str:
        """Generate markdown content for FILE_INVENTORY.md."""
        output = []
        output.append("# FILE_INVENTORY.md")
        output.append("")
        output.append(f"**Auto-generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        output.append("**Purpose:** Comprehensive inventory of all project files with automatic summaries.")
        output.append("")
        output.append("---")
        output.append("")

        # Group files by category
        categories = {
            'Root Documentation': [],
            'Scripts - AWS': [],
            'Scripts - Shell Utilities': [],
            'Scripts - ETL': [],
            'Scripts - Maintenance': [],
            'Documentation': [],
            'Architecture Decision Records': [],
            'SQL Scripts': [],
            'Configuration': [],
        }

        for filepath in sorted(self.files_to_document):
            rel_path = str(filepath.relative_to(self.project_root))

            if filepath.parent == self.project_root and filepath.suffix == '.md':
                categories['Root Documentation'].append(filepath)
            elif 'scripts/aws' in rel_path:
                categories['Scripts - AWS'].append(filepath)
            elif 'scripts/shell' in rel_path:
                categories['Scripts - Shell Utilities'].append(filepath)
            elif 'scripts/etl' in rel_path:
                categories['Scripts - ETL'].append(filepath)
            elif 'scripts/maintenance' in rel_path:
                categories['Scripts - Maintenance'].append(filepath)
            elif 'docs/adr' in rel_path and filepath.name[0].isdigit():
                categories['Architecture Decision Records'].append(filepath)
            elif 'docs/' in rel_path:
                categories['Documentation'].append(filepath)
            elif 'sql/' in rel_path:
                categories['SQL Scripts'].append(filepath)
            else:
                categories['Configuration'].append(filepath)

        # Generate sections
        for category, files in categories.items():
            if not files:
                continue

            output.append(f"## {category}")
            output.append("")

            for filepath in sorted(files):
                info = self.get_file_info(filepath)

                output.append(f"### {info['relative_path']}")
                output.append("")
                output.append(f"**Type:** {info['type']} ({info['lines']} lines)")
                output.append(f"**Last Modified:** {info['modified']}")
                output.append(f"**Purpose:** {info['purpose']}")

                if info['functions']:
                    output.append(f"**Key Functions:**")
                    for func in info['functions']:
                        output.append(f"- `{func}`")

                if info['dependencies']:
                    output.append(f"**Dependencies:** {', '.join(info['dependencies'])}")

                if info['usage']:
                    output.append(f"**Usage:** `{info['usage']}`")

                output.append("")

            output.append("---")
            output.append("")

        # Summary statistics
        output.append("## Summary Statistics")
        output.append("")
        total_lines = sum(self.get_file_info(f)['lines'] for f in self.files_to_document)
        output.append(f"**Total files documented:** {len(self.files_to_document)}")
        output.append(f"**Total lines of code/docs:** {total_lines:,}")
        output.append("")

        by_type = {}
        for filepath in self.files_to_document:
            ftype = self.get_file_type(filepath)
            by_type[ftype] = by_type.get(ftype, 0) + 1

        output.append("**Files by type:**")
        for ftype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            output.append(f"- {ftype}: {count}")

        output.append("")
        output.append("---")
        output.append("")
        output.append("**Note:** This file is auto-generated. To update, run: `make inventory`")
        output.append("")

        return '\n'.join(output)

    def run(self):
        """Main execution."""
        print("🔍 Scanning project files...")
        self.scan_project()
        print(f"   Found {len(self.files_to_document)} files to document")

        print("📝 Generating inventory...")
        content = self.generate_markdown()

        print(f"💾 Writing to {self.inventory_file}...")
        self.inventory_file.write_text(content, encoding='utf-8')

        print("✅ FILE_INVENTORY.md generated successfully!")
        print(f"   Total files: {len(self.files_to_document)}")
        print(f"   Location: {self.inventory_file}")


if __name__ == '__main__':
    inventory = FileInventory()
    inventory.run()