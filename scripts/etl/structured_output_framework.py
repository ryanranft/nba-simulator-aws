#!/usr/bin/env python3
"""
Structured Output Framework - rec_64

Comprehensive data extraction and validation framework implementing
recommendation rec_64 from the Master Implementation Sequence.

Features:
1. Schema-based data extraction from unstructured sources
2. Multi-format output (JSON, CSV, Parquet)
3. Automatic schema validation and type coercion
4. Error handling and data quality checks
5. Incremental extraction with checkpointing
6. Transformation pipelines

Implementation: Master Implementation Sequence #12
Phase: 0 (Data Collection)
Dependencies: rec_22 (panel data structure)
"""

import os
import sys
import logging
import json
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataType(Enum):
    """Supported data types for schema validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"


class OutputFormat(Enum):
    """Supported output formats."""
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    PANDAS = "pandas"


@dataclass
class FieldSchema:
    """
    Schema definition for a single field.

    Attributes:
        name: Field name
        data_type: Expected data type
        required: Whether field is required
        default: Default value if missing
        validator: Custom validation function
        transformer: Custom transformation function
    """
    name: str
    data_type: DataType
    required: bool = True
    default: Any = None
    validator: Optional[Callable] = None
    transformer: Optional[Callable] = None
    description: str = ""

    def validate(self, value: Any) -> bool:
        """Validate value against schema."""
        # Check if required
        if self.required and value is None:
            return False

        # Allow None for optional fields
        if not self.required and value is None:
            return True

        # Type-specific validation
        try:
            if self.data_type == DataType.STRING:
                return isinstance(value, str)
            elif self.data_type == DataType.INTEGER:
                return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
            elif self.data_type == DataType.FLOAT:
                return isinstance(value, (int, float))
            elif self.data_type == DataType.BOOLEAN:
                return isinstance(value, bool)
            elif self.data_type == DataType.DATETIME:
                return isinstance(value, (datetime, str))
            elif self.data_type == DataType.ARRAY:
                return isinstance(value, (list, tuple))
            elif self.data_type == DataType.OBJECT:
                return isinstance(value, dict)
        except Exception:
            return False

        # Custom validation if provided
        if self.validator:
            return self.validator(value)

        return True

    def coerce(self, value: Any) -> Any:
        """Coerce value to correct type."""
        if value is None:
            return self.default

        try:
            if self.data_type == DataType.STRING:
                return str(value)
            elif self.data_type == DataType.INTEGER:
                return int(float(value))  # Handle "42.0" -> 42
            elif self.data_type == DataType.FLOAT:
                return float(value)
            elif self.data_type == DataType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'y')
                return bool(value)
            elif self.data_type == DataType.DATETIME:
                if isinstance(value, str):
                    return pd.to_datetime(value)
                return value
            elif self.data_type == DataType.ARRAY:
                if isinstance(value, str):
                    return json.loads(value) if value.startswith('[') else [value]
                return list(value)
            elif self.data_type == DataType.OBJECT:
                if isinstance(value, str):
                    return json.loads(value)
                return dict(value)
        except Exception as e:
            logger.warning(f"Coercion failed for {self.name}: {e}")
            return self.default

        return value

    def transform(self, value: Any) -> Any:
        """Apply custom transformation if provided."""
        if self.transformer:
            return self.transformer(value)
        return value


@dataclass
class DataSchema:
    """
    Complete schema definition for structured data.

    Attributes:
        name: Schema name
        version: Schema version
        fields: List of field schemas
        strict: Whether to reject unknown fields
    """
    name: str
    version: str
    fields: List[FieldSchema]
    strict: bool = False

    def validate_record(self, record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a record against schema.

        Returns:
            (is_valid, list of error messages)
        """
        errors = []

        # Check for required fields
        for field in self.fields:
            if field.required and field.name not in record:
                errors.append(f"Missing required field: {field.name}")

        # Validate each field
        for field_name, value in record.items():
            field_schema = self.get_field(field_name)

            if field_schema is None:
                if self.strict:
                    errors.append(f"Unknown field: {field_name}")
                continue

            if not field_schema.validate(value):
                errors.append(
                    f"Invalid value for {field_name}: {value} "
                    f"(expected {field_schema.data_type.value})"
                )

        return len(errors) == 0, errors

    def coerce_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coerce record values to match schema types.

        Returns:
            Coerced record with proper types
        """
        coerced = {}

        for field in self.fields:
            value = record.get(field.name)

            # Coerce to correct type
            coerced_value = field.coerce(value)

            # Apply transformation
            coerced_value = field.transform(coerced_value)

            coerced[field.name] = coerced_value

        # Include extra fields if not strict
        if not self.strict:
            for key, value in record.items():
                if key not in coerced:
                    coerced[key] = value

        return coerced

    def get_field(self, name: str) -> Optional[FieldSchema]:
        """Get field schema by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'strict': self.strict,
            'fields': [
                {
                    'name': f.name,
                    'type': f.data_type.value,
                    'required': f.required,
                    'default': f.default,
                    'description': f.description
                }
                for f in self.fields
            ]
        }


class StructuredOutputFramework:
    """
    Framework for extracting and validating structured data.

    Provides tools for:
    - Schema definition and validation
    - Data extraction from various sources
    - Type coercion and transformation
    - Error handling and reporting
    - Multi-format output
    """

    def __init__(
        self,
        schema: Optional[DataSchema] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Structured Output Framework.

        Args:
            schema: Data schema for validation
            config: Configuration options
        """
        self.schema = schema
        self.config = config or {}
        self.extraction_stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'errors': []
        }

        # Default configuration
        self.default_config = {
            'strict_validation': False,
            'coerce_types': True,
            'skip_invalid': False,
            'max_errors': 100,
            'checkpoint_interval': 1000
        }

        # Merge with provided config
        self.config = {**self.default_config, **self.config}

        logger.info("Initialized Structured Output Framework")

    def extract_records(
        self,
        source_data: Union[List[Dict], pd.DataFrame, str],
        validate: bool = True,
        coerce: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract and validate records from source data.

        Args:
            source_data: Source data (list of dicts, DataFrame, or JSON string)
            validate: Whether to validate against schema
            coerce: Whether to coerce types

        Returns:
            List of validated/coerced records
        """
        logger.info("Extracting records from source")

        # Convert source to list of dicts
        if isinstance(source_data, pd.DataFrame):
            records = source_data.to_dict('records')
        elif isinstance(source_data, str):
            records = json.loads(source_data)
        else:
            records = source_data

        if not isinstance(records, list):
            records = [records]

        extracted = []
        self.extraction_stats['total_records'] = len(records)

        for i, record in enumerate(records):
            try:
                processed_record = record.copy()

                # Coerce types if enabled
                if coerce and self.schema:
                    processed_record = self.schema.coerce_record(processed_record)

                # Validate if enabled
                if validate and self.schema:
                    is_valid, errors = self.schema.validate_record(processed_record)

                    if not is_valid:
                        self.extraction_stats['invalid_records'] += 1
                        self.extraction_stats['errors'].extend([
                            f"Record {i}: {error}" for error in errors
                        ])

                        if self.config['skip_invalid']:
                            continue
                        elif len(self.extraction_stats['errors']) > self.config['max_errors']:
                            logger.error("Max errors exceeded")
                            break

                extracted.append(processed_record)
                self.extraction_stats['valid_records'] += 1

                # Checkpoint
                if (i + 1) % self.config['checkpoint_interval'] == 0:
                    logger.info(f"Processed {i + 1} records")

            except Exception as e:
                logger.error(f"Error processing record {i}: {e}")
                self.extraction_stats['invalid_records'] += 1
                self.extraction_stats['errors'].append(f"Record {i}: {str(e)}")

        logger.info(
            f"Extraction complete: {self.extraction_stats['valid_records']}/{self.extraction_stats['total_records']} valid"
        )

        return extracted

    def export_to_json(
        self,
        records: List[Dict],
        output_path: str,
        indent: int = 2
    ) -> None:
        """Export records to JSON file."""
        logger.info(f"Exporting {len(records)} records to JSON: {output_path}")

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(records, f, indent=indent, default=str)

        logger.info(f"Exported to {output_path}")

    def export_to_csv(
        self,
        records: List[Dict],
        output_path: str,
        index: bool = False
    ) -> None:
        """Export records to CSV file."""
        logger.info(f"Exporting {len(records)} records to CSV: {output_path}")

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        df = pd.DataFrame(records)
        df.to_csv(output_path, index=index)

        logger.info(f"Exported to {output_path}")

    def export_to_parquet(
        self,
        records: List[Dict],
        output_path: str,
        compression: str = 'snappy'
    ) -> None:
        """Export records to Parquet file."""
        logger.info(f"Exporting {len(records)} records to Parquet: {output_path}")

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        df = pd.DataFrame(records)
        df.to_parquet(output_path, compression=compression, index=False)

        logger.info(f"Exported to {output_path}")

    def export(
        self,
        records: List[Dict],
        output_path: str,
        format: OutputFormat = OutputFormat.JSON
    ) -> None:
        """
        Export records to file in specified format.

        Args:
            records: Records to export
            output_path: Output file path
            format: Output format (JSON, CSV, or Parquet)
        """
        if format == OutputFormat.JSON:
            self.export_to_json(records, output_path)
        elif format == OutputFormat.CSV:
            self.export_to_csv(records, output_path)
        elif format == OutputFormat.PARQUET:
            self.export_to_parquet(records, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return {
            'total_records': self.extraction_stats['total_records'],
            'valid_records': self.extraction_stats['valid_records'],
            'invalid_records': self.extraction_stats['invalid_records'],
            'success_rate': (
                self.extraction_stats['valid_records'] / self.extraction_stats['total_records']
                if self.extraction_stats['total_records'] > 0 else 0
            ),
            'error_count': len(self.extraction_stats['errors']),
            'errors': self.extraction_stats['errors'][:10]  # First 10 errors
        }

    def generate_report(
        self,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate extraction report.

        Args:
            output_path: Path to save report (optional)

        Returns:
            Report dictionary
        """
        report = {
            'schema': self.schema.to_dict() if self.schema else None,
            'statistics': self.get_stats(),
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Report saved to {output_path}")

        return report


# Predefined schemas for NBA data
def create_player_game_schema() -> DataSchema:
    """Create schema for player game statistics."""
    return DataSchema(
        name="player_game_stats",
        version="1.0",
        fields=[
            FieldSchema("player_id", DataType.INTEGER, required=True),
            FieldSchema("player_name", DataType.STRING, required=True),
            FieldSchema("game_id", DataType.STRING, required=True),
            FieldSchema("game_date", DataType.DATETIME, required=True),
            FieldSchema("team", DataType.STRING, required=True),
            FieldSchema("opponent", DataType.STRING, required=True),
            FieldSchema("points", DataType.INTEGER, default=0),
            FieldSchema("rebounds", DataType.INTEGER, default=0),
            FieldSchema("assists", DataType.INTEGER, default=0),
            FieldSchema("steals", DataType.INTEGER, default=0),
            FieldSchema("blocks", DataType.INTEGER, default=0),
            FieldSchema("turnovers", DataType.INTEGER, default=0),
            FieldSchema("minutes", DataType.FLOAT, default=0.0),
            FieldSchema("fg_made", DataType.INTEGER, default=0),
            FieldSchema("fg_attempted", DataType.INTEGER, default=0),
            FieldSchema("fg3_made", DataType.INTEGER, default=0),
            FieldSchema("fg3_attempted", DataType.INTEGER, default=0),
            FieldSchema("ft_made", DataType.INTEGER, default=0),
            FieldSchema("ft_attempted", DataType.INTEGER, default=0)
        ],
        strict=False
    )


def demo_structured_output():
    """Demonstrate structured output framework with NBA data."""
    logger.info("="*80)
    logger.info("Structured Output Framework - Demo")
    logger.info("="*80)

    # 1. Create schema
    logger.info("\n1. Creating schema for player game stats")
    schema = create_player_game_schema()
    logger.info(f"Schema '{schema.name}' v{schema.version} created with {len(schema.fields)} fields")

    # 2. Generate sample data (some valid, some invalid)
    logger.info("\n2. Generating sample data")
    sample_data = [
        {
            "player_id": 2544,
            "player_name": "LeBron James",
            "game_id": "20240101LAL",
            "game_date": "2024-01-01",
            "team": "LAL",
            "opponent": "BOS",
            "points": 28,
            "rebounds": 7,
            "assists": 11,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
            "minutes": 36.5,
            "fg_made": 10,
            "fg_attempted": 18,
            "fg3_made": 2,
            "fg3_attempted": 6,
            "ft_made": 6,
            "ft_attempted": 8
        },
        {
            "player_id": "invalid",  # Invalid type
            "player_name": "Stephen Curry",
            "game_id": "20240102GSW",
            "game_date": "2024-01-02",
            "team": "GSW",
            "opponent": "LAL",
            "points": 32,
            "rebounds": 5,
            "assists": 8
        },
        {
            # Missing required fields
            "player_name": "Kevin Durant",
            "game_date": "2024-01-03",
            "points": 30
        },
        {
            "player_id": 201935,
            "player_name": "James Harden",
            "game_id": "20240103LAC",
            "game_date": "2024-01-03",
            "team": "LAC",
            "opponent": "DEN",
            "points": "25",  # String instead of int (will be coerced)
            "rebounds": "6",
            "assists": "10",
            "minutes": "38.2"
        }
    ]

    logger.info(f"Generated {len(sample_data)} sample records")

    # 3. Initialize framework
    logger.info("\n3. Initializing Structured Output Framework")
    framework = StructuredOutputFramework(
        schema=schema,
        config={
            'coerce_types': True,
            'skip_invalid': False,
            'max_errors': 100
        }
    )

    # 4. Extract and validate records
    logger.info("\n4. Extracting and validating records")
    extracted_records = framework.extract_records(
        sample_data,
        validate=True,
        coerce=True
    )

    logger.info(f"Extracted {len(extracted_records)} valid records")

    # 5. Export to multiple formats
    logger.info("\n5. Exporting to multiple formats")

    output_dir = "/tmp/structured_output"
    os.makedirs(output_dir, exist_ok=True)

    # JSON
    framework.export_to_json(
        extracted_records,
        f"{output_dir}/player_stats.json"
    )

    # CSV
    framework.export_to_csv(
        extracted_records,
        f"{output_dir}/player_stats.csv"
    )

    # Parquet
    framework.export_to_parquet(
        extracted_records,
        f"{output_dir}/player_stats.parquet"
    )

    # 6. Generate report
    logger.info("\n6. Generating extraction report")
    report = framework.generate_report(
        output_path=f"{output_dir}/extraction_report.json"
    )

    logger.info("\nExtraction Statistics:")
    stats = report['statistics']
    logger.info(f"  Total records: {stats['total_records']}")
    logger.info(f"  Valid records: {stats['valid_records']}")
    logger.info(f"  Invalid records: {stats['invalid_records']}")
    logger.info(f"  Success rate: {stats['success_rate']:.1%}")

    if stats['errors']:
        logger.info(f"\nFirst {min(3, len(stats['errors']))} errors:")
        for error in stats['errors'][:3]:
            logger.info(f"  - {error}")

    logger.info("\n" + "="*80)
    logger.info("✅ Structured Output Framework demo complete!")
    logger.info("="*80)


if __name__ == '__main__':
    demo_structured_output()
