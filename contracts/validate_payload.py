#!/usr/bin/env python3
"""
WINDI Contract Validator — API Schema Validation
================================================
Sistema de contenção #1: Elimina Loop 2 (campos faltando)

Uso:
    from validate_payload import ContractValidator, validate_request

    validator = ContractValidator()
    result = validator.validate('/bridge/open', payload, lang='pt')

    if not result['valid']:
        return jsonify({'error': result['error'], 'field': result['field']}), 400

Flask Middleware:
    @app.before_request
    def validate_api_request():
        return validate_request(request)

Criado: 2026-03-19
Liga IA+H — Kempten, Bavaria
"AI processes. Human decides. WINDI guarantees."
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache

# ─────────────────────────────────────────────────────────────
# CONTRACTS DIRECTORY
# ─────────────────────────────────────────────────────────────

CONTRACTS_DIR = Path(__file__).parent
SUPPORTED_LANGUAGES = ['de', 'en', 'pt']
DEFAULT_LANGUAGE = 'en'


# ─────────────────────────────────────────────────────────────
# CONTRACT LOADER
# ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=32)
def load_contract(contract_name: str) -> Dict:
    """Load a contract JSON file (cached)."""
    path = CONTRACTS_DIR / f"{contract_name}.json"
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_contracts() -> Dict[str, Dict]:
    """Load all contract files."""
    contracts = {}
    for path in CONTRACTS_DIR.glob("*.json"):
        name = path.stem
        contracts[name] = load_contract(name)
    return contracts


# ─────────────────────────────────────────────────────────────
# VALIDATION RESULT
# ─────────────────────────────────────────────────────────────

class ValidationResult:
    """Result of a validation check."""

    def __init__(self, valid: bool, error: str = None, field: str = None,
                 i9_warning: str = None, payload: Dict = None):
        self.valid = valid
        self.error = error
        self.field = field
        self.i9_warning = i9_warning
        self.payload = payload or {}

    def to_dict(self) -> Dict:
        return {
            'valid': self.valid,
            'error': self.error,
            'field': self.field,
            'i9_warning': self.i9_warning,
            'payload': self.payload
        }


# ─────────────────────────────────────────────────────────────
# FIELD VALIDATORS
# ─────────────────────────────────────────────────────────────

def validate_string(value: Any, schema: Dict, lang: str) -> Tuple[bool, str]:
    """Validate a string field."""
    if not isinstance(value, str):
        return False, f"expected string, got {type(value).__name__}"

    min_len = schema.get('min_length', 0)
    max_len = schema.get('max_length', float('inf'))

    if len(value) < min_len:
        return False, f"minimum length is {min_len}"
    if len(value) > max_len:
        return False, f"maximum length is {max_len}"

    pattern = schema.get('pattern')
    if pattern and not re.match(pattern, value):
        return False, schema.get(f'error_{lang}', f"must match pattern {pattern}")

    enum = schema.get('enum')
    if enum and value not in enum:
        return False, f"must be one of: {', '.join(enum)}"

    return True, None


def validate_array(value: Any, schema: Dict, lang: str) -> Tuple[bool, str]:
    """Validate an array field."""
    if not isinstance(value, list):
        return False, f"expected array, got {type(value).__name__}"

    max_items = schema.get('max_items')
    if max_items and len(value) > max_items:
        return False, f"maximum {max_items} items allowed"

    return True, None


def validate_boolean(value: Any, schema: Dict, lang: str) -> Tuple[bool, str]:
    """Validate a boolean field."""
    if not isinstance(value, bool):
        return False, f"expected boolean, got {type(value).__name__}"
    return True, None


def validate_object(value: Any, schema: Dict, lang: str) -> Tuple[bool, str]:
    """Validate an object field."""
    if not isinstance(value, dict):
        return False, f"expected object, got {type(value).__name__}"
    return True, None


def validate_number(value: Any, schema: Dict, lang: str) -> Tuple[bool, str]:
    """Validate a number field."""
    if not isinstance(value, (int, float)):
        return False, f"expected number, got {type(value).__name__}"

    minimum = schema.get('minimum')
    maximum = schema.get('maximum')

    if minimum is not None and value < minimum:
        return False, f"minimum value is {minimum}"
    if maximum is not None and value > maximum:
        return False, f"maximum value is {maximum}"

    return True, None


VALIDATORS = {
    'string': validate_string,
    'array': validate_array,
    'boolean': validate_boolean,
    'object': validate_object,
    'number': validate_number,
    'integer': validate_number,
}


# ─────────────────────────────────────────────────────────────
# CONTRACT VALIDATOR
# ─────────────────────────────────────────────────────────────

class ContractValidator:
    """
    Main validator class.

    Usage:
        validator = ContractValidator()
        result = validator.validate('/bridge/open', {'title': 'Test'}, lang='pt')
    """

    def __init__(self, contracts_dir: Path = None):
        self.contracts_dir = contracts_dir or CONTRACTS_DIR
        self._endpoint_map = {}
        self._build_endpoint_map()

    def _build_endpoint_map(self):
        """Build a map of endpoint paths to their contracts."""
        contracts = get_all_contracts()
        for contract_name, contract in contracts.items():
            endpoints = contract.get('endpoints', {})
            for path, schema in endpoints.items():
                self._endpoint_map[path] = schema

    def get_schema(self, endpoint: str) -> Optional[Dict]:
        """Get the schema for an endpoint."""
        # Exact match first
        if endpoint in self._endpoint_map:
            return self._endpoint_map[endpoint]

        # Try without trailing slash
        if endpoint.endswith('/'):
            clean = endpoint.rstrip('/')
            if clean in self._endpoint_map:
                return self._endpoint_map[clean]

        # Try with trailing slash
        if not endpoint.endswith('/'):
            with_slash = endpoint + '/'
            if with_slash in self._endpoint_map:
                return self._endpoint_map[with_slash]

        return None

    def validate(self, endpoint: str, payload: Dict, lang: str = 'en') -> ValidationResult:
        """
        Validate a payload against the contract for an endpoint.

        Args:
            endpoint: The API endpoint path (e.g., '/bridge/open')
            payload: The request payload to validate
            lang: Language for error messages ('de', 'en', 'pt')

        Returns:
            ValidationResult with valid=True/False and error details
        """
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE

        schema = self.get_schema(endpoint)
        if not schema:
            # No contract = no validation (passthrough)
            return ValidationResult(valid=True, payload=payload)

        # Check required fields
        required = schema.get('required', [])
        fields = schema.get('fields', {})

        validated_payload = {}

        for field_name in required:
            if field_name not in payload or payload[field_name] is None:
                field_schema = fields.get(field_name, {})
                error_msg = field_schema.get(f'error_{lang}', f"'{field_name}' is required")
                return ValidationResult(
                    valid=False,
                    error=error_msg,
                    field=field_name
                )

        # Validate and collect all fields
        for field_name, field_schema in fields.items():
            field_type = field_schema.get('type', 'string')
            default = field_schema.get('default')

            if field_name in payload:
                value = payload[field_name]

                # Type validation
                validator = VALIDATORS.get(field_type)
                if validator:
                    is_valid, error = validator(value, field_schema, lang)
                    if not is_valid:
                        custom_error = field_schema.get(f'error_{lang}')
                        return ValidationResult(
                            valid=False,
                            error=custom_error or f"'{field_name}': {error}",
                            field=field_name
                        )

                validated_payload[field_name] = value
            elif default is not None:
                validated_payload[field_name] = default

        # Passthrough any extra fields not in schema
        for key, value in payload.items():
            if key not in validated_payload:
                validated_payload[key] = value

        # Check for I9 gate warning
        i9_warning = None
        if schema.get('i9_gate'):
            human_approved = validated_payload.get('human_approved', False)
            if human_approved:
                # Find the I9 warning message
                for field_name, field_schema in fields.items():
                    warning_key = f'i9_warning_{lang}'
                    if warning_key in field_schema:
                        i9_warning = field_schema[warning_key]
                        break

        return ValidationResult(
            valid=True,
            payload=validated_payload,
            i9_warning=i9_warning
        )


# ─────────────────────────────────────────────────────────────
# FLASK MIDDLEWARE
# ─────────────────────────────────────────────────────────────

_validator = None

def get_validator() -> ContractValidator:
    """Get the singleton validator instance."""
    global _validator
    if _validator is None:
        _validator = ContractValidator()
    return _validator


def validate_request(request) -> Optional[Tuple[Dict, int]]:
    """
    Flask middleware function to validate incoming requests.

    Usage in Flask app:
        @app.before_request
        def validate_api_request():
            error_response = validate_request(request)
            if error_response:
                return error_response

    Returns:
        None if valid, or (error_dict, status_code) if invalid
    """
    # Only validate POST/PUT/PATCH with JSON body
    if request.method not in ('POST', 'PUT', 'PATCH'):
        return None

    if not request.is_json:
        return None

    # Get endpoint path
    endpoint = request.path

    # Get validator and schema
    validator = get_validator()
    schema = validator.get_schema(endpoint)

    if not schema:
        return None  # No contract = passthrough

    # Get payload
    payload = request.get_json(silent=True) or {}

    # Detect language from payload, header, or default
    lang = payload.get('language') or request.headers.get('Accept-Language', 'en')[:2]
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    # Validate
    result = validator.validate(endpoint, payload, lang)

    if not result.valid:
        return {
            'status': 'error',
            'error': result.error,
            'field': result.field,
            'endpoint': endpoint,
            'hint': 'Check API contract at /contracts/' + endpoint.split('/')[1] + '.json'
        }, 400

    # Store validated payload for later use
    request.validated_payload = result.payload
    request.i9_warning = result.i9_warning

    return None


# ─────────────────────────────────────────────────────────────
# DECORATOR FOR ROUTES
# ─────────────────────────────────────────────────────────────

def requires_contract(endpoint: str = None):
    """
    Decorator to enforce contract validation on a route.

    Usage:
        @app.route('/bridge/open', methods=['POST'])
        @requires_contract('/bridge/open')
        def bridge_open():
            # request.validated_payload contains the validated data
            data = request.validated_payload
            ...
    """
    def decorator(f):
        from functools import wraps

        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify

            # Use provided endpoint or infer from request
            path = endpoint or request.path

            payload = request.get_json(silent=True) or {}
            lang = payload.get('language', 'en')

            validator = get_validator()
            result = validator.validate(path, payload, lang)

            if not result.valid:
                return jsonify({
                    'status': 'error',
                    'error': result.error,
                    'field': result.field
                }), 400

            request.validated_payload = result.payload
            request.i9_warning = result.i9_warning

            return f(*args, **kwargs)

        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────
# CLI FOR TESTING
# ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    print("WINDI Contract Validator — Test Mode")
    print("=" * 50)

    validator = ContractValidator()

    # List all registered endpoints
    print("\nRegistered Endpoints:")
    for path in sorted(validator._endpoint_map.keys()):
        schema = validator._endpoint_map[path]
        required = schema.get('required', [])
        print(f"  {path}")
        print(f"    Required: {required}")

    # Test cases
    print("\n" + "=" * 50)
    print("Test Cases:")

    # Test 1: Missing required field
    result = validator.validate('/bridge/open', {}, lang='pt')
    print(f"\n1. /bridge/open with empty payload:")
    print(f"   Valid: {result.valid}")
    print(f"   Error: {result.error}")

    # Test 2: Valid payload
    result = validator.validate('/bridge/open', {'title': 'Test Document'}, lang='pt')
    print(f"\n2. /bridge/open with valid title:")
    print(f"   Valid: {result.valid}")
    print(f"   Payload: {result.payload}")

    # Test 3: Invalid wallet_id format
    result = validator.validate('/bridge/open', {
        'title': 'Test',
        'wallet_id': 'invalid-format'
    }, lang='pt')
    print(f"\n3. /bridge/open with invalid wallet_id:")
    print(f"   Valid: {result.valid}")
    print(f"   Error: {result.error}")

    # Test 4: Missing draft_id for seal
    result = validator.validate('/api/onetouch/seal', {}, lang='en')
    print(f"\n4. /api/onetouch/seal without draft_id:")
    print(f"   Valid: {result.valid}")
    print(f"   Error: {result.error}")

    print("\n" + "=" * 50)
    print("Validator ready for integration.")
