"""
DIMS Output Module
Generates inventory documentation in multiple formats (Markdown, JSON, HTML, Jupyter).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Base class for output generators."""

    def generate(self, metrics: Dict[str, Any], output_path: Path) -> bool:
        """Generate output file from metrics."""
        raise NotImplementedError


class MarkdownGenerator(OutputGenerator):
    """Generate Markdown documentation from metrics."""

    def __init__(self, template: str = 'master_inventory'):
        """
        Initialize Markdown generator.

        Args:
            template: Template type ('master_inventory' or 'collection_inventory')
        """
        self.template = template

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata section."""
        lines = []
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Version:** {metadata.get('version', 'unknown')}")
        lines.append(f"- **Last Updated:** {metadata.get('last_updated', 'unknown')}")
        lines.append(f"- **Last Verified:** {metadata.get('last_verified', 'unknown')}")
        lines.append(f"- **Verified By:** {metadata.get('verified_by', 'unknown')}")
        lines.append(f"- **System:** {metadata.get('system', 'DIMS')}")

        notes = metadata.get('notes')
        if notes:
            lines.append(f"- **Notes:** {notes}")

        lines.append("")
        return "\n".join(lines)

    def _format_s3_storage(self, s3_data: Dict[str, Any]) -> str:
        """Format S3 storage section."""
        lines = []
        lines.append("## S3 Storage")
        lines.append("")

        total_objects = s3_data.get('total_objects', {})
        total_size = s3_data.get('total_size_gb', {})
        hoopr_files = s3_data.get('hoopr_files', {})

        lines.append("### Summary")
        lines.append("")
        lines.append(f"- **Total Objects:** {total_objects.get('value', 'N/A'):,}")
        lines.append(f"- **Total Size:** {total_size.get('value', 'N/A')} GB")
        lines.append(f"- **hoopR Parquet Files:** {hoopr_files.get('value', 'N/A')}")
        lines.append("")

        lines.append("### Verification")
        lines.append("")
        lines.append("| Metric | Value | Last Verified | Method |")
        lines.append("|--------|-------|---------------|--------|")

        for metric_name, metric_data in s3_data.items():
            if isinstance(metric_data, dict) and 'value' in metric_data:
                value = metric_data.get('value', 'N/A')
                last_verified = metric_data.get('last_verified', 'N/A')
                method = metric_data.get('verification_method', 'N/A')

                # Format value
                if metric_name == 'total_objects':
                    value_str = f"{value:,}"
                elif metric_name == 'total_size_gb':
                    value_str = f"{value} GB"
                else:
                    value_str = str(value)

                lines.append(f"| {metric_name.replace('_', ' ').title()} | {value_str} | {last_verified} | {method} |")

        lines.append("")
        return "\n".join(lines)

    def _format_prediction_system(self, prediction_data: Dict[str, Any]) -> str:
        """Format prediction system section."""
        lines = []
        lines.append("## Prediction System")
        lines.append("")

        total_lines = prediction_data.get('total_lines', {})
        lines.append(f"**Total Lines of Code:** {total_lines.get('value', 'N/A'):,}")
        lines.append("")

        scripts = prediction_data.get('scripts', {})
        if scripts:
            lines.append("### Scripts")
            lines.append("")
            lines.append("| Script | Lines | Path |")
            lines.append("|--------|-------|------|")

            for script_name, script_data in scripts.items():
                if isinstance(script_data, dict):
                    script_lines = script_data.get('lines', 'N/A')
                    script_path = script_data.get('path', 'N/A')
                    display_name = script_name.replace('_', ' ').title()
                    lines.append(f"| {display_name} | {script_lines} | `{script_path}` |")

            lines.append("")

        return "\n".join(lines)

    def _format_plus_minus_system(self, plus_minus_data: Dict[str, Any]) -> str:
        """Format Plus/Minus system section."""
        lines = []
        lines.append("## Plus/Minus System")
        lines.append("")

        total_lines = plus_minus_data.get('total_lines', {})
        if isinstance(total_lines, dict):
            value = total_lines.get('value', 'N/A')
            components = total_lines.get('components', {})

            lines.append(f"**Total Lines:** {value:,}")
            lines.append("")

            if components:
                lines.append("### Components")
                lines.append("")
                lines.append(f"- **Python:** {components.get('python', 'N/A'):,} lines")
                lines.append(f"- **SQL:** {components.get('sql', 'N/A'):,} lines")
                lines.append(f"- **Documentation:** {components.get('docs', 'N/A'):,} lines")
                lines.append("")

        # Python files
        python_files = plus_minus_data.get('python_files', {})
        if python_files:
            lines.append("### Python Scripts")
            lines.append("")
            scripts = python_files.get('scripts', {})
            if scripts:
                lines.append("| Script | Lines | Path |")
                lines.append("|--------|-------|------|")

                for script_name, script_data in scripts.items():
                    if isinstance(script_data, dict):
                        script_lines = script_data.get('lines', 'N/A')
                        script_path = script_data.get('path', 'N/A')
                        display_name = script_name.replace('_', ' ').title()
                        lines.append(f"| {display_name} | {script_lines} | `{script_path}` |")

                lines.append("")

        # Documentation
        documentation = plus_minus_data.get('documentation', {})
        if documentation:
            lines.append("### Documentation")
            lines.append("")
            total_doc_lines = documentation.get('total_lines', 'N/A')
            lines.append(f"**Total Documentation Lines:** {total_doc_lines:,}")
            lines.append("")

            files = documentation.get('files', [])
            if files:
                lines.append("| Document | Lines |")
                lines.append("|----------|-------|")

                for file_data in files:
                    if isinstance(file_data, dict):
                        file_name = file_data.get('name', 'N/A')
                        file_lines = file_data.get('lines', 'N/A')
                        lines.append(f"| {file_name} | {file_lines} |")

                lines.append("")

        return "\n".join(lines)

    def _format_code_base(self, code_data: Dict[str, Any]) -> str:
        """Format code base section."""
        lines = []
        lines.append("## Code Base")
        lines.append("")

        python_files = code_data.get('python_files', {})
        test_files = code_data.get('test_files', {})
        ml_scripts = code_data.get('ml_scripts', {})
        phase_9_scripts = code_data.get('phase_9_scripts', {})

        lines.append("### Overview")
        lines.append("")
        lines.append(f"- **Total Python Files:** {python_files.get('value', 'N/A'):,}")
        lines.append(f"- **Test Files:** {test_files.get('value', 'N/A'):,}")
        lines.append(f"- **ML Scripts:** {ml_scripts.get('value', 'N/A')}")
        lines.append(f"- **Phase 9 Scripts:** {phase_9_scripts.get('value', 'N/A')}")
        lines.append("")

        return "\n".join(lines)

    def _format_documentation(self, doc_data: Dict[str, Any]) -> str:
        """Format documentation section."""
        lines = []
        lines.append("## Documentation")
        lines.append("")

        markdown_files = doc_data.get('markdown_files', {})
        total_size = doc_data.get('total_size_mb', {})

        lines.append(f"- **Markdown Files:** {markdown_files.get('value', 'N/A'):,}")
        lines.append(f"- **Total Size:** {total_size.get('value', 'N/A')} MB")
        lines.append("")

        return "\n".join(lines)

    def _format_git_metrics(self, git_data: Dict[str, Any]) -> str:
        """Format git metrics section."""
        lines = []
        lines.append("## Git Metrics")
        lines.append("")

        book_commits = git_data.get('book_recommendation_commits', {})

        lines.append(f"- **Book Recommendation Commits:** {book_commits.get('value', 'N/A'):,}")
        if isinstance(book_commits, dict) and 'description' in book_commits:
            lines.append(f"  - {book_commits['description']}")
        lines.append("")

        return "\n".join(lines)

    def _format_workflows(self, workflow_data: Dict[str, Any]) -> str:
        """Format workflows section."""
        lines = []
        lines.append("## Workflows")
        lines.append("")

        total = workflow_data.get('total', {})

        lines.append(f"- **Total Workflow Files:** {total.get('value', 'N/A')}")
        if isinstance(total, dict) and 'directory' in total:
            lines.append(f"- **Directory:** `{total['directory']}`")
        lines.append("")

        return "\n".join(lines)

    def _format_sql_schemas(self, sql_data: Dict[str, Any]) -> str:
        """Format SQL schemas section."""
        lines = []
        lines.append("## SQL Schemas")
        lines.append("")

        total_lines = sql_data.get('total_lines', {})

        if isinstance(total_lines, dict):
            value = total_lines.get('value', 'N/A')
            lines.append(f"**Total Lines:** {value:,}")
            lines.append("")

            files = total_lines.get('files', [])
            if files:
                lines.append("### Schema Files")
                lines.append("")
                lines.append("| File | Lines |")
                lines.append("|------|-------|")

                for file_data in files:
                    if isinstance(file_data, dict):
                        file_name = file_data.get('name', 'N/A')
                        file_lines = file_data.get('lines', 'N/A')
                        lines.append(f"| `{file_name}` | {file_lines} |")

                lines.append("")

        return "\n".join(lines)

    def _format_local_data(self, local_data: Dict[str, Any]) -> str:
        """Format local data section."""
        lines = []
        lines.append("## Local Data")
        lines.append("")

        espn_size = local_data.get('espn_size_gb', {})

        if isinstance(espn_size, dict):
            value = espn_size.get('value', 'N/A')
            path = espn_size.get('path', 'N/A')
            note = espn_size.get('note', '')

            lines.append(f"- **ESPN Data Size:** {value} GB")
            lines.append(f"- **Path:** `{path}`")
            if note:
                lines.append(f"- **Note:** {note}")
            lines.append("")

        return "\n".join(lines)

    def generate(self, metrics: Dict[str, Any], output_path: Path) -> bool:
        """Generate Markdown inventory file."""
        try:
            lines = []

            # Header
            if self.template == 'master_inventory':
                lines.append("# NBA Simulator - Master Data Inventory")
            else:
                lines.append("# NBA Simulator - Data Collection Inventory")

            lines.append("")
            lines.append("**Auto-generated by DIMS** (Data Inventory Management System)")
            lines.append("")

            # Metadata
            metadata = metrics.get('metadata', {})
            lines.append(self._format_metadata(metadata))

            # Main sections
            if 's3_storage' in metrics:
                lines.append(self._format_s3_storage(metrics['s3_storage']))

            if 'prediction_system' in metrics:
                lines.append(self._format_prediction_system(metrics['prediction_system']))

            if 'plus_minus_system' in metrics:
                lines.append(self._format_plus_minus_system(metrics['plus_minus_system']))

            if 'code_base' in metrics:
                lines.append(self._format_code_base(metrics['code_base']))

            if 'documentation' in metrics:
                lines.append(self._format_documentation(metrics['documentation']))

            if 'git' in metrics:
                lines.append(self._format_git_metrics(metrics['git']))

            if 'workflows' in metrics:
                lines.append(self._format_workflows(metrics['workflows']))

            if 'sql_schemas' in metrics:
                lines.append(self._format_sql_schemas(metrics['sql_schemas']))

            if 'local_data' in metrics:
                lines.append(self._format_local_data(metrics['local_data']))

            # Footer
            lines.append("---")
            lines.append("")
            lines.append(f"*Last generated: {datetime.now().isoformat()}*")
            lines.append("")

            # Write to file
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                f.write("\n".join(lines))

            logger.info(f"Generated Markdown inventory: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating Markdown inventory: {e}")
            return False


class JSONGenerator(OutputGenerator):
    """Generate JSON output from metrics."""

    def generate(self, metrics: Dict[str, Any], output_path: Path) -> bool:
        """Generate JSON inventory file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)

            logger.info(f"Generated JSON inventory: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating JSON inventory: {e}")
            return False


class DIMSOutputManager:
    """High-level output manager for DIMS."""

    def __init__(self, config: Dict[str, Any], project_root: Path):
        """
        Initialize DIMS output manager.

        Args:
            config: DIMS configuration dict
            project_root: Project root path
        """
        self.config = config
        self.project_root = project_root
        self.output_config = config.get('outputs', {})

    def generate_all(self, metrics: Dict[str, Any]) -> Dict[str, bool]:
        """
        Generate all configured outputs.

        Args:
            metrics: Metrics dict to output

        Returns:
            Dict mapping output type to success status
        """
        results = {}

        # Markdown outputs
        markdown_config = self.output_config.get('markdown', {})
        if markdown_config.get('enabled', True):
            for file_config in markdown_config.get('files', []):
                path = self.project_root / file_config.get('path', '')
                template = file_config.get('template', 'master_inventory')

                generator = MarkdownGenerator(template=template)
                success = generator.generate(metrics, path)
                results[f"markdown:{template}"] = success

        # JSON outputs
        json_config = self.output_config.get('json', {})
        if json_config.get('enabled', True):
            for file_config in json_config.get('files', []):
                path = self.project_root / file_config.get('path', '')

                generator = JSONGenerator()
                success = generator.generate(metrics, path)
                results[f"json:{path.name}"] = success

        # HTML output (future)
        html_config = self.output_config.get('html', {})
        if html_config.get('enabled', False):
            logger.warning("HTML output not yet implemented")
            results['html'] = False

        # Jupyter output (future)
        jupyter_config = self.output_config.get('jupyter', {})
        if jupyter_config.get('enabled', False):
            logger.warning("Jupyter output not yet implemented")
            results['jupyter'] = False

        return results

    def generate_markdown(self, metrics: Dict[str, Any], template: str = 'master_inventory') -> bool:
        """Generate a single Markdown output."""
        markdown_config = self.output_config.get('markdown', {})

        if not markdown_config.get('enabled', True):
            logger.warning("Markdown output is disabled")
            return False

        # Find matching template
        for file_config in markdown_config.get('files', []):
            if file_config.get('template') == template:
                path = self.project_root / file_config.get('path', '')
                generator = MarkdownGenerator(template=template)
                return generator.generate(metrics, path)

        logger.error(f"No Markdown output configured for template: {template}")
        return False

    def generate_json(self, metrics: Dict[str, Any]) -> bool:
        """Generate JSON output."""
        json_config = self.output_config.get('json', {})

        if not json_config.get('enabled', True):
            logger.warning("JSON output is disabled")
            return False

        # Generate first configured JSON file
        for file_config in json_config.get('files', []):
            path = self.project_root / file_config.get('path', '')
            generator = JSONGenerator()
            return generator.generate(metrics, path)

        logger.error("No JSON output configured")
        return False
