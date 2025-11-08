"""
Quality Report Generator

Generates automated quality reports in various formats:
- Markdown reports
- JSON exports
- HTML dashboards (future)
- Email summaries (future)

Created: November 5, 2025
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from .base import (
    QualityMonitor,
    QualityAlert,
    QualityCheck,
    QualityStatus,
    QualitySeverity,
)
from .metrics import QualityMetricsTracker


class ReportFormat(Enum):
    """Report output formats"""

    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    TEXT = "text"


@dataclass
class ReportSection:
    """
    Section of a quality report.

    Attributes:
        title: Section title
        content: Section content
        level: Heading level (1-6)
        subsections: Nested subsections
    """

    title: str
    content: str = ""
    level: int = 2
    subsections: List["ReportSection"] = None

    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []


class QualityReportGenerator:
    """
    Generates quality reports in various formats.

    Supports:
    - Daily quality summaries
    - Trend analysis reports
    - Alert summaries
    - Metric history reports
    """

    def __init__(
        self,
        monitor: QualityMonitor,
        metrics_tracker: Optional[QualityMetricsTracker] = None,
    ):
        """
        Initialize report generator.

        Args:
            monitor: Quality monitor instance
            metrics_tracker: Optional metrics tracker for historical data
        """
        self.monitor = monitor
        self.metrics_tracker = metrics_tracker or QualityMetricsTracker()

    def generate_daily_report(
        self, format: ReportFormat = ReportFormat.MARKDOWN
    ) -> str:
        """
        Generate daily quality report.

        Args:
            format: Output format

        Returns:
            Report string in specified format
        """
        sections = self._build_daily_report_sections()

        if format == ReportFormat.MARKDOWN:
            return self._render_markdown(sections)
        elif format == ReportFormat.JSON:
            return self._render_json(sections)
        elif format == ReportFormat.TEXT:
            return self._render_text(sections)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _build_daily_report_sections(self) -> List[ReportSection]:
        """
        Build sections for daily report.

        Returns:
            List of report sections
        """
        sections = []

        # Header
        sections.append(self._build_header_section())

        # Executive Summary
        sections.append(self._build_summary_section())

        # Recent Checks
        sections.append(self._build_checks_section())

        # Active Alerts
        sections.append(self._build_alerts_section())

        # Metrics Overview
        sections.append(self._build_metrics_section())

        # Trends
        sections.append(self._build_trends_section())

        # Recommendations
        sections.append(self._build_recommendations_section())

        return sections

    def _build_header_section(self) -> ReportSection:
        """Build report header"""
        now = datetime.now(timezone.utc)

        content = f"""
**Date:** {now.strftime('%Y-%m-%d')}
**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Monitor:** {self.monitor.monitor_name}
"""

        return ReportSection(
            title="Daily Data Quality Report", content=content.strip(), level=1
        )

    def _build_summary_section(self) -> ReportSection:
        """Build executive summary"""
        summary = self.monitor.get_summary()

        total_checks = summary["total_checks"]
        total_metrics = summary["total_metrics"]
        active_alerts = summary["active_alerts"]

        status_counts = summary["status_counts"]
        passed = status_counts.get("passed", 0)
        warnings = status_counts.get("warnings", 0)
        failed = status_counts.get("failed", 0)

        # Overall health
        if failed > 0:
            health = "🔴 CRITICAL"
        elif warnings > 0:
            health = "🟡 WARNING"
        else:
            health = "🟢 HEALTHY"

        content = f"""
**Overall Health:** {health}

**Key Metrics:**
- Quality Checks: {total_checks}
- Metrics Collected: {total_metrics}
- Active Alerts: {active_alerts}

**Status Breakdown:**
- ✅ Passed: {passed}
- ⚠️  Warnings: {warnings}
- ❌ Failed: {failed}
"""

        return ReportSection(
            title="Executive Summary", content=content.strip(), level=2
        )

    def _build_checks_section(self) -> ReportSection:
        """Build recent checks section"""
        checks = self.monitor.checks[-10:]  # Last 10 checks

        if not checks:
            return ReportSection(
                title="Recent Quality Checks", content="*No recent checks*", level=2
            )

        content_lines = []
        for check in checks:
            status_emoji = self._get_status_emoji(check.status)
            content_lines.append(
                f"- {status_emoji} **{check.check_name}** "
                f"({check.check_type}): "
                f"{check.passed} passed, {check.warnings} warnings, {check.failed} failed "
                f"[{check.duration_seconds:.2f}s]"
            )

        return ReportSection(
            title="Recent Quality Checks", content="\n".join(content_lines), level=2
        )

    def _build_alerts_section(self) -> ReportSection:
        """Build active alerts section"""
        active_alerts = self.monitor.get_active_alerts()

        if not active_alerts:
            return ReportSection(
                title="Active Alerts", content="✅ No active alerts", level=2
            )

        # Group by severity
        by_severity = {}
        for alert in active_alerts:
            severity = alert.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(alert)

        content_lines = [f"**Total Active Alerts:** {len(active_alerts)}\n"]

        for severity in [
            QualitySeverity.CRITICAL,
            QualitySeverity.HIGH,
            QualitySeverity.MEDIUM,
            QualitySeverity.LOW,
        ]:
            alerts = by_severity.get(severity.value, [])
            if alerts:
                emoji = self._get_severity_emoji(severity)
                content_lines.append(
                    f"\n### {emoji} {severity.value.upper()} ({len(alerts)})"
                )
                for alert in alerts:
                    content_lines.append(
                        f"- **{alert.alert_type}**: {alert.message} "
                        f"({alert.timestamp.strftime('%H:%M:%S')})"
                    )

        return ReportSection(
            title="Active Alerts", content="\n".join(content_lines), level=2
        )

    def _build_metrics_section(self) -> ReportSection:
        """Build metrics overview section"""
        metrics = self.monitor.metrics[-20:]  # Last 20 metrics

        if not metrics:
            return ReportSection(
                title="Quality Metrics", content="*No metrics collected*", level=2
            )

        # Group by type
        by_type = {}
        for metric in metrics:
            if metric.metric_type not in by_type:
                by_type[metric.metric_type] = []
            by_type[metric.metric_type].append(metric)

        content_lines = []
        for metric_type, type_metrics in by_type.items():
            content_lines.append(f"\n### {metric_type.title()} Metrics")
            for metric in type_metrics[-5:]:  # Last 5 of each type
                status_emoji = self._get_status_emoji(metric.status)
                content_lines.append(
                    f"- {status_emoji} **{metric.metric_name}**: {metric.metric_value:.2f}"
                )
                if metric.threshold:
                    content_lines[-1] += f" (threshold: {metric.threshold:.2f})"

        return ReportSection(
            title="Quality Metrics", content="\n".join(content_lines), level=2
        )

    def _build_trends_section(self) -> ReportSection:
        """Build trends analysis section"""
        # Get unique metric names from recent metrics
        metric_names = set(m.metric_name for m in self.monitor.metrics[-50:])

        if not metric_names:
            return ReportSection(
                title="Trend Analysis",
                content="*Not enough data for trend analysis*",
                level=2,
            )

        content_lines = []
        for metric_name in sorted(metric_names):
            trend = self.metrics_tracker.calculate_trend(metric_name, hours=24)
            if trend:
                direction_emoji = (
                    "📈"
                    if trend.trend_direction == "up"
                    else "📉" if trend.trend_direction == "down" else "➡️"
                )
                improving_emoji = "✅" if trend.is_improving else "⚠️"
                content_lines.append(
                    f"- {direction_emoji} **{metric_name}**: "
                    f"{trend.current_value:.2f} "
                    f"({trend.percent_change:+.1f}% change) "
                    f"{improving_emoji}"
                )

        if not content_lines:
            return ReportSection(
                title="Trend Analysis", content="*Not enough historical data*", level=2
            )

        return ReportSection(
            title="Trend Analysis (24h)", content="\n".join(content_lines), level=2
        )

    def _build_recommendations_section(self) -> ReportSection:
        """Build recommendations section"""
        recommendations = []

        # Analyze current state and provide recommendations
        active_alerts = self.monitor.get_active_alerts()
        critical_alerts = [
            a for a in active_alerts if a.severity == QualitySeverity.CRITICAL
        ]

        if critical_alerts:
            recommendations.append(
                "🚨 **URGENT**: Address critical alerts immediately:\n"
                + "\n".join(f"  - {a.message}" for a in critical_alerts[:3])
            )

        failed_metrics = [
            m for m in self.monitor.metrics[-50:] if m.status == QualityStatus.FAIL
        ]
        if len(failed_metrics) > 10:
            recommendations.append(
                f"⚠️  **HIGH**: Multiple quality metrics failing ({len(failed_metrics)} in last 50)"
            )

        warning_metrics = [
            m for m in self.monitor.metrics[-50:] if m.status == QualityStatus.WARNING
        ]
        if len(warning_metrics) > 20:
            recommendations.append(
                f"📊 **MEDIUM**: Review warning metrics ({len(warning_metrics)} warnings)"
            )

        if not recommendations:
            recommendations.append(
                "✅ No immediate action required. All systems healthy."
            )

        return ReportSection(
            title="Recommendations", content="\n\n".join(recommendations), level=2
        )

    def _render_markdown(self, sections: List[ReportSection]) -> str:
        """
        Render sections as Markdown.

        Args:
            sections: Report sections

        Returns:
            Markdown string
        """
        lines = []

        for section in sections:
            # Add heading
            lines.append(f"{'#' * section.level} {section.title}\n")

            # Add content
            if section.content:
                lines.append(section.content)
                lines.append("")

            # Add subsections
            for subsection in section.subsections:
                lines.append(self._render_markdown([subsection]))

        return "\n".join(lines)

    def _render_json(self, sections: List[ReportSection]) -> str:
        """
        Render sections as JSON.

        Args:
            sections: Report sections

        Returns:
            JSON string
        """
        report_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "monitor": self.monitor.monitor_name,
            "summary": self.monitor.get_summary(),
            "sections": [
                {"title": s.title, "content": s.content, "level": s.level}
                for s in sections
            ],
        }

        return json.dumps(report_data, indent=2)

    def _render_text(self, sections: List[ReportSection]) -> str:
        """
        Render sections as plain text.

        Args:
            sections: Report sections

        Returns:
            Text string
        """
        lines = []

        for section in sections:
            # Add heading with underline
            lines.append(section.title.upper())
            lines.append("=" * len(section.title))
            lines.append("")

            # Add content (strip markdown formatting)
            if section.content:
                # Simple markdown stripping
                content = section.content
                content = content.replace("**", "")
                content = content.replace("*", "")
                content = content.replace("#", "")
                lines.append(content)
                lines.append("")

        return "\n".join(lines)

    def save_report(
        self,
        report: str,
        output_dir: Path,
        filename: Optional[str] = None,
        format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> Path:
        """
        Save report to file.

        Args:
            report: Report content
            output_dir: Directory to save report
            filename: Optional filename (auto-generated if None)
            format: Report format

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = format.value if format != ReportFormat.MARKDOWN else "md"
            filename = f"quality_report_{timestamp}.{ext}"

        output_path = output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(report)
        return output_path

    @staticmethod
    def _get_status_emoji(status: QualityStatus) -> str:
        """Get emoji for quality status"""
        return {
            QualityStatus.PASS: "✅",
            QualityStatus.WARNING: "⚠️",
            QualityStatus.FAIL: "❌",
            QualityStatus.ERROR: "🔴",
            QualityStatus.UNKNOWN: "❓",
        }.get(status, "")

    @staticmethod
    def _get_severity_emoji(severity: QualitySeverity) -> str:
        """Get emoji for severity level"""
        return {
            QualitySeverity.INFO: "ℹ️",
            QualitySeverity.LOW: "🔵",
            QualitySeverity.MEDIUM: "🟡",
            QualitySeverity.HIGH: "🟠",
            QualitySeverity.CRITICAL: "🔴",
        }.get(severity, "")
