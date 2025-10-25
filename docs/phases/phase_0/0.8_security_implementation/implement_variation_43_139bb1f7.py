#!/usr/bin/env python3
"""
Implementation Script: JWT Authentication and Access Control for NBA API

Recommendation ID: variation_43_139bb1f7
Priority: SECURITY
Source Book: Book 38 (Security Best Practices)
Generated: 2025-10-15T23:49:50.315538
Enhanced: 2025-10-23 (Full Implementation)

Description:
Implements JWT-based authentication and role-based access control (RBAC) for
NBA simulator API endpoints. Provides secure token generation, validation, and
refresh mechanisms with support for:
- User authentication with hashed passwords
- Role-based access control (Admin, Analyst, Viewer)
- Token expiration and refresh
- API endpoint protection
- Audit logging of authentication events

Ensures secure access to sensitive NBA data including player statistics,
betting odds, and proprietary analytics models.

Expected Impact: HIGH (API security, access control, compliance)
Time Estimate: 23 hours
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import hashlib
import secrets
import base64
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import PyJWT (optional for testing without dependencies)
try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    logger.warning("PyJWT not available - running in mock mode")
    JWT_AVAILABLE = False


class UserRole(Enum):
    """User roles for role-based access control."""

    ADMIN = "admin"  # Full access to all endpoints
    ANALYST = "analyst"  # Access to analytics and read operations
    VIEWER = "viewer"  # Read-only access


class SecurityImplementationVariation43:
    """
    JWT Authentication and Access Control for NBA API.

    Implements secure token-based authentication with role-based access control.
    Supports user management, token generation/validation, and audit logging.
    """

    # Default token expiration times
    DEFAULT_ACCESS_TOKEN_EXPIRY = 3600  # 1 hour
    DEFAULT_REFRESH_TOKEN_EXPIRY = 604800  # 7 days

    # API endpoints and required roles
    ENDPOINT_PERMISSIONS = {
        "/api/players": [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN],
        "/api/games": [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN],
        "/api/stats": [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN],
        "/api/analytics": [UserRole.ANALYST, UserRole.ADMIN],
        "/api/betting": [UserRole.ANALYST, UserRole.ADMIN],
        "/api/models": [UserRole.ANALYST, UserRole.ADMIN],
        "/api/admin": [UserRole.ADMIN],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NBA API Authentication System.

        Args:
            config: Configuration dictionary with keys:
                - jwt_secret: Secret key for JWT encoding (auto-generated if not provided)
                - jwt_algorithm: Algorithm for JWT (default: HS256)
                - access_token_expiry: Access token lifetime in seconds
                - refresh_token_expiry: Refresh token lifetime in seconds
                - mock_mode: Run without JWT library (for testing)
        """
        self.config = config or {}
        self.setup_complete = False
        self.mock_mode = self.config.get("mock_mode", not JWT_AVAILABLE)

        # JWT configuration
        self.jwt_secret = self.config.get("jwt_secret", secrets.token_urlsafe(32))
        self.jwt_algorithm = self.config.get("jwt_algorithm", "HS256")
        self.access_token_expiry = self.config.get(
            "access_token_expiry", self.DEFAULT_ACCESS_TOKEN_EXPIRY
        )
        self.refresh_token_expiry = self.config.get(
            "refresh_token_expiry", self.DEFAULT_REFRESH_TOKEN_EXPIRY
        )

        # User database (in-memory for this implementation)
        # In production: Replace with database queries
        self.users: Dict[str, Dict[str, Any]] = {}

        # Active tokens (for revocation tracking)
        self.active_tokens: Dict[str, Dict[str, Any]] = {}

        # Authentication audit log
        self.auth_log: List[Dict[str, Any]] = []

        logger.info("Initializing NBA API Authentication System...")
        if self.mock_mode:
            logger.warning("Running in MOCK MODE - no actual JWT encoding")

    def setup(self) -> bool:
        """
        Set up authentication system with demo users.

        Returns:
            bool: True if setup successful
        """
        try:
            logger.info("Setting up NBA API Authentication System...")

            # Create demo users for testing
            self._create_demo_users()

            self.setup_complete = True
            logger.info("✅ Setup complete")
            logger.info(f"   Created {len(self.users)} demo users")
            logger.info(f"   JWT algorithm: {self.jwt_algorithm}")
            logger.info(f"   Access token expiry: {self.access_token_expiry}s")
            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    def _create_demo_users(self):
        """Create demo users for testing."""
        demo_users = [
            {
                "username": "admin_user",
                "password": "admin_password_123",
                "role": UserRole.ADMIN,
                "email": "admin@nba-simulator.local",
            },
            {
                "username": "analyst_user",
                "password": "analyst_password_123",
                "role": UserRole.ANALYST,
                "email": "analyst@nba-simulator.local",
            },
            {
                "username": "viewer_user",
                "password": "viewer_password_123",
                "role": UserRole.VIEWER,
                "email": "viewer@nba-simulator.local",
            },
        ]

        for user_data in demo_users:
            self.create_user(
                username=user_data["username"],
                password=user_data["password"],
                role=user_data["role"],
                email=user_data["email"],
            )

    def validate_prerequisites(self) -> bool:
        """
        Validate that all prerequisites are met.

        Returns:
            bool: True if all prerequisites met
        """
        logger.info("Validating prerequisites...")

        # Check JWT secret is set
        if not self.jwt_secret:
            logger.error("JWT secret is not configured")
            return False

        # Check JWT library availability (if not in mock mode)
        if not self.mock_mode and not JWT_AVAILABLE:
            logger.error("PyJWT library not available and mock_mode=False")
            return False

        # Verify endpoint permissions are defined
        if not self.ENDPOINT_PERMISSIONS:
            logger.error("No endpoint permissions defined")
            return False

        logger.info("✅ Prerequisites validated")
        return True

    def execute(self) -> Dict[str, Any]:
        """
        Execute authentication system demonstration.

        Tests authentication workflows including:
        - User authentication
        - Token generation
        - Token validation
        - Access control checks
        - Token refresh

        Returns:
            dict: Execution results and metrics
        """
        if not self.setup_complete:
            raise RuntimeError("Setup must be completed before execution")

        logger.info("Executing NBA API Authentication System...")
        start_time = datetime.now()

        try:
            results = {
                "success": True,
                "mock_mode": self.mock_mode,
                "users_created": len(self.users),
                "authentication_tests": {},
                "access_control_tests": {},
                "token_operations": {},
            }

            # Test 1: Authenticate each demo user
            logger.info("Testing user authentication...")
            for username in ["admin_user", "analyst_user", "viewer_user"]:
                password = f"{username.split('_')[0]}_password_123"
                tokens = self.authenticate(username, password)
                if tokens:
                    results["authentication_tests"][username] = "success"
                    logger.info(f"  ✅ {username} authenticated successfully")
                else:
                    results["authentication_tests"][username] = "failed"

            # Test 2: Test access control for different roles
            logger.info("Testing access control...")
            test_cases = [
                ("admin_user", "/api/admin", True),
                ("analyst_user", "/api/analytics", True),
                ("analyst_user", "/api/admin", False),
                ("viewer_user", "/api/players", True),
                ("viewer_user", "/api/betting", False),
            ]

            for username, endpoint, should_pass in test_cases:
                user = self.users.get(username)
                if user:
                    has_access = self.check_access(user["role"], endpoint)
                    test_name = f"{username}→{endpoint}"
                    if has_access == should_pass:
                        results["access_control_tests"][test_name] = "pass"
                        logger.info(
                            f"  ✅ {test_name}: {'allowed' if has_access else 'denied'} (expected)"
                        )
                    else:
                        results["access_control_tests"][test_name] = "fail"

            # Test 3: Token operations
            logger.info("Testing token operations...")
            test_user = self.users.get("admin_user")
            if test_user:
                # Generate access token
                access_token = self.generate_access_token(test_user)
                results["token_operations"]["access_token_generated"] = bool(
                    access_token
                )

                # Validate token
                if access_token:
                    payload = self.validate_token(access_token)
                    results["token_operations"]["token_validated"] = payload is not None

                # Generate refresh token
                refresh_token = self.generate_refresh_token(test_user)
                results["token_operations"]["refresh_token_generated"] = bool(
                    refresh_token
                )

            # Calculate statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            results["execution_time"] = execution_time
            results["timestamp"] = datetime.now().isoformat()
            results["total_auth_events"] = len(self.auth_log)

            logger.info(f"✅ Authentication system tested successfully")
            logger.info(f"   Users: {results['users_created']}")
            logger.info(f"   Auth tests: {len(results['authentication_tests'])}")
            logger.info(f"   Access tests: {len(results['access_control_tests'])}")
            logger.info(f"   Auth events logged: {results['total_auth_events']}")
            logger.info(f"Execution completed in {execution_time:.2f}s")
            return results

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    # ===== User Management =====

    def create_user(
        self, username: str, password: str, role: UserRole, email: str
    ) -> bool:
        """
        Create a new user with hashed password.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role (UserRole enum)
            email: User email address

        Returns:
            bool: True if user created successfully
        """
        if username in self.users:
            logger.warning(f"User {username} already exists")
            return False

        password_hash = self._hash_password(password)

        self.users[username] = {
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
        }

        self._log_auth_event("user_created", username, {"role": role.value})
        return True

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return self._hash_password(password) == password_hash

    # ===== Authentication =====

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """
        Authenticate user and return access + refresh tokens.

        Args:
            username: Username
            password: Password

        Returns:
            dict: {"access_token": str, "refresh_token": str} or None if auth fails
        """
        user = self.users.get(username)
        if not user:
            self._log_auth_event("auth_failed", username, {"reason": "user_not_found"})
            return None

        if not self._verify_password(password, user["password_hash"]):
            self._log_auth_event(
                "auth_failed", username, {"reason": "invalid_password"}
            )
            return None

        # Update last login
        user["last_login"] = datetime.now().isoformat()

        # Generate tokens
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)

        self._log_auth_event("auth_success", username, {"role": user["role"].value})

        return {"access_token": access_token, "refresh_token": refresh_token}

    # ===== Token Management =====

    def generate_access_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT access token."""
        if self.mock_mode:
            # Mock token for testing
            return f"mock_access_token_{user['username']}_{secrets.token_hex(8)}"

        payload = {
            "username": user["username"],
            "role": user["role"].value,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(seconds=self.access_token_expiry),
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        self.active_tokens[token] = {"user": user["username"], "type": "access"}
        return token

    def generate_refresh_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT refresh token."""
        if self.mock_mode:
            # Mock token for testing
            return f"mock_refresh_token_{user['username']}_{secrets.token_hex(8)}"

        payload = {
            "username": user["username"],
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(seconds=self.refresh_token_expiry),
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        self.active_tokens[token] = {"user": user["username"], "type": "refresh"}
        return token

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return payload.

        Args:
            token: JWT token string

        Returns:
            dict: Token payload if valid, None otherwise
        """
        if self.mock_mode:
            # Mock validation - just check format
            if token.startswith("mock_access_token_") or token.startswith(
                "mock_refresh_token_"
            ):
                username = token.split("_")[3]
                user = self.users.get(username)
                if user:
                    return {
                        "username": username,
                        "role": user["role"].value,
                        "type": "access" if "access" in token else "refresh",
                    }
            return None

        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            # Check if token is in active tokens list
            if token not in self.active_tokens:
                logger.warning(
                    "Token not found in active tokens (may have been revoked)"
                )
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def revoke_token(self, token: str):
        """Revoke a token."""
        if token in self.active_tokens:
            del self.active_tokens[token]
            self._log_auth_event(
                "token_revoked",
                self.active_tokens.get(token, {}).get("user", "unknown"),
                {},
            )

    # ===== Access Control =====

    def check_access(self, user_role: UserRole, endpoint: str) -> bool:
        """
        Check if user role has access to endpoint.

        Args:
            user_role: User's role
            endpoint: API endpoint path

        Returns:
            bool: True if access granted
        """
        allowed_roles = self.ENDPOINT_PERMISSIONS.get(endpoint)
        if allowed_roles is None:
            # Endpoint not defined - deny by default
            return False

        return user_role in allowed_roles

    # ===== Audit Logging =====

    def _log_auth_event(self, event_type: str, username: str, metadata: Dict[str, Any]):
        """Log authentication event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "username": username,
            "metadata": metadata,
        }
        self.auth_log.append(event)

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        logger.info(f"   Total authentication events: {len(self.auth_log)}")
        logger.info(f"   Active tokens: {len(self.active_tokens)}")
        logger.info("✅ Cleanup complete")


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info(f"Starting: Security Implementation - Variation 43")
    logger.info("=" * 80)

    # Load configuration
    config_file = os.path.join(os.path.dirname(__file__), "config.json")

    config = {}
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)

    # Initialize and execute
    implementation = SecurityImplementationVariation43(config)

    # Validate prerequisites
    if not implementation.validate_prerequisites():
        logger.error("Prerequisites not met. Exiting.")
        sys.exit(1)

    # Setup
    if not implementation.setup():
        logger.error("Setup failed. Exiting.")
        sys.exit(1)

    # Execute
    results = implementation.execute()

    # Cleanup
    implementation.cleanup()

    # Report results
    logger.info("=" * 80)
    logger.info("Results:")
    logger.info(json.dumps(results, indent=2))
    logger.info("=" * 80)

    if results.get("success"):
        logger.info("✅ Implementation completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Implementation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
