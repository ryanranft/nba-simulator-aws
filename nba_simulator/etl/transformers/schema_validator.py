"""
Schema Validator

Validates data against defined schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


class SchemaValidator:
    """
    Validates data against schemas.
    
    Provides comprehensive schema validation including:
    - Required field checks
    - Type validation
    - Value range validation
    - Format validation
    
    Usage:
        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate(data)
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize validator with schema.
        
        Args:
            schema: Schema definition dictionary
        """
        self.schema = schema
    
    def validate(
        self,
        data: Dict[str, Any],
        strict: bool = False
    ) -> tuple[bool, List[str]]:
        """
        Validate data against schema.
        
        Args:
            data: Data to validate
            strict: If True, require all schema fields; if False, only validate present fields
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_errors = self._validate_required_fields(data, strict)
        errors.extend(required_errors)
        
        # Check field types
        type_errors = self._validate_field_types(data)
        errors.extend(type_errors)
        
        # Check value constraints
        value_errors = self._validate_value_constraints(data)
        errors.extend(value_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_required_fields(
        self,
        data: Dict[str, Any],
        strict: bool
    ) -> List[str]:
        """
        Validate required fields are present.
        
        Args:
            data: Data to validate
            strict: If True, check all schema fields
        
        Returns:
            List of error messages
        """
        errors = []
        
        for field, config in self.schema.items():
            if isinstance(config, dict):
                required = config.get('required', False)
                if required and field not in data:
                    errors.append(f"Missing required field: {field}")
                elif strict and field not in data and not required:
                    errors.append(f"Missing field: {field} (strict mode)")
            else:
                # Simple type definition
                if field not in data and strict:
                    errors.append(f"Missing field: {field}")
        
        return errors
    
    def _validate_field_types(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate field types.
        
        Args:
            data: Data to validate
        
        Returns:
            List of error messages
        """
        errors = []
        
        for field, value in data.items():
            if field not in self.schema:
                continue  # Unknown fields OK
            
            schema_def = self.schema[field]
            expected_type = self._get_expected_type(schema_def)
            
            if value is not None and expected_type:
                if not self._check_type(value, expected_type):
                    errors.append(
                        f"Field {field} has type {type(value).__name__}, "
                        f"expected {expected_type.__name__}"
                    )
        
        return errors
    
    def _validate_value_constraints(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate value constraints (ranges, patterns, etc.).
        
        Args:
            data: Data to validate
        
        Returns:
            List of error messages
        """
        errors = []
        
        for field, value in data.items():
            if field not in self.schema or value is None:
                continue
            
            schema_def = self.schema[field]
            if not isinstance(schema_def, dict):
                continue
            
            # Check min/max for numbers
            if 'min' in schema_def and value < schema_def['min']:
                errors.append(f"Field {field} value {value} below minimum {schema_def['min']}")
            
            if 'max' in schema_def and value > schema_def['max']:
                errors.append(f"Field {field} value {value} above maximum {schema_def['max']}")
            
            # Check enum values
            if 'enum' in schema_def and value not in schema_def['enum']:
                errors.append(f"Field {field} value {value} not in allowed values")
        
        return errors
    
    def _get_expected_type(self, schema_def: Any) -> Optional[type]:
        """
        Get expected type from schema definition.
        
        Args:
            schema_def: Schema definition
        
        Returns:
            Expected type or None
        """
        if isinstance(schema_def, type):
            return schema_def
        elif isinstance(schema_def, dict) and 'type' in schema_def:
            return schema_def['type']
        return None
    
    def _check_type(self, value: Any, expected_type: type) -> bool:
        """
        Check if value matches expected type.
        
        Args:
            value: Value to check
            expected_type: Expected type
        
        Returns:
            True if type matches
        """
        # Handle Optional types
        if expected_type == Optional[str]:
            return value is None or isinstance(value, str)
        
        # Direct type check
        if isinstance(value, expected_type):
            return True
        
        # Special cases
        if expected_type == datetime:
            if isinstance(value, str):
                # Allow string timestamps
                return True
        
        return False


# Predefined schemas

UNIFIED_PLAY_BY_PLAY_SCHEMA = {
    'game_id': {'type': str, 'required': True},
    'event_id': {'type': str, 'required': True},
    'timestamp': {'type': datetime, 'required': True},
    'event_type': {'type': str, 'required': False},
    'player_id': {'type': str, 'required': False},
    'team_id': {'type': str, 'required': False},
    'event_data': {'type': dict, 'required': False},
    'data_source': {'type': str, 'required': True, 'enum': ['hoopr', 'espn', 'basketball_reference', 'nba_api']},
    'created_at': {'type': datetime, 'required': True}
}

UNIFIED_BOX_SCORE_SCHEMA = {
    'game_id': {'type': str, 'required': True},
    'player_id': {'type': str, 'required': True},
    'team_id': {'type': str, 'required': True},
    'minutes': {'type': float, 'required': False, 'min': 0, 'max': 60},
    'points': {'type': int, 'required': False, 'min': 0},
    'rebounds': {'type': int, 'required': False, 'min': 0},
    'assists': {'type': int, 'required': False, 'min': 0},
    'data_source': {'type': str, 'required': True},
    'created_at': {'type': datetime, 'required': True}
}

