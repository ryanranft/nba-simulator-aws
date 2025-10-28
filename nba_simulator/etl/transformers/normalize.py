"""
Data Normalizer

Normalizes data from different sources into unified format.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from .base import BaseTransformer


class DataNormalizer(BaseTransformer):
    """
    Normalizes data from different sources into unified format.

    Handles:
    - Field name standardization
    - Data type conversion
    - ID mapping
    - Timestamp standardization

    Usage:
        normalizer = DataNormalizer(source="hoopr")
        unified_data = normalizer.transform(raw_data)
    """

    # Unified schema field names
    UNIFIED_FIELDS = {
        'game_id': str,
        'event_id': str,
        'timestamp': datetime,
        'event_type': str,
        'player_id': Optional[str],
        'team_id': Optional[str],
        'event_data': dict,
        'data_source': str,
        'created_at': datetime
    }

    def __init__(self, source: str):
        """
        Initialize normalizer for specific data source.

        Args:
            source: Data source (hoopr, espn, basketball_reference, nba_api)
        """
        super().__init__(f"{source}_normalizer", source)
        self.field_mappings = self._get_field_mappings()

    def transform(self, data: Any) -> Dict[str, Any]:
        """
        Transform data to unified format.

        Args:
            data: Raw data from extractor

        Returns:
            Normalized data in unified format
        """
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data)}")

        unified = {}

        # Map fields using source-specific mappings
        for unified_field, source_field in self.field_mappings.items():
            if source_field in data:
                unified[unified_field] = self._convert_field(
                    unified_field,
                    data[source_field]
                )

        # Add metadata
        unified['data_source'] = self.source
        unified['created_at'] = datetime.utcnow()

        # Store original data for reference
        unified['event_data'] = unified.get('event_data', {})
        unified['event_data']['_original'] = data

        return unified

    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validate data against unified schema.

        Args:
            data: Transformed data

        Returns:
            True if valid
        """
        # Check required fields present
        required = ['game_id', 'event_id', 'timestamp', 'data_source']
        for field in required:
            if field not in data or data[field] is None:
                self.logger.warning(f"Missing required field: {field}")
                return False

        # Check field types
        for field, expected_type in self.UNIFIED_FIELDS.items():
            if field in data and data[field] is not None:
                if expected_type == Optional[str]:
                    expected_type = str

                if expected_type != type(data[field]):
                    # Allow some flexibility
                    if expected_type == datetime and isinstance(data[field], str):
                        continue  # String timestamps OK
                    self.logger.warning(
                        f"Field {field} has type {type(data[field])}, "
                        f"expected {expected_type}"
                    )

        return True

    def _get_field_mappings(self) -> Dict[str, str]:
        """
        Get field mappings for this data source.

        Maps unified field names to source-specific field names.

        Returns:
            Dictionary mapping unified fields to source fields
        """
        # Source-specific field mappings
        mappings = {
            'hoopr': {
                'game_id': 'game_id',
                'event_id': 'id',
                'timestamp': 'wallclock',
                'event_type': 'type_text',
                'player_id': 'athlete_id_1',
                'team_id': 'team_id',
                'event_data': 'text'
            },
            'espn': {
                'game_id': 'game_id',
                'event_id': 'eventId',
                'timestamp': 'clock',
                'event_type': 'type',
                'player_id': 'playerId',
                'team_id': 'teamId',
                'event_data': 'description'
            },
            'basketball_reference': {
                'game_id': 'game_id',
                'event_id': 'event_id',
                'timestamp': 'time',
                'event_type': 'play_type',
                'player_id': 'player',
                'team_id': 'team'
            },
            'nba_api': {
                'game_id': 'GAME_ID',
                'event_id': 'EVENTNUM',
                'timestamp': 'PCTIMESTRING',
                'event_type': 'EVENTMSGTYPE',
                'player_id': 'PLAYER1_ID',
                'team_id': 'PLAYER1_TEAM_ID'
            }
        }

        return mappings.get(self.source, {})

    def _convert_field(self, field_name: str, value: Any) -> Any:
        """
        Convert field value to appropriate type.

        Args:
            field_name: Unified field name
            value: Raw value from source

        Returns:
            Converted value
        """
        if value is None:
            return None

        expected_type = self.UNIFIED_FIELDS.get(field_name)

        # Handle timestamps
        if expected_type == datetime:
            if isinstance(value, datetime):
                return value
            elif isinstance(value, str):
                # Try to parse common timestamp formats
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                # If parsing fails, return as-is (will be caught in validation)
                return value

        # Handle dictionaries (event_data)
        if expected_type == dict and not isinstance(value, dict):
            return {'value': value}

        # Convert to expected type
        if expected_type and expected_type != Optional[str]:
            try:
                if expected_type == str:
                    return str(value)
                elif expected_type == dict:
                    if isinstance(value, str):
                        return {'text': value}
                    return value
            except Exception as e:
                self.logger.warning(f"Could not convert {field_name}: {e}")

        return value

    def _get_required_fields(self) -> list:
        """Get list of required fields"""
        return ['game_id', 'event_id', 'timestamp', 'data_source']

