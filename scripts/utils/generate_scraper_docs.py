#!/usr/bin/env python3
"""
Documentation Generator - Auto-Generated Docs from Docstrings

Generates comprehensive documentation for NBA data scrapers:
- Extracts docstrings and type hints from all scraper modules
- Generates API reference documentation
- Creates markdown documentation with examples
- Updates README files with current functionality
- Generates configuration documentation

Based on Crawl4AI MCP server documentation patterns.

Usage:
    python scripts/utils/generate_scraper_docs.py
    python scripts/utils/generate_scraper_docs.py --output docs/api/
    python scripts/utils/generate_scraper_docs.py --format html

Version: 1.0
Created: October 13, 2025
"""

import ast
import inspect
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


@dataclass
class FunctionDoc:
    """Function documentation"""

    name: str
    docstring: str
    signature: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    version: str = "1.0"
    created: str = ""


@dataclass
class ClassDoc:
    """Class documentation"""

    name: str
    docstring: str
    methods: List[FunctionDoc] = field(default_factory=list)
    properties: List[Dict[str, Any]] = field(default_factory=list)
    version: str = "1.0"
    created: str = ""


@dataclass
class ModuleDoc:
    """Module documentation"""

    name: str
    docstring: str
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    version: str = "1.0"
    created: str = ""


class DocstringExtractor:
    """Extracts docstrings and metadata from Python files"""

    def __init__(self):
        self.logger = logging.getLogger("docstring_extractor")

    def extract_module_doc(self, file_path: Path) -> ModuleDoc:
        """Extract documentation from a Python module"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract module docstring
            module_docstring = ""
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
            ):
                module_docstring = tree.body[0].value.value

            # Extract version and created info
            version = self._extract_version(content)
            created = self._extract_created(content)

            module_doc = ModuleDoc(
                name=file_path.stem,
                docstring=module_docstring,
                version=version,
                created=created,
            )

            # Extract classes and functions
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_doc = self._extract_class_doc(node, content)
                    module_doc.classes.append(class_doc)
                elif isinstance(node, ast.FunctionDef):
                    func_doc = self._extract_function_doc(node, content)
                    module_doc.functions.append(func_doc)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    module_doc.imports.append(ast.unparse(node))

            return module_doc

        except Exception as e:
            self.logger.error(f"Error extracting docs from {file_path}: {e}")
            return ModuleDoc(
                name=file_path.stem, docstring="Error extracting documentation"
            )

    def _extract_class_doc(self, node: ast.ClassDef, content: str) -> ClassDoc:
        """Extract class documentation"""
        docstring = ""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            docstring = node.body[0].value.value

        class_doc = ClassDoc(name=node.name, docstring=docstring)

        # Extract methods
        for method_node in node.body:
            if isinstance(method_node, ast.FunctionDef):
                method_doc = self._extract_function_doc(method_node, content)
                class_doc.methods.append(method_doc)

        return class_doc

    def _extract_function_doc(self, node: ast.FunctionDef, content: str) -> FunctionDoc:
        """Extract function documentation"""
        docstring = ""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            docstring = node.body[0].value.value

        # Extract signature
        signature = ast.unparse(node)

        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "type": "Any",
                "default": None,
                "description": "",
            }

            # Try to get type annotation
            if arg.annotation:
                param_info["type"] = ast.unparse(arg.annotation)

            parameters.append(param_info)

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Extract examples from docstring
        examples = self._extract_examples(docstring)

        return FunctionDoc(
            name=node.name,
            docstring=docstring,
            signature=signature,
            parameters=parameters,
            return_type=return_type,
            examples=examples,
        )

    def _extract_examples(self, docstring: str) -> List[str]:
        """Extract code examples from docstring"""
        examples = []

        # Look for code blocks
        code_pattern = r"```(?:python)?\n(.*?)\n```"
        matches = re.findall(code_pattern, docstring, re.DOTALL)
        examples.extend(matches)

        # Look for Usage sections
        usage_pattern = r"Usage:\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)"
        usage_match = re.search(usage_pattern, docstring, re.DOTALL)
        if usage_match:
            usage_text = usage_match.group(1).strip()
            # Extract code lines
            for line in usage_text.split("\n"):
                if line.strip() and not line.strip().startswith("#"):
                    examples.append(line.strip())

        return examples

    def _extract_version(self, content: str) -> str:
        """Extract version from content"""
        version_pattern = r"Version:\s*([0-9.]+)"
        match = re.search(version_pattern, content)
        return match.group(1) if match else "1.0"

    def _extract_created(self, content: str) -> str:
        """Extract created date from content"""
        created_pattern = r"Created:\s*([^\n]+)"
        match = re.search(created_pattern, content)
        return match.group(1).strip() if match else ""


class MarkdownGenerator:
    """Generates markdown documentation"""

    def __init__(self):
        self.logger = logging.getLogger("markdown_generator")

    def generate_module_doc(self, module_doc: ModuleDoc) -> str:
        """Generate markdown documentation for a module"""
        md_content = []

        # Module header
        md_content.append(f"# {module_doc.name}")
        md_content.append("")

        if module_doc.docstring:
            md_content.append(module_doc.docstring)
            md_content.append("")

        # Version info
        md_content.append(f"**Version:** {module_doc.version}")
        md_content.append(f"**Created:** {module_doc.created}")
        md_content.append("")

        # Classes
        if module_doc.classes:
            md_content.append("## Classes")
            md_content.append("")

            for class_doc in module_doc.classes:
                md_content.extend(self._generate_class_doc(class_doc))
                md_content.append("")

        # Functions
        if module_doc.functions:
            md_content.append("## Functions")
            md_content.append("")

            for func_doc in module_doc.functions:
                md_content.extend(self._generate_function_doc(func_doc))
                md_content.append("")

        # Examples
        all_examples = []
        for class_doc in module_doc.classes:
            for method_doc in class_doc.methods:
                all_examples.extend(method_doc.examples)
        for func_doc in module_doc.functions:
            all_examples.extend(func_doc.examples)

        if all_examples:
            md_content.append("## Examples")
            md_content.append("")
            md_content.append("```python")
            md_content.extend(all_examples[:5])  # Limit to 5 examples
            md_content.append("```")
            md_content.append("")

        return "\n".join(md_content)

    def _generate_class_doc(self, class_doc: ClassDoc) -> List[str]:
        """Generate markdown for a class"""
        content = []

        content.append(f"### {class_doc.name}")
        content.append("")

        if class_doc.docstring:
            content.append(class_doc.docstring)
            content.append("")

        # Methods
        if class_doc.methods:
            content.append("**Methods:**")
            content.append("")

            for method_doc in class_doc.methods:
                content.append(
                    f"- `{method_doc.name}()` - {self._extract_summary(method_doc.docstring)}"
                )

        return content

    def _generate_function_doc(self, func_doc: FunctionDoc) -> List[str]:
        """Generate markdown for a function"""
        content = []

        content.append(f"### {func_doc.name}")
        content.append("")

        if func_doc.docstring:
            content.append(func_doc.docstring)
            content.append("")

        # Signature
        content.append("**Signature:**")
        content.append("")
        content.append(f"```python")
        content.append(func_doc.signature)
        content.append("```")
        content.append("")

        # Parameters
        if func_doc.parameters:
            content.append("**Parameters:**")
            content.append("")
            for param in func_doc.parameters:
                content.append(
                    f"- `{param['name']}` ({param['type']}) - {param['description']}"
                )
            content.append("")

        # Return type
        if func_doc.return_type:
            content.append(f"**Returns:** `{func_doc.return_type}`")
            content.append("")

        return content

    def _extract_summary(self, docstring: str) -> str:
        """Extract summary from docstring"""
        if not docstring:
            return "No description available"

        # Get first line
        first_line = docstring.split("\n")[0].strip()
        if len(first_line) > 100:
            return first_line[:100] + "..."

        return first_line


class HTMLGenerator:
    """Generates HTML documentation"""

    def __init__(self):
        self.logger = logging.getLogger("html_generator")

    def generate_module_doc(self, module_doc: ModuleDoc) -> str:
        """Generate HTML documentation for a module"""
        html_content = []

        # HTML header
        html_content.append(
            """
<!DOCTYPE html>
<html>
<head>
    <title>{} - NBA Scraper Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .method {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .signature {{ background-color: #f9f9f9; padding: 10px; font-family: monospace; }}
        .parameter {{ margin: 5px 0; }}
        code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; }}
    </style>
</head>
<body>
        """.format(
                module_doc.name
            )
        )

        # Module header
        html_content.append(f'<div class="header">')
        html_content.append(f"<h1>{module_doc.name}</h1>")
        html_content.append(f"<p><strong>Version:</strong> {module_doc.version}</p>")
        html_content.append(f"<p><strong>Created:</strong> {module_doc.created}</p>")
        html_content.append("</div>")

        if module_doc.docstring:
            html_content.append(
                f'<div class="description">{module_doc.docstring}</div>'
            )

        # Classes
        if module_doc.classes:
            html_content.append("<h2>Classes</h2>")
            for class_doc in module_doc.classes:
                html_content.extend(self._generate_class_html(class_doc))

        # Functions
        if module_doc.functions:
            html_content.append("<h2>Functions</h2>")
            for func_doc in module_doc.functions:
                html_content.extend(self._generate_function_html(func_doc))

        html_content.append("</body></html>")

        return "\n".join(html_content)

    def _generate_class_html(self, class_doc: ClassDoc) -> List[str]:
        """Generate HTML for a class"""
        content = []

        content.append(f'<div class="method">')
        content.append(f"<h3>{class_doc.name}</h3>")

        if class_doc.docstring:
            content.append(f"<p>{class_doc.docstring}</p>")

        if class_doc.methods:
            content.append("<h4>Methods:</h4>")
            content.append("<ul>")
            for method_doc in class_doc.methods:
                content.append(
                    f"<li><code>{method_doc.name}()</code> - {self._extract_summary(method_doc.docstring)}</li>"
                )
            content.append("</ul>")

        content.append("</div>")

        return content

    def _generate_function_html(self, func_doc: FunctionDoc) -> List[str]:
        """Generate HTML for a function"""
        content = []

        content.append(f'<div class="method">')
        content.append(f"<h3>{func_doc.name}</h3>")

        if func_doc.docstring:
            content.append(f"<p>{func_doc.docstring}</p>")

        content.append('<div class="signature">')
        content.append(f"<code>{func_doc.signature}</code>")
        content.append("</div>")

        if func_doc.parameters:
            content.append("<h4>Parameters:</h4>")
            content.append("<ul>")
            for param in func_doc.parameters:
                content.append(
                    f'<li class="parameter"><code>{param["name"]}</code> ({param["type"]}) - {param["description"]}</li>'
                )
            content.append("</ul>")

        if func_doc.return_type:
            content.append(
                f"<p><strong>Returns:</strong> <code>{func_doc.return_type}</code></p>"
            )

        content.append("</div>")

        return content

    def _extract_summary(self, docstring: str) -> str:
        """Extract summary from docstring"""
        if not docstring:
            return "No description available"

        first_line = docstring.split("\n")[0].strip()
        if len(first_line) > 100:
            return first_line[:100] + "..."

        return first_line


class DocumentationGenerator:
    """Main documentation generator"""

    def __init__(self, output_dir: str = "docs/api"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("documentation_generator")

        self.extractor = DocstringExtractor()
        self.markdown_generator = MarkdownGenerator()
        self.html_generator = HTMLGenerator()

    def generate_all_docs(self, source_dir: str = "scripts/etl") -> None:
        """Generate documentation for all modules"""
        source_path = Path(source_dir)

        if not source_path.exists():
            self.logger.error(f"Source directory not found: {source_dir}")
            return

        # Find all Python files
        python_files = list(source_path.rglob("*.py"))

        self.logger.info(f"Found {len(python_files)} Python files")

        # Generate documentation for each file
        for py_file in python_files:
            if py_file.name.startswith("__"):
                continue

            self.logger.info(f"Processing {py_file}")

            try:
                module_doc = self.extractor.extract_module_doc(py_file)

                # Generate markdown
                md_content = self.markdown_generator.generate_module_doc(module_doc)
                md_file = self.output_dir / f"{py_file.stem}.md"
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(md_content)

                # Generate HTML
                html_content = self.html_generator.generate_module_doc(module_doc)
                html_file = self.output_dir / f"{py_file.stem}.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html_content)

            except Exception as e:
                self.logger.error(f"Error processing {py_file}: {e}")

        # Generate index files
        self._generate_index_files(python_files)

        self.logger.info(f"Documentation generated in {self.output_dir}")

    def _generate_index_files(self, python_files: List[Path]) -> None:
        """Generate index files"""
        # Markdown index
        md_index = ["# NBA Scraper API Documentation", ""]
        md_index.append(
            f"Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        md_index.append("")
        md_index.append("## Modules")
        md_index.append("")

        for py_file in python_files:
            if py_file.name.startswith("__"):
                continue

            module_name = py_file.stem
            md_index.append(f"- [{module_name}]({module_name}.md)")

        with open(self.output_dir / "README.md", "w", encoding="utf-8") as f:
            f.write("\n".join(md_index))

        # HTML index
        html_index = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NBA Scraper API Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .module-list {{ list-style-type: none; padding: 0; }}
        .module-item {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .module-item a {{ text-decoration: none; color: #333; }}
        .module-item a:hover {{ color: #007bff; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>NBA Scraper API Documentation</h1>
        <p>Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>

    <h2>Modules</h2>
    <ul class="module-list">
"""

        for py_file in python_files:
            if py_file.name.startswith("__"):
                continue

            module_name = py_file.stem
            html_index += f'        <li class="module-item"><a href="{module_name}.html">{module_name}</a></li>\n'

        html_index += """
    </ul>
</body>
</html>
"""

        with open(self.output_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html_index)


# Example usage
if __name__ == "__main__":
    import argparse
    import logging

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Parse arguments
    parser = argparse.ArgumentParser(description="Generate NBA Scraper Documentation")
    parser.add_argument("--output", "-o", default="docs/api", help="Output directory")
    parser.add_argument(
        "--source", "-s", default="scripts/etl", help="Source directory"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "html", "both"],
        default="both",
        help="Output format",
    )

    args = parser.parse_args()

    # Generate documentation
    generator = DocumentationGenerator(args.output)
    generator.generate_all_docs(args.source)

    print(f"Documentation generated successfully in {args.output}")


