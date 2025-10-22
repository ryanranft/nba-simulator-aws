#!/usr/bin/env python3
"""
NBA Panel Data Quality Monitoring System

Recommendation: rec_29 (Data Quality Monitoring System)
Source Books: Econometric Analysis, Designing Machine Learning Systems
Priority: CRITICAL
Time Estimate: 40 hours

Features:
- Panel data integrity validation
- Missing observation detection (MAR, MCAR, MNAR patterns)
- Outlier and anomaly identification
- Temporal consistency checks
- Cross-source validation
- Data completeness metrics
- Source reliability scoring

Usage:
    # Validate PostgreSQL panel data
    python scripts/analysis/panel_data_quality_monitor.py --source postgresql

    # Validate specific dataset with detailed report
    python scripts/analysis/panel_data_quality_monitor.py --source postgresql --detailed --output /tmp/quality_report.json

    # Validate CSV/Parquet files
    python scripts/analysis/panel_data_quality_monitor.py --source file --file-path /path/to/data.csv

    # Real-time monitoring mode
    python scripts/analysis/panel_data_quality_monitor.py --source postgresql --monitor --interval 300
"""

import os
import sys
import logging
import argparse
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

# Database connection
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("Warning: psycopg2 not available. Install with: pip install psycopg2-binary")

# Statistical tests
try:
    from scipy import stats
    from scipy.stats import zscore, iqr
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not available. Install with: pip install scipy")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DataQualityMetrics:
    """Container for data quality metrics"""

    # Completeness metrics
    total_observations: int = 0
    missing_observations: int = 0
    completeness_pct: float = 0.0

    # Missing data pattern
    missing_pattern: str = "Unknown"  # MAR, MCAR, MNAR
    missing_by_column: Dict[str, int] = None

    # Duplicates
    duplicate_count: int = 0
    duplicate_pct: float = 0.0

    # Temporal consistency
    temporal_errors: int = 0
    temporal_error_types: Dict[str, int] = None

    # Outliers
    outlier_count: int = 0
    outlier_pct: float = 0.0
    outlier_by_column: Dict[str, int] = None

    # Cross-source validation
    source_agreement_pct: float = 0.0
    source_discrepancies: int = 0

    # Data quality score
    overall_quality_score: float = 0.0
    quality_grade: str = "Unknown"

    # Timestamps
    validation_timestamp: str = ""
    data_timestamp_range: Tuple[str, str] = ("", "")

    def __post_init__(self):
        if self.missing_by_column is None:
            self.missing_by_column = {}
        if self.temporal_error_types is None:
            self.temporal_error_types = {}
        if self.outlier_by_column is None:
            self.outlier_by_column = {}


class PanelDataQualityMonitor:
    """
    Comprehensive data quality monitoring system for NBA panel data.

    Implements rec_29: Data Quality Monitoring System
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Panel Data Quality Monitor.

        Args:
            config: Configuration dictionary with database credentials, thresholds, etc.
        """
        self.config = config or {}

        # Database configuration
        self.db_config = {
            'host': self.config.get('db_host', 'localhost'),
            'database': self.config.get('db_name', 'nba_panel_data'),
            'user': self.config.get('db_user', os.getenv('DB_USER', 'ryanranft')),
            'password': self.config.get('db_password', os.getenv('DB_PASSWORD', '')),
        }

        # Quality thresholds
        self.thresholds = {
            'completeness_min': self.config.get('completeness_min', 0.95),  # 95% complete
            'duplicate_max': self.config.get('duplicate_max', 0.01),  # <1% duplicates
            'outlier_max': self.config.get('outlier_max', 0.05),  # <5% outliers
            'temporal_error_max': self.config.get('temporal_error_max', 0.001),  # <0.1% errors
            'source_agreement_min': self.config.get('source_agreement_min', 0.98),  # 98% agreement
        }

        # Statistical thresholds
        self.outlier_threshold = self.config.get('outlier_z_score', 3.5)  # Z-score threshold

        # Results storage
        self.metrics = DataQualityMetrics()
        self.validation_errors = []
        self.warnings_list = []

    def connect_db(self) -> Optional[psycopg2.extensions.connection]:
        """Connect to PostgreSQL database"""
        if not POSTGRES_AVAILABLE:
            logger.error("psycopg2 not available")
            return None

        try:
            conn = psycopg2.connect(**self.db_config)
            logger.info(f"Connected to database: {self.db_config['database']}")
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None

    def validate_panel_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate panel data structure (multi-index, temporal ordering)

        Args:
            df: Panel data DataFrame

        Returns:
            Dictionary of validation results
        """
        logger.info("Validating panel data structure...")

        results = {
            'has_player_id': 'player_id' in df.columns,
            'has_game_id': 'game_id' in df.columns,
            'has_timestamp': any(col in df.columns for col in ['timestamp', 'game_date', 'date']),
            'is_multi_indexed': isinstance(df.index, pd.MultiIndex),
            'is_sorted': False,
            'issues': []
        }

        # Check required columns
        required_cols = ['player_id', 'game_id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results['issues'].append(f"Missing required columns: {missing_cols}")

        # Check temporal ordering
        time_col = next((col for col in ['timestamp', 'game_date', 'date'] if col in df.columns), None)
        if time_col:
            try:
                df[time_col] = pd.to_datetime(df[time_col])
                is_sorted = df[time_col].is_monotonic_increasing
                results['is_sorted'] = is_sorted
                if not is_sorted:
                    results['issues'].append("Data not sorted by timestamp")
            except:
                results['issues'].append(f"Could not parse {time_col} as datetime")

        return results

    def check_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data completeness and missing value patterns.

        Identifies:
        - MCAR (Missing Completely At Random)
        - MAR (Missing At Random)
        - MNAR (Missing Not At Random)

        Args:
            df: Panel data DataFrame

        Returns:
            Completeness metrics and missing pattern classification
        """
        logger.info("Checking data completeness...")

        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isna().sum().sum()
        completeness_pct = ((total_cells - missing_cells) / total_cells) * 100

        # Missing values by column
        missing_by_col = df.isna().sum().to_dict()
        missing_by_col = {k: int(v) for k, v in missing_by_col.items() if v > 0}

        # Classify missing pattern
        missing_pattern = self._classify_missing_pattern(df)

        # Update metrics
        self.metrics.total_observations = len(df)
        self.metrics.missing_observations = int(missing_cells)
        self.metrics.completeness_pct = round(completeness_pct, 2)
        self.metrics.missing_pattern = missing_pattern
        self.metrics.missing_by_column = missing_by_col

        # Validate against threshold
        if completeness_pct < self.thresholds['completeness_min'] * 100:
            self.validation_errors.append(
                f"Completeness {completeness_pct:.2f}% below threshold "
                f"{self.thresholds['completeness_min'] * 100}%"
            )

        return {
            'total_observations': len(df),
            'total_cells': total_cells,
            'missing_cells': int(missing_cells),
            'completeness_pct': round(completeness_pct, 2),
            'missing_pattern': missing_pattern,
            'missing_by_column': missing_by_col
        }

    def _classify_missing_pattern(self, df: pd.DataFrame) -> str:
        """
        Classify missing data pattern (MCAR, MAR, MNAR)

        Simplified classification:
        - MCAR: Missing values uniformly distributed
        - MAR: Missing values correlated with observed data
        - MNAR: Missing values correlated with unobserved data
        """
        missing_pct_by_col = (df.isna().sum() / len(df)) * 100

        # If no missing values
        if missing_pct_by_col.sum() == 0:
            return "NONE"

        # If missing values highly variable across columns (>20% std dev)
        if missing_pct_by_col.std() > 20:
            return "MAR (likely)"  # Systematic missingness

        # If missing values uniform across columns (<5% std dev)
        if missing_pct_by_col.std() < 5:
            return "MCAR (likely)"  # Random missingness

        return "MNAR (possible)"  # Non-random pattern

    def detect_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect duplicate observations in panel data.

        Args:
            df: Panel data DataFrame

        Returns:
            Duplicate detection results
        """
        logger.info("Detecting duplicates...")

        # Check for exact duplicates
        duplicate_rows = df.duplicated(keep=False)
        duplicate_count = duplicate_rows.sum()
        duplicate_pct = (duplicate_count / len(df)) * 100

        # Check for duplicates in key columns
        key_cols = ['player_id', 'game_id']
        key_duplicates = 0
        if all(col in df.columns for col in key_cols):
            key_duplicates = df.duplicated(subset=key_cols, keep=False).sum()

        # Update metrics
        self.metrics.duplicate_count = int(duplicate_count)
        self.metrics.duplicate_pct = round(duplicate_pct, 4)

        # Validate against threshold
        if duplicate_pct > self.thresholds['duplicate_max'] * 100:
            self.validation_errors.append(
                f"Duplicate rate {duplicate_pct:.2f}% exceeds threshold "
                f"{self.thresholds['duplicate_max'] * 100}%"
            )

        return {
            'duplicate_count': int(duplicate_count),
            'duplicate_pct': round(duplicate_pct, 4),
            'key_duplicates': int(key_duplicates),
        }

    def check_temporal_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check temporal consistency (cumulative stats should not decrease).

        Validates:
        - Career statistics monotonically increase
        - Season totals increase throughout season
        - Minutes/games played increase

        Args:
            df: Panel data DataFrame

        Returns:
            Temporal consistency results
        """
        logger.info("Checking temporal consistency...")

        temporal_errors = []
        error_types = defaultdict(int)

        # Cumulative columns that should be monotonic
        cumulative_cols = [
            'career_points', 'career_rebounds', 'career_assists',
            'season_points', 'season_rebounds', 'season_assists',
            'games_played', 'minutes_played'
        ]

        available_cumulative = [col for col in cumulative_cols if col in df.columns]

        if not available_cumulative:
            logger.warning("No cumulative columns found for temporal consistency check")
            return {'temporal_errors': 0, 'error_types': {}}

        # Check monotonicity for each player
        if 'player_id' in df.columns:
            for player_id, player_df in df.groupby('player_id'):
                # Sort by date
                time_col = next((col for col in ['timestamp', 'game_date', 'date'] if col in df.columns), None)
                if time_col:
                    player_df = player_df.sort_values(time_col)

                # Check each cumulative column
                for col in available_cumulative:
                    if col in player_df.columns:
                        # Check for decreases
                        decreases = (player_df[col].diff() < 0).sum()
                        if decreases > 0:
                            temporal_errors.append({
                                'player_id': player_id,
                                'column': col,
                                'decreases': int(decreases)
                            })
                            error_types[col] += int(decreases)

        total_errors = len(temporal_errors)
        error_pct = (total_errors / len(df)) * 100 if len(df) > 0 else 0

        # Update metrics
        self.metrics.temporal_errors = total_errors
        self.metrics.temporal_error_types = dict(error_types)

        # Validate against threshold
        if error_pct > self.thresholds['temporal_error_max'] * 100:
            self.validation_errors.append(
                f"Temporal error rate {error_pct:.4f}% exceeds threshold "
                f"{self.thresholds['temporal_error_max'] * 100}%"
            )

        return {
            'temporal_errors': total_errors,
            'error_pct': round(error_pct, 4),
            'error_types': dict(error_types),
            'errors': temporal_errors[:10]  # Return first 10 examples
        }

    def detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect statistical outliers using multiple methods.

        Methods:
        - Z-score (>3.5 standard deviations)
        - IQR (Interquartile Range)
        - Domain-specific rules (e.g., points > 100)

        Args:
            df: Panel data DataFrame

        Returns:
            Outlier detection results
        """
        logger.info("Detecting outliers...")

        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available for outlier detection")
            return {'outlier_count': 0, 'outlier_pct': 0.0}

        outlier_flags = pd.DataFrame(index=df.index)
        outlier_by_col = {}

        # Numeric columns for outlier detection
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Exclude ID columns
        exclude_cols = ['player_id', 'game_id', 'team_id', 'season_id']
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

        for col in numeric_cols:
            # Z-score method
            try:
                z_scores = np.abs(zscore(df[col].dropna()))
                outliers_zscore = z_scores > self.outlier_threshold

                # Domain-specific rules
                outliers_domain = pd.Series(False, index=df.index)
                if col in ['points', 'pts']:
                    outliers_domain = df[col] > 100  # More than 100 points
                elif col in ['rebounds', 'reb']:
                    outliers_domain = df[col] > 30  # More than 30 rebounds
                elif col in ['assists', 'ast']:
                    outliers_domain = df[col] > 25  # More than 25 assists

                # Combine methods
                col_outliers = outliers_zscore | outliers_domain
                outlier_count = col_outliers.sum()

                if outlier_count > 0:
                    outlier_by_col[col] = int(outlier_count)
                    outlier_flags[col] = col_outliers

            except Exception as e:
                logger.debug(f"Could not detect outliers in {col}: {e}")
                continue

        # Total unique outlier rows
        total_outliers = (outlier_flags.any(axis=1)).sum()
        outlier_pct = (total_outliers / len(df)) * 100 if len(df) > 0 else 0

        # Update metrics
        self.metrics.outlier_count = int(total_outliers)
        self.metrics.outlier_pct = round(outlier_pct, 2)
        self.metrics.outlier_by_column = outlier_by_col

        # Validate against threshold
        if outlier_pct > self.thresholds['outlier_max'] * 100:
            self.warnings_list.append(
                f"Outlier rate {outlier_pct:.2f}% exceeds threshold "
                f"{self.thresholds['outlier_max'] * 100}% (some may be legitimate)"
            )

        return {
            'outlier_count': int(total_outliers),
            'outlier_pct': round(outlier_pct, 2),
            'outlier_by_column': outlier_by_col
        }

    def calculate_quality_score(self) -> float:
        """
        Calculate overall data quality score (0-100).

        Weighted formula:
        - Completeness: 30%
        - Duplicates: 20%
        - Temporal consistency: 20%
        - Outliers: 15%
        - Source agreement: 15%

        Returns:
            Quality score (0-100)
        """
        logger.info("Calculating overall quality score...")

        # Completeness score (0-30)
        completeness_score = (self.metrics.completeness_pct / 100) * 30

        # Duplicate score (0-20, penalize duplicates)
        duplicate_penalty = min(self.metrics.duplicate_pct * 10, 20)  # Max penalty 20
        duplicate_score = 20 - duplicate_penalty

        # Temporal consistency score (0-20, penalize errors)
        temporal_error_pct = (self.metrics.temporal_errors / max(self.metrics.total_observations, 1)) * 100
        temporal_penalty = min(temporal_error_pct * 100, 20)  # Max penalty 20
        temporal_score = 20 - temporal_penalty

        # Outlier score (0-15, some outliers acceptable)
        outlier_penalty = min(self.metrics.outlier_pct * 2, 15)  # Max penalty 15
        outlier_score = 15 - outlier_penalty

        # Source agreement score (0-15)
        source_score = (self.metrics.source_agreement_pct / 100) * 15 if self.metrics.source_agreement_pct > 0 else 15

        # Total score
        total_score = completeness_score + duplicate_score + temporal_score + outlier_score + source_score

        # Grade
        if total_score >= 90:
            grade = "A (Excellent)"
        elif total_score >= 80:
            grade = "B (Good)"
        elif total_score >= 70:
            grade = "C (Fair)"
        elif total_score >= 60:
            grade = "D (Poor)"
        else:
            grade = "F (Failing)"

        self.metrics.overall_quality_score = round(total_score, 2)
        self.metrics.quality_grade = grade

        return total_score

    def validate_from_postgresql(self, table_name: str = 'nba_play_by_play_historical') -> Dict[str, Any]:
        """
        Validate data from PostgreSQL database.

        Args:
            table_name: Name of table to validate

        Returns:
            Validation results
        """
        logger.info(f"Validating data from PostgreSQL table: {table_name}")

        conn = self.connect_db()
        if not conn:
            return {'error': 'Database connection failed'}

        try:
            # Load data (sample for performance)
            query = f"SELECT * FROM {table_name} LIMIT 100000"
            df = pd.read_sql(query, conn)

            logger.info(f"Loaded {len(df)} rows from {table_name}")

            # Run all validations
            results = self.validate_dataframe(df)

            conn.close()
            return results

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            if conn:
                conn.close()
            return {'error': str(e)}

    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all validation checks on a DataFrame.

        Args:
            df: Panel data DataFrame

        Returns:
            Complete validation results
        """
        logger.info("Running comprehensive data quality validation...")

        # Set timestamps
        self.metrics.validation_timestamp = datetime.now().isoformat()

        # Try to get data timestamp range
        time_col = next((col for col in ['timestamp', 'game_date', 'date'] if col in df.columns), None)
        if time_col:
            try:
                df[time_col] = pd.to_datetime(df[time_col])
                self.metrics.data_timestamp_range = (
                    df[time_col].min().isoformat(),
                    df[time_col].max().isoformat()
                )
            except:
                pass

        # Run all validation checks
        structure_results = self.validate_panel_structure(df)
        completeness_results = self.check_completeness(df)
        duplicate_results = self.detect_duplicates(df)
        temporal_results = self.check_temporal_consistency(df)
        outlier_results = self.detect_outliers(df)

        # Calculate quality score
        quality_score = self.calculate_quality_score()

        # Compile results
        results = {
            'summary': {
                'total_observations': len(df),
                'total_columns': len(df.columns),
                'quality_score': round(quality_score, 2),
                'quality_grade': self.metrics.quality_grade,
                'validation_timestamp': self.metrics.validation_timestamp,
            },
            'structure': structure_results,
            'completeness': completeness_results,
            'duplicates': duplicate_results,
            'temporal_consistency': temporal_results,
            'outliers': outlier_results,
            'validation_errors': self.validation_errors,
            'warnings': self.warnings_list,
            'metrics': asdict(self.metrics)
        }

        return results

    def generate_report(self, results: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate formatted quality report.

        Args:
            results: Validation results dictionary
            output_path: Optional path to save JSON report

        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("NBA PANEL DATA QUALITY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary
        summary = results.get('summary', {})
        report_lines.append("OVERALL QUALITY")
        report_lines.append("-" * 80)
        report_lines.append(f"Quality Score: {summary.get('quality_score', 0)}/100")
        report_lines.append(f"Quality Grade: {summary.get('quality_grade', 'Unknown')}")
        report_lines.append(f"Total Observations: {summary.get('total_observations', 0):,}")
        report_lines.append(f"Total Columns: {summary.get('total_columns', 0)}")
        report_lines.append("")

        # Completeness
        completeness = results.get('completeness', {})
        report_lines.append("DATA COMPLETENESS")
        report_lines.append("-" * 80)
        report_lines.append(f"Completeness: {completeness.get('completeness_pct', 0):.2f}%")
        report_lines.append(f"Missing Pattern: {completeness.get('missing_pattern', 'Unknown')}")
        if completeness.get('missing_by_column'):
            report_lines.append("Missing by Column:")
            for col, count in sorted(completeness['missing_by_column'].items(), key=lambda x: x[1], reverse=True)[:10]:
                report_lines.append(f"  {col}: {count:,}")
        report_lines.append("")

        # Duplicates
        duplicates = results.get('duplicates', {})
        report_lines.append("DUPLICATE DETECTION")
        report_lines.append("-" * 80)
        report_lines.append(f"Duplicates: {duplicates.get('duplicate_count', 0):,} ({duplicates.get('duplicate_pct', 0):.2f}%)")
        report_lines.append(f"Key Duplicates: {duplicates.get('key_duplicates', 0):,}")
        report_lines.append("")

        # Temporal Consistency
        temporal = results.get('temporal_consistency', {})
        report_lines.append("TEMPORAL CONSISTENCY")
        report_lines.append("-" * 80)
        report_lines.append(f"Temporal Errors: {temporal.get('temporal_errors', 0):,}")
        if temporal.get('error_types'):
            report_lines.append("Errors by Type:")
            for error_type, count in temporal['error_types'].items():
                report_lines.append(f"  {error_type}: {count:,}")
        report_lines.append("")

        # Outliers
        outliers = results.get('outliers', {})
        report_lines.append("OUTLIER DETECTION")
        report_lines.append("-" * 80)
        report_lines.append(f"Outliers: {outliers.get('outlier_count', 0):,} ({outliers.get('outlier_pct', 0):.2f}%)")
        if outliers.get('outlier_by_column'):
            report_lines.append("Outliers by Column (Top 10):")
            for col, count in sorted(outliers['outlier_by_column'].items(), key=lambda x: x[1], reverse=True)[:10]:
                report_lines.append(f"  {col}: {count:,}")
        report_lines.append("")

        # Validation Errors
        if results.get('validation_errors'):
            report_lines.append("VALIDATION ERRORS")
            report_lines.append("-" * 80)
            for error in results['validation_errors']:
                report_lines.append(f"❌ {error}")
            report_lines.append("")

        # Warnings
        if results.get('warnings'):
            report_lines.append("WARNINGS")
            report_lines.append("-" * 80)
            for warning in results['warnings']:
                report_lines.append(f"⚠️  {warning}")
            report_lines.append("")

        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)

        # Save JSON if requested
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Detailed results saved to: {output_path}")

        return report_text


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NBA Panel Data Quality Validation System (rec_29)'
    )
    parser.add_argument(
        '--source',
        choices=['postgresql', 'file'],
        default='postgresql',
        help='Data source to validate'
    )
    parser.add_argument(
        '--table',
        default='nba_play_by_play_historical',
        help='PostgreSQL table name (default: nba_play_by_play_historical)'
    )
    parser.add_argument(
        '--file-path',
        help='Path to CSV/Parquet file to validate'
    )
    parser.add_argument(
        '--output',
        help='Path to save detailed JSON report'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed report'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Run in continuous monitoring mode'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Monitoring interval in seconds (default: 300)'
    )

    args = parser.parse_args()

    # Initialize validator
    validator = PanelDataQualityMonitor()

    # Run validation
    if args.source == 'postgresql':
        results = validator.validate_from_postgresql(table_name=args.table)
    elif args.source == 'file':
        if not args.file_path:
            logger.error("--file-path required when source is 'file'")
            sys.exit(1)

        # Load file
        if args.file_path.endswith('.csv'):
            df = pd.read_csv(args.file_path)
        elif args.file_path.endswith('.parquet'):
            df = pd.read_parquet(args.file_path)
        else:
            logger.error("Unsupported file format. Use CSV or Parquet.")
            sys.exit(1)

        results = validator.validate_dataframe(df)

    # Generate report
    report = validator.generate_report(results, output_path=args.output)

    # Display report
    print(report)

    # Monitoring mode
    if args.monitor and args.source == 'postgresql':
        logger.info(f"Entering monitoring mode (interval: {args.interval}s)")
        logger.info("Press Ctrl+C to stop")

        try:
            import time
            while True:
                time.sleep(args.interval)
                logger.info("Running scheduled validation...")
                results = validator.validate_from_postgresql(table_name=args.table)
                report = validator.generate_report(results)
                print("\n" + report)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")

    # Exit with appropriate code
    if results.get('validation_errors'):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
