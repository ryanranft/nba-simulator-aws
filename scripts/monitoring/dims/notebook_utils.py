"""
DIMS Jupyter Notebook Utilities
Helper functions for interactive data exploration and visualization.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class DIMSNotebookHelper:
    """Helper class for DIMS Jupyter notebooks."""

    def __init__(self, core):
        """
        Initialize notebook helper.

        Args:
            core: DIMSCore instance
        """
        self.core = core
        self.db = core.database

    # =========================================================================
    # Database Query Helpers
    # =========================================================================

    def get_latest_metrics(self) -> pd.DataFrame:
        """
        Get all latest metrics as a DataFrame.

        Returns:
            DataFrame with columns: category, metric, value, recorded_at
        """
        if not self.db:
            logger.warning("Database not available")
            return pd.DataFrame()

        query = """
            SELECT
                metric_category,
                metric_name,
                value,
                value_type,
                numeric_value,
                recorded_at
            FROM dims_metrics_latest
            ORDER BY metric_category, metric_name
        """

        conn = self.db.pool.getconn()
        try:
            df = pd.read_sql_query(query, conn)
            return df
        finally:
            self.db.pool.putconn(conn)

    def get_metric_history(
        self,
        category: str,
        metric: str,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Get metric history for trend analysis.

        Args:
            category: Metric category
            metric: Metric name
            days: Number of days to retrieve

        Returns:
            DataFrame with columns: recorded_at, value, numeric_value
        """
        if not self.db:
            logger.warning("Database not available")
            return pd.DataFrame()

        query = """
            SELECT
                recorded_at,
                value,
                numeric_value
            FROM dims_metrics_history
            WHERE metric_category = %s
              AND metric_name = %s
              AND recorded_at >= NOW() - INTERVAL '%s days'
            ORDER BY recorded_at
        """

        conn = self.db.pool.getconn()
        try:
            df = pd.read_sql_query(query, conn, params=(category, metric, days))
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])
            return df
        finally:
            self.db.pool.putconn(conn)

    def get_verification_runs(self, days: int = 30) -> pd.DataFrame:
        """
        Get verification run history.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame with verification run data
        """
        if not self.db:
            logger.warning("Database not available")
            return pd.DataFrame()

        query = """
            SELECT
                id,
                run_timestamp,
                total_metrics,
                metrics_verified,
                drift_detected,
                auto_updated,
                execution_time_ms,
                triggered_by
            FROM dims_verification_runs
            WHERE run_timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY run_timestamp DESC
        """

        conn = self.db.pool.getconn()
        try:
            df = pd.read_sql_query(query, conn, params=(days,))
            df['run_timestamp'] = pd.to_datetime(df['run_timestamp'])
            return df
        finally:
            self.db.pool.putconn(conn)

    def get_approval_log(self, days: int = 30) -> pd.DataFrame:
        """
        Get approval workflow history.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame with approval data
        """
        if not self.db:
            logger.warning("Database not available")
            return pd.DataFrame()

        query = """
            SELECT
                id,
                metric_category,
                metric_name,
                old_value,
                new_value,
                drift_pct,
                status,
                requested_at,
                reviewed_at,
                reviewed_by
            FROM dims_approval_log
            WHERE requested_at >= NOW() - INTERVAL '%s days'
            ORDER BY requested_at DESC
        """

        conn = self.db.pool.getconn()
        try:
            df = pd.read_sql_query(query, conn, params=(days,))
            df['requested_at'] = pd.to_datetime(df['requested_at'])
            if 'reviewed_at' in df.columns:
                df['reviewed_at'] = pd.to_datetime(df['reviewed_at'])
            return df
        finally:
            self.db.pool.putconn(conn)

    def get_event_log(self, days: int = 7) -> pd.DataFrame:
        """
        Get event processing history.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame with event data
        """
        if not self.db:
            logger.warning("Database not available")
            return pd.DataFrame()

        query = """
            SELECT
                id,
                event_type,
                event_source,
                triggered_at,
                metrics_updated,
                success,
                error_message
            FROM dims_event_log
            WHERE triggered_at >= NOW() - INTERVAL '%s days'
            ORDER BY triggered_at DESC
        """

        conn = self.db.pool.getconn()
        try:
            df = pd.read_sql_query(query, conn, params=(days,))
            df['triggered_at'] = pd.to_datetime(df['triggered_at'])
            return df
        finally:
            self.db.pool.putconn(conn)

    # =========================================================================
    # Visualization Helpers
    # =========================================================================

    def plot_metric_trend(
        self,
        category: str,
        metric: str,
        days: int = 30
    ) -> go.Figure:
        """
        Create interactive trend chart for a metric.

        Args:
            category: Metric category
            metric: Metric name
            days: Number of days to show

        Returns:
            Plotly figure
        """
        df = self.get_metric_history(category, metric, days)

        if df.empty:
            logger.warning(f"No data for {category}.{metric}")
            return go.Figure()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['recorded_at'],
            y=df['numeric_value'],
            mode='lines+markers',
            name=f"{category}.{metric}",
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=6),
            hovertemplate='<b>%{y}</b><br>%{x|%Y-%m-%d %H:%M}<extra></extra>'
        ))

        fig.update_layout(
            title=f"Trend: {category}.{metric}",
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )

        return fig

    def plot_metrics_overview(self) -> go.Figure:
        """
        Create overview dashboard of all metrics.

        Returns:
            Plotly figure with metric counts by category
        """
        df = self.get_latest_metrics()

        if df.empty:
            return go.Figure()

        # Count metrics by category
        category_counts = df.groupby('metric_category').size().reset_index(name='count')

        fig = px.bar(
            category_counts,
            x='metric_category',
            y='count',
            title='Metrics by Category',
            labels={'metric_category': 'Category', 'count': 'Metric Count'},
            color='count',
            color_continuous_scale='Blues'
        )

        fig.update_layout(
            template='plotly_white',
            height=400,
            showlegend=False
        )

        return fig

    def plot_verification_timeline(self, days: int = 30) -> go.Figure:
        """
        Create timeline of verification runs.

        Args:
            days: Number of days to show

        Returns:
            Plotly figure
        """
        df = self.get_verification_runs(days)

        if df.empty:
            return go.Figure()

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Metrics Verified', 'Execution Time'),
            vertical_spacing=0.15
        )

        # Metrics verified over time
        fig.add_trace(
            go.Scatter(
                x=df['run_timestamp'],
                y=df['metrics_verified'],
                mode='lines+markers',
                name='Metrics Verified',
                line=dict(color='#06A77D', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )

        # Execution time over time
        fig.add_trace(
            go.Scatter(
                x=df['run_timestamp'],
                y=df['execution_time_ms'] / 1000,  # Convert to seconds
                mode='lines+markers',
                name='Execution Time (s)',
                line=dict(color='#D62828', width=2),
                marker=dict(size=6)
            ),
            row=2, col=1
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Seconds", row=2, col=1)

        fig.update_layout(
            title_text="Verification Run Timeline",
            template='plotly_white',
            height=600,
            showlegend=False
        )

        return fig

    def plot_drift_heatmap(self, days: int = 30) -> go.Figure:
        """
        Create heatmap of metric drift over time.

        Args:
            days: Number of days to show

        Returns:
            Plotly figure
        """
        # Get all metrics with history
        df_latest = self.get_latest_metrics()

        if df_latest.empty:
            return go.Figure()

        # Build drift matrix
        drift_data = []
        categories = []
        metrics = []

        for _, row in df_latest.iterrows():
            category = row['metric_category']
            metric = row['metric_name']

            history = self.get_metric_history(category, metric, days)

            if len(history) > 1:
                # Calculate drift percentage from first to last
                first_val = history.iloc[0]['numeric_value']
                last_val = history.iloc[-1]['numeric_value']

                if first_val and first_val != 0:
                    drift_pct = ((last_val - first_val) / first_val) * 100
                    drift_data.append(drift_pct)
                    categories.append(category)
                    metrics.append(metric)

        if not drift_data:
            return go.Figure()

        # Create heatmap
        fig = go.Figure(data=go.Bar(
            x=metrics,
            y=drift_data,
            marker=dict(
                color=drift_data,
                colorscale='RdYlGn',
                cmid=0,
                colorbar=dict(title="Drift %")
            ),
            text=[f"{d:.1f}%" for d in drift_data],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Drift: %{y:.2f}%<extra></extra>'
        ))

        fig.update_layout(
            title=f"Metric Drift ({days} days)",
            xaxis_title="Metric",
            yaxis_title="Drift %",
            template='plotly_white',
            height=400
        )

        return fig

    def plot_approval_status(self, days: int = 30) -> go.Figure:
        """
        Create approval workflow status visualization.

        Args:
            days: Number of days to show

        Returns:
            Plotly figure
        """
        df = self.get_approval_log(days)

        if df.empty:
            return go.Figure()

        # Count by status
        status_counts = df.groupby('status').size().reset_index(name='count')

        fig = px.pie(
            status_counts,
            names='status',
            values='count',
            title='Approval Workflow Status',
            color='status',
            color_discrete_map={
                'pending': '#FFC857',
                'approved': '#06A77D',
                'rejected': '#D62828'
            }
        )

        fig.update_layout(
            template='plotly_white',
            height=400
        )

        return fig

    # =========================================================================
    # Analysis Helpers
    # =========================================================================

    def get_drift_summary(self, days: int = 30) -> pd.DataFrame:
        """
        Analyze drift across all metrics.

        Args:
            days: Number of days to analyze

        Returns:
            DataFrame with drift analysis
        """
        df_latest = self.get_latest_metrics()

        if df_latest.empty:
            return pd.DataFrame()

        results = []

        for _, row in df_latest.iterrows():
            category = row['metric_category']
            metric = row['metric_name']

            history = self.get_metric_history(category, metric, days)

            if len(history) > 1:
                first_val = history.iloc[0]['numeric_value']
                last_val = history.iloc[-1]['numeric_value']
                min_val = history['numeric_value'].min()
                max_val = history['numeric_value'].max()

                if first_val and first_val != 0:
                    drift_pct = ((last_val - first_val) / first_val) * 100
                    volatility = ((max_val - min_val) / first_val) * 100 if first_val != 0 else 0

                    results.append({
                        'category': category,
                        'metric': metric,
                        'first_value': first_val,
                        'last_value': last_val,
                        'drift_pct': drift_pct,
                        'min_value': min_val,
                        'max_value': max_val,
                        'volatility_pct': volatility,
                        'data_points': len(history)
                    })

        return pd.DataFrame(results)

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health metrics.

        Returns:
            Dictionary with health statistics
        """
        health = {
            'total_metrics': 0,
            'metrics_with_data': 0,
            'recent_verifications': 0,
            'pending_approvals': 0,
            'recent_events': 0,
            'avg_execution_time_ms': 0
        }

        # Count metrics
        df_latest = self.get_latest_metrics()
        health['total_metrics'] = len(self.core.metrics)
        health['metrics_with_data'] = len(df_latest)

        # Count recent verifications
        df_verifications = self.get_verification_runs(days=7)
        health['recent_verifications'] = len(df_verifications)

        if not df_verifications.empty:
            health['avg_execution_time_ms'] = df_verifications['execution_time_ms'].mean()

        # Count pending approvals
        if self.core.approval:
            pending = self.core.approval.get_pending_approvals()
            health['pending_approvals'] = len(pending)

        # Count recent events
        df_events = self.get_event_log(days=7)
        health['recent_events'] = len(df_events)

        return health

    # =========================================================================
    # Export Helpers
    # =========================================================================

    def export_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """
        Export DataFrame to CSV.

        Args:
            df: DataFrame to export
            filename: Output filename

        Returns:
            Path to exported file
        """
        output_dir = Path(self.core.project_root) / 'inventory' / 'exports'
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / filename
        df.to_csv(output_path, index=False)

        logger.info(f"Exported to {output_path}")
        return str(output_path)

    def export_to_excel(self, dataframes: Dict[str, pd.DataFrame], filename: str) -> str:
        """
        Export multiple DataFrames to Excel with sheets.

        Args:
            dataframes: Dictionary of {sheet_name: DataFrame}
            filename: Output filename

        Returns:
            Path to exported file
        """
        output_dir = Path(self.core.project_root) / 'inventory' / 'exports'
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / filename

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Exported to {output_path}")
        return str(output_path)
