#!/usr/bin/env python3
"""
PRMS CLI - Path Reference Management System
Automated validation and correction of path references across the codebase.

Version: 1.0.0
Created: 2025-10-26

Usage:
    python scripts/maintenance/prms_cli.py scan         # Discover all path references
    python scripts/maintenance/prms_cli.py classify     # Categorize references
    python scripts/maintenance/prms_cli.py validate     # Verify paths exist
    python scripts/maintenance/prms_cli.py fix          # Auto-correct safe references
    python scripts/maintenance/prms_cli.py report       # Generate audit report
    python scripts/maintenance/prms_cli.py check FILE   # Check specific file
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


class PathReference:
    """Represents a single path reference found in a file."""

    def __init__(
        self,
        file_path: str,
        line_number: int,
        line_content: str,
        pattern: str,
        match_text: str,
        category: str = "UNKNOWN",
        confidence: float = 0.5,
        suggested_fix: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.line_content = line_content
        self.pattern = pattern
        self.match_text = match_text
        self.category = category
        self.confidence = confidence
        self.suggested_fix = suggested_fix
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file": self.file_path,
            "line": self.line_number,
            "content": self.line_content.strip(),
            "pattern": self.pattern,
            "match": self.match_text,
            "category": self.category,
            "confidence": self.confidence,
            "suggested_fix": self.suggested_fix,
            "reason": self.reason,
        }


class PRMSConfig:
    """Manages PRMS configuration."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config from {self.config_path}: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """Setup logging based on config."""
        log_config = self.config.get("logging", {})
        log_file = PROJECT_ROOT / log_config.get("file", "inventory/outputs/prms/prms.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, log_config.get("level", "INFO")),
            format=log_config.get("format", "%(asctime)s - %(levelname)s - %(message)s"),
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger("PRMS")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            value = value.get(k, {})
            if not value:
                return default
        return value if value != {} else default


class PathReferenceScanner:
    """Scans codebase for path references."""

    def __init__(self, config: PRMSConfig):
        self.config = config
        self.logger = logging.getLogger("PRMS.Scanner")
        self.references: List[PathReference] = []

    def scan(self) -> List[PathReference]:
        """Scan all configured directories for path references."""
        self.logger.info("Starting path reference scan...")

        scan_dirs = self.config.get("scan.directories", [])
        exclude_dirs = set(self.config.get("scan.exclude_dirs", []))
        extensions = set(self.config.get("scan.extensions", []))
        max_size = self.config.get("scan.max_file_size", 5242880)
        parallel = self.config.get("scan.parallel", True)
        max_workers = self.config.get("scan.max_workers", 4)

        # Collect all files to scan
        files_to_scan = []
        for scan_dir in scan_dirs:
            dir_path = PROJECT_ROOT / scan_dir
            if not dir_path.exists():
                self.logger.warning(f"Directory not found: {dir_path}")
                continue

            for file_path in dir_path.rglob("*"):
                # Skip if in excluded directory
                if any(excl in str(file_path) for excl in exclude_dirs):
                    continue

                # Skip if not a file
                if not file_path.is_file():
                    continue

                # Skip if wrong extension
                if file_path.suffix not in extensions:
                    continue

                # Skip if too large
                try:
                    if file_path.stat().st_size > max_size:
                        self.logger.debug(f"Skipping large file: {file_path}")
                        continue
                except:
                    continue

                files_to_scan.append(file_path)

        self.logger.info(f"Scanning {len(files_to_scan)} files...")

        # Scan files (parallel or sequential)
        if parallel and len(files_to_scan) > 10:
            self._scan_parallel(files_to_scan, max_workers)
        else:
            self._scan_sequential(files_to_scan)

        self.logger.info(f"Scan complete. Found {len(self.references)} references.")
        return self.references

    def _scan_sequential(self, files: List[Path]):
        """Scan files sequentially."""
        for i, file_path in enumerate(files, 1):
            if i % 100 == 0:
                self.logger.info(f"Progress: {i}/{len(files)} files scanned...")
            self._scan_file(file_path)

    def _scan_parallel(self, files: List[Path], max_workers: int):
        """Scan files in parallel."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._scan_file, f): f for f in files}
            for i, future in enumerate(as_completed(futures), 1):
                if i % 100 == 0:
                    self.logger.info(f"Progress: {i}/{len(files)} files scanned...")
                try:
                    future.result()
                except Exception as e:
                    file_path = futures[future]
                    self.logger.error(f"Error scanning {file_path}: {e}")

    def _scan_file(self, file_path: Path):
        """Scan a single file for path references."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    self._scan_line(file_path, line_num, line)
        except Exception as e:
            self.logger.debug(f"Could not read {file_path}: {e}")

    def _scan_line(self, file_path: Path, line_num: int, line: str):
        """Scan a single line for path references."""
        # Get phase number patterns
        phase_patterns = self._build_phase_patterns()

        for pattern_name, regex in phase_patterns.items():
            for match in regex.finditer(line):
                ref = PathReference(
                    file_path=str(file_path.relative_to(PROJECT_ROOT)),
                    line_number=line_num,
                    line_content=line,
                    pattern=pattern_name,
                    match_text=match.group(0),
                )
                self.references.append(ref)

    def _build_phase_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for detecting phase references."""
        patterns = {}

        # Phase directory patterns
        patterns["phase_dir"] = re.compile(r"(docs|tests|validators)/phases/phase_([6-9])/")

        # Phase prose references
        patterns["phase_prose"] = re.compile(r"\b(P|p)hase\s+([6-9])\b")
        patterns["phase_subphase"] = re.compile(r"\b(P|p)hase\s+([6-9])\.([0-9]+)\b")

        # Phase code references
        patterns["phase_code"] = re.compile(r"\bphase_([6-9])\b")
        patterns["phase_code_caps"] = re.compile(r"\bPHASE_([6-9])\b")

        # File name patterns
        patterns["phase_filename"] = re.compile(r"phase_([6-9])_[a-z_]+")

        # Specific known problematic patterns
        patterns["phase_2_scripts"] = re.compile(r"\bphase_2_scripts\b")
        patterns["phase_2_agent"] = re.compile(r"\bphase_9_[a-z_]+_agent\b")

        return patterns


class PathReferenceClassifier:
    """Classifies path references as update/skip/manual."""

    def __init__(self, config: PRMSConfig):
        self.config = config
        self.logger = logging.getLogger("PRMS.Classifier")

    def classify(self, references: List[PathReference]) -> List[PathReference]:
        """Classify all references."""
        self.logger.info(f"Classifying {len(references)} references...")

        for ref in references:
            self._classify_reference(ref)

        # Log summary
        summary = self._get_classification_summary(references)
        self.logger.info(f"Classification summary: {summary}")

        return references

    def _classify_reference(self, ref: PathReference):
        """Classify a single reference."""
        file_path = Path(ref.file_path)

        # Check if in always_skip paths
        if self._is_always_skip(file_path):
            ref.category = "SKIP"
            ref.reason = "File in always_skip list (archive/migration/ADR)"
            ref.confidence = 1.0
            return

        # Check if in manual_review
        if self._requires_manual_review(ref):
            ref.category = "MANUAL_REVIEW"
            ref.reason = "Requires manual review (workflow name or context-dependent)"
            ref.confidence = 0.3
            return

        # Check if in always_update paths
        if self._is_always_update(file_path):
            ref.category = "MUST_UPDATE"
            ref.suggested_fix = self._suggest_fix(ref)
            ref.reason = "File in always_update list (active code/docs)"
            ref.confidence = 0.9 if ref.suggested_fix else 0.6
            return

        # Default to manual review if uncertain
        ref.category = "MANUAL_REVIEW"
        ref.reason = "Uncertain classification"
        ref.confidence = 0.4

    def _is_always_skip(self, file_path: Path) -> bool:
        """Check if file should always be skipped."""
        skip_paths = self.config.get("classification.always_skip.paths", [])
        skip_files = self.config.get("classification.always_skip.files", [])

        # Check paths
        file_str = str(file_path)
        for pattern in skip_paths:
            # Remove wildcards to get base path
            pattern_clean = pattern.replace("/**", "").replace("**", "").rstrip("/")
            # Check if file starts with or contains the base path
            if file_str.startswith(pattern_clean) or pattern_clean in file_str:
                return True

        # Check specific files
        for skip_file in skip_files:
            if file_path.name == Path(skip_file).name:
                return True

        return False

    def _is_always_update(self, file_path: Path) -> bool:
        """Check if file should always be updated."""
        update_paths = self.config.get("classification.always_update.paths", [])
        exclude_paths = self.config.get("classification.always_update.exclude", [])

        file_str = str(file_path)

        # Check excludes first
        for pattern in exclude_paths:
            pattern_clean = pattern.replace("**", "*").rstrip("/")
            if pattern_clean in file_str:
                return False

        # Check update paths
        for pattern in update_paths:
            pattern_clean = pattern.replace("**", "*").rstrip("/")
            if pattern_clean in file_str or file_path.match(pattern):
                return True

        return False

    def _requires_manual_review(self, ref: PathReference) -> bool:
        """Check if reference requires manual review."""
        manual_patterns = self.config.get("classification.manual_review.patterns", [])
        manual_files = self.config.get("classification.manual_review.files", [])

        # Check patterns
        for pattern in manual_patterns:
            if pattern in ref.match_text:
                return True

        # Check files
        file_path = Path(ref.file_path)
        for manual_file in manual_files:
            if file_path.match(manual_file):
                return True

        return False

    def _suggest_fix(self, ref: PathReference) -> Optional[str]:
        """Suggest a fix for the reference."""
        mappings = self.config.get("mappings", {})

        # Extract phase number from match
        phase_num = self._extract_phase_number(ref.match_text)
        if not phase_num:
            return None

        # Get mapping for this phase
        phase_key = f"phase_{phase_num}"
        if phase_key not in mappings:
            return None

        mapping = mappings[phase_key]
        new_phase = mapping.get("new_phase")

        # Handle different reference types
        if "phase_dir" in ref.pattern:
            # Directory reference: phase_0/ → phase_0/
            return ref.match_text.replace(f"phase_{phase_num}/", f"phase_{new_phase}/")

        elif "phase_prose" in ref.pattern:
            # Prose reference: "Phase 0.0.0019/0.0.0020/0.0.0021" → "Phase 0.0019/0.0020/0.0021"
            sub_phases = mapping.get("sub_phase_map", {})
            if sub_phases:
                sub_phase_list = "/".join(f"{new_phase}.{sp}" for sp in sub_phases.values())
                return f"Phase {sub_phase_list}"
            else:
                return f"Phase {new_phase}"

        elif "phase_code" in ref.pattern or "phase_filename" in ref.pattern:
            # Code reference: phase_0 → phase_0
            return ref.match_text.replace(f"phase_{phase_num}", f"phase_{new_phase}")

        elif "phase_2_scripts" in ref.pattern:
            # Special case
            return mapping.get("special_cases", {}).get("phase_2_scripts", "phase_2_scripts")

        elif "phase_2_agent" in ref.pattern:
            # Special case for agents
            special_cases = mapping.get("special_cases", {})
            for old_name, new_name in special_cases.items():
                if old_name in ref.match_text:
                    return ref.match_text.replace(old_name, new_name)

        return None

    def _extract_phase_number(self, text: str) -> Optional[str]:
        """Extract phase number from text."""
        match = re.search(r"phase[_\s]?([6-9])", text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _get_classification_summary(self, references: List[PathReference]) -> Dict[str, int]:
        """Get summary of classifications."""
        summary = defaultdict(int)
        for ref in references:
            summary[ref.category] += 1
        return dict(summary)


class PathReferenceValidator:
    """Validates that path references point to existing files/directories."""

    def __init__(self, config: PRMSConfig):
        self.config = config
        self.logger = logging.getLogger("PRMS.Validator")

    def validate(self, references: List[PathReference]) -> Tuple[int, int]:
        """Validate all references. Returns (valid_count, invalid_count)."""
        self.logger.info(f"Validating {len(references)} references...")

        valid = 0
        invalid = 0

        for ref in references:
            if self._validate_reference(ref):
                valid += 1
            else:
                invalid += 1

        self.logger.info(f"Validation complete: {valid} valid, {invalid} invalid")
        return valid, invalid

    def _validate_reference(self, ref: PathReference) -> bool:
        """Validate a single reference."""
        # For now, just check if the file itself exists
        file_path = PROJECT_ROOT / ref.file_path
        return file_path.exists()


class PathReferenceFixer:
    """Fixes path references automatically."""

    def __init__(self, config: PRMSConfig, dry_run: bool = True):
        self.config = config
        self.dry_run = dry_run
        self.logger = logging.getLogger("PRMS.Fixer")
        self.fixes_applied = []

    def fix(self, references: List[PathReference]) -> int:
        """Fix all MUST_UPDATE references. Returns count of fixes."""
        self.logger.info(f"Fixing references (dry_run={self.dry_run})...")

        # Filter to only MUST_UPDATE with high confidence
        auto_fix_threshold = self.config.get("confidence.auto_fix_threshold", 0.8)
        fixable_refs = [
            ref
            for ref in references
            if ref.category == "MUST_UPDATE"
            and ref.confidence >= auto_fix_threshold
            and ref.suggested_fix
        ]

        self.logger.info(f"Found {len(fixable_refs)} fixable references")

        if not fixable_refs:
            return 0

        # Group by file
        refs_by_file = defaultdict(list)
        for ref in fixable_refs:
            refs_by_file[ref.file_path].append(ref)

        # Fix each file
        fixes_count = 0
        for file_path, refs in refs_by_file.items():
            if self._fix_file(file_path, refs):
                fixes_count += len(refs)

        self.logger.info(f"Applied {fixes_count} fixes across {len(refs_by_file)} files")
        return fixes_count

    def _fix_file(self, file_path: str, refs: List[PathReference]) -> bool:
        """Fix all references in a single file."""
        full_path = PROJECT_ROOT / file_path

        try:
            # Read file
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Create backup if configured
            if self.config.get("fix.create_backup", True) and not self.dry_run:
                backup_path = str(full_path) + self.config.get("fix.backup_suffix", ".prms_backup")
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

            # Apply fixes (reverse order to preserve line numbers)
            for ref in sorted(refs, key=lambda r: r.line_number, reverse=True):
                line_idx = ref.line_number - 1
                if 0 <= line_idx < len(lines):
                    old_line = lines[line_idx]
                    new_line = old_line.replace(ref.match_text, ref.suggested_fix)
                    lines[line_idx] = new_line

                    self.fixes_applied.append(
                        {
                            "file": file_path,
                            "line": ref.line_number,
                            "old": ref.match_text,
                            "new": ref.suggested_fix,
                        }
                    )

                    if self.dry_run:
                        self.logger.info(
                            f"[DRY RUN] Would fix {file_path}:{ref.line_number}: "
                            f"{ref.match_text} → {ref.suggested_fix}"
                        )

            # Write file if not dry run
            if not self.dry_run:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                self.logger.info(f"Fixed {len(refs)} references in {file_path}")

            return True

        except Exception as e:
            self.logger.error(f"Error fixing {file_path}: {e}")
            return False


class PathReferenceReporter:
    """Generates reports about path references."""

    def __init__(self, config: PRMSConfig):
        self.config = config
        self.logger = logging.getLogger("PRMS.Reporter")

    def generate_reports(self, references: List[PathReference]):
        """Generate all configured report formats."""
        output_dir = PROJECT_ROOT / self.config.get("report.output_dir", "inventory/outputs/prms/")
        output_dir.mkdir(parents=True, exist_ok=True)

        formats = self.config.get("report.formats", ["markdown", "json"])

        for fmt in formats:
            if fmt == "markdown":
                self._generate_markdown_report(references, output_dir)
            elif fmt == "json":
                self._generate_json_report(references, output_dir)
            elif fmt == "html":
                self._generate_html_report(references, output_dir)

    def _generate_markdown_report(self, references: List[PathReference], output_dir: Path):
        """Generate Markdown report."""
        report_path = output_dir / "prms_audit_report.md"
        self.logger.info(f"Generating Markdown report: {report_path}")

        # Group references
        by_category = defaultdict(list)
        by_file_type = defaultdict(list)
        for ref in references:
            by_category[ref.category].append(ref)
            ext = Path(ref.file_path).suffix
            by_file_type[ext].append(ref)

        # Generate report
        lines = []
        lines.append("# PRMS Path Reference Audit Report")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total References:** {len(references)}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        for category, refs in sorted(by_category.items()):
            pct = (len(refs) / len(references) * 100) if references else 0
            lines.append(f"- **{category}:** {len(refs)} ({pct:.1f}%)")
        lines.append("")

        # Must Update section
        must_update = by_category.get("MUST_UPDATE", [])
        if must_update:
            lines.append("## Must Update")
            lines.append("")
            lines.append(f"**Total:** {len(must_update)} references")
            lines.append("")

            # Group by file type
            by_ext = defaultdict(list)
            for ref in must_update:
                ext = Path(ref.file_path).suffix
                by_ext[ext].append(ref)

            for ext, refs in sorted(by_ext.items()):
                lines.append(f"### {ext} files ({len(refs)} references)")
                lines.append("")
                lines.append("| File | Line | Old Reference | Suggested Fix |")
                lines.append("|------|------|---------------|---------------|")
                for ref in refs[:20]:  # Limit to 20 per section
                    lines.append(
                        f"| `{ref.file_path}` | {ref.line_number} | `{ref.match_text}` | `{ref.suggested_fix or 'N/A'}` |"
                    )
                if len(refs) > 20:
                    lines.append(f"| ... | ... | ... | ... |")
                    lines.append(f"| *(+{len(refs) - 20} more)* | | | |")
                lines.append("")

        # Manual Review section
        manual_review = by_category.get("MANUAL_REVIEW", [])
        if manual_review:
            lines.append("## Manual Review Required")
            lines.append("")
            lines.append(f"**Total:** {len(manual_review)} references")
            lines.append("")
            lines.append("| File | Line | Pattern | Reason |")
            lines.append("|------|------|---------|--------|")
            for ref in manual_review:
                lines.append(
                    f"| `{ref.file_path}` | {ref.line_number} | `{ref.match_text}` | {ref.reason or 'N/A'} |"
                )
            lines.append("")

        # Skip section
        skipped = by_category.get("SKIP", [])
        if skipped:
            lines.append("## Safely Skipped")
            lines.append("")
            lines.append(f"**Total:** {len(skipped)} references")
            lines.append("")
            files_skipped = set(ref.file_path for ref in skipped)
            for file in sorted(files_skipped):
                count = sum(1 for ref in skipped if ref.file_path == file)
                reason = next((ref.reason for ref in skipped if ref.file_path == file), "N/A")
                lines.append(f"- `{file}` ({count} refs) - {reason}")
            lines.append("")

        # Write report
        with open(report_path, "w") as f:
            f.write("\n".join(lines))

        self.logger.info(f"Markdown report written to {report_path}")

    def _generate_json_report(self, references: List[PathReference], output_dir: Path):
        """Generate JSON report."""
        report_path = output_dir / "prms_audit_report.json"
        self.logger.info(f"Generating JSON report: {report_path}")

        report_data = {
            "generated": datetime.now().isoformat(),
            "total_references": len(references),
            "references": [ref.to_dict() for ref in references],
            "summary": self._get_summary(references),
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        self.logger.info(f"JSON report written to {report_path}")

    def _generate_html_report(self, references: List[PathReference], output_dir: Path):
        """Generate HTML report (simplified)."""
        report_path = output_dir / "prms_audit_report.html"
        self.logger.info(f"Generating HTML report: {report_path}")

        # Simple HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PRMS Audit Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .must-update {{ background-color: #ffcccc; }}
                .manual-review {{ background-color: #ffffcc; }}
                .skip {{ background-color: #ccffcc; }}
            </style>
        </head>
        <body>
            <h1>PRMS Path Reference Audit Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total References:</strong> {len(references)}</p>

            <h2>Summary</h2>
            <ul>
                <li><strong>MUST_UPDATE:</strong> {sum(1 for r in references if r.category == 'MUST_UPDATE')}</li>
                <li><strong>MANUAL_REVIEW:</strong> {sum(1 for r in references if r.category == 'MANUAL_REVIEW')}</li>
                <li><strong>SKIP:</strong> {sum(1 for r in references if r.category == 'SKIP')}</li>
            </ul>

            <h2>All References</h2>
            <table>
                <tr>
                    <th>File</th>
                    <th>Line</th>
                    <th>Match</th>
                    <th>Category</th>
                    <th>Suggested Fix</th>
                </tr>
        """

        for ref in references[:100]:  # Limit to 100 for HTML
            category_class = ref.category.lower().replace("_", "-")
            html += f"""
                <tr class="{category_class}">
                    <td>{ref.file_path}</td>
                    <td>{ref.line_number}</td>
                    <td><code>{ref.match_text}</code></td>
                    <td>{ref.category}</td>
                    <td><code>{ref.suggested_fix or 'N/A'}</code></td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        with open(report_path, "w") as f:
            f.write(html)

        self.logger.info(f"HTML report written to {report_path}")

    def _get_summary(self, references: List[PathReference]) -> Dict[str, Any]:
        """Get summary statistics."""
        by_category = defaultdict(int)
        by_file_type = defaultdict(int)

        for ref in references:
            by_category[ref.category] += 1
            ext = Path(ref.file_path).suffix
            by_file_type[ext] += 1

        return {
            "by_category": dict(by_category),
            "by_file_type": dict(by_file_type),
        }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PRMS - Path Reference Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for path references")
    scan_parser.add_argument("--classify", action="store_true", help="Also classify references")
    scan_parser.add_argument("--report", action="store_true", help="Also generate report")

    # Classify command
    classify_parser = subparsers.add_parser("classify", help="Classify scanned references")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate path references")

    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Fix path references")
    fix_parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    fix_parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate audit report")
    report_parser.add_argument("--format", choices=["markdown", "json", "html", "all"], default="all", help="Report format")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check specific file")
    check_parser.add_argument("file", help="File to check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load configuration
    config_path = PROJECT_ROOT / "config" / "prms_config.yaml"
    config = PRMSConfig(config_path)

    # Execute command
    if args.command == "scan":
        scanner = PathReferenceScanner(config)
        references = scanner.scan()

        # Save to JSON
        output_dir = PROJECT_ROOT / config.get("report.output_dir", "inventory/outputs/prms/")
        output_dir.mkdir(parents=True, exist_ok=True)
        refs_file = output_dir / "path_references.json"

        with open(refs_file, "w") as f:
            json.dump(
                {
                    "scan_date": datetime.now().isoformat(),
                    "total_references": len(references),
                    "references": [ref.to_dict() for ref in references],
                },
                f,
                indent=2,
            )
        print(f"✅ Scan complete. Found {len(references)} references.")
        print(f"📁 Saved to {refs_file}")

        if args.classify:
            classifier = PathReferenceClassifier(config)
            references = classifier.classify(references)

            # Re-save with classifications
            with open(refs_file, "w") as f:
                json.dump(
                    {
                        "scan_date": datetime.now().isoformat(),
                        "total_references": len(references),
                        "references": [ref.to_dict() for ref in references],
                    },
                    f,
                    indent=2,
                )
            print(f"✅ Classification complete.")

        if args.report:
            reporter = PathReferenceReporter(config)
            reporter.generate_reports(references)
            print(f"✅ Reports generated.")

    elif args.command == "classify":
        # Load previous scan
        refs_file = PROJECT_ROOT / config.get("report.output_dir", "inventory/outputs/prms/") / "path_references.json"
        if not refs_file.exists():
            print(f"❌ No scan data found. Run 'prms_cli.py scan' first.")
            sys.exit(1)

        with open(refs_file, "r") as f:
            data = json.load(f)

        # Convert dict keys to match PathReference constructor
        references = []
        for ref_data in data["references"]:
            ref_dict = ref_data.copy()
            if "file" in ref_dict:
                ref_dict["file_path"] = ref_dict.pop("file")
            if "line" in ref_dict:
                ref_dict["line_number"] = ref_dict.pop("line")
            if "content" in ref_dict:
                ref_dict["line_content"] = ref_dict.pop("content")
            if "match" in ref_dict:
                ref_dict["match_text"] = ref_dict.pop("match")
            references.append(PathReference(**ref_dict))

        classifier = PathReferenceClassifier(config)
        references = classifier.classify(references)

        # Save
        with open(refs_file, "w") as f:
            json.dump(
                {
                    "scan_date": data["scan_date"],
                    "total_references": len(references),
                    "references": [ref.to_dict() for ref in references],
                },
                f,
                indent=2,
            )
        print(f"✅ Classification complete.")

    elif args.command == "validate":
        # Load scan
        refs_file = PROJECT_ROOT / config.get("report.output_dir", "inventory/outputs/prms/") / "path_references.json"
        if not refs_file.exists():
            print(f"❌ No scan data found. Run 'prms_cli.py scan' first.")
            sys.exit(1)

        with open(refs_file, "r") as f:
            data = json.load(f)

        # Convert dict keys to match PathReference constructor
        references = []
        for ref_data in data["references"]:
            ref_dict = ref_data.copy()
            if "file" in ref_dict:
                ref_dict["file_path"] = ref_dict.pop("file")
            if "line" in ref_dict:
                ref_dict["line_number"] = ref_dict.pop("line")
            if "content" in ref_dict:
                ref_dict["line_content"] = ref_dict.pop("content")
            if "match" in ref_dict:
                ref_dict["match_text"] = ref_dict.pop("match")
            references.append(PathReference(**ref_dict))

        validator = PathReferenceValidator(config)
        valid, invalid = validator.validate(references)
        print(f"✅ Validation complete: {valid} valid, {invalid} invalid")

    elif args.command == "fix":
        # Load scan
        refs_file = PROJECT_ROOT / config.get("report.output_dir", "inventory/outputs/prms/") / "path_references.json"
        if not refs_file.exists():
            print(f"❌ No scan data found. Run 'prms_cli.py scan --classify' first.")
            sys.exit(1)

        with open(refs_file, "r") as f:
            data = json.load(f)

        # Convert dict keys to match PathReference constructor
        references = []
        for ref_data in data["references"]:
            ref_dict = ref_data.copy()
            if "file" in ref_dict:
                ref_dict["file_path"] = ref_dict.pop("file")
            if "line" in ref_dict:
                ref_dict["line_number"] = ref_dict.pop("line")
            if "content" in ref_dict:
                ref_dict["line_content"] = ref_dict.pop("content")
            if "match" in ref_dict:
                ref_dict["match_text"] = ref_dict.pop("match")
            references.append(PathReference(**ref_dict))

        # Count fixable
        auto_fix_threshold = config.get("confidence.auto_fix_threshold", 0.8)
        fixable = sum(
            1
            for r in references
            if r.category == "MUST_UPDATE" and r.confidence >= auto_fix_threshold and r.suggested_fix
        )

        print(f"Found {fixable} references that can be auto-fixed.")

        if not args.yes and not args.dry_run:
            response = input("Continue with fixes? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("Aborted.")
                sys.exit(0)

        fixer = PathReferenceFixer(config, dry_run=args.dry_run)
        fixes_count = fixer.fix(references)

        if args.dry_run:
            print(f"✅ [DRY RUN] Would fix {fixes_count} references.")
        else:
            print(f"✅ Fixed {fixes_count} references.")

    elif args.command == "report":
        # Load scan
        refs_file = PROJECT_ROOT / config.get("report.output_dir", "inventory/outputs/prms/") / "path_references.json"
        if not refs_file.exists():
            print(f"❌ No scan data found. Run 'prms_cli.py scan --classify' first.")
            sys.exit(1)

        with open(refs_file, "r") as f:
            data = json.load(f)

        # Convert dict keys to match PathReference constructor
        references = []
        for ref_data in data["references"]:
            ref_dict = ref_data.copy()
            if "file" in ref_dict:
                ref_dict["file_path"] = ref_dict.pop("file")
            if "line" in ref_dict:
                ref_dict["line_number"] = ref_dict.pop("line")
            if "content" in ref_dict:
                ref_dict["line_content"] = ref_dict.pop("content")
            if "match" in ref_dict:
                ref_dict["match_text"] = ref_dict.pop("match")
            references.append(PathReference(**ref_dict))

        reporter = PathReferenceReporter(config)
        reporter.generate_reports(references)
        print(f"✅ Reports generated in {config.get('report.output_dir')}")

    elif args.command == "check":
        # Check specific file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        scanner = PathReferenceScanner(config)
        scanner._scan_file(file_path)

        if scanner.references:
            print(f"Found {len(scanner.references)} references in {file_path}:")
            for ref in scanner.references:
                print(f"  Line {ref.line_number}: {ref.match_text} ({ref.pattern})")
        else:
            print(f"No phase references found in {file_path}")


if __name__ == "__main__":
    main()
