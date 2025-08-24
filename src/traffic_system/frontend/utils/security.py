"""
Security Utilities for Frontend Application

Implements security measures including path validation, input sanitization,
secure backup handling, and basic access controls.
"""

import logging
import re
import shlex
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Handles security validation for frontend operations."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize security validator.

        Args:
            project_root: Root directory of the project for path validation
        """
        self.project_root = project_root or Path.cwd()
        self.allowed_extensions = {
            ".yaml",
            ".yml",
            ".json",
            ".txt",
            ".log",
            ".py",
            ".md",
        }
        self.blocked_patterns = [
            r"\.\./",  # Directory traversal
            r"\.\.\\",  # Windows directory traversal
            r"/etc/",  # System directories
            r"/root/",  # Root directory
            r"C:\\Windows",  # Windows system
            r"C:\\Program Files",  # Program files
        ]

    def validate_file_path(self, file_path: str | Path) -> tuple[bool, str]:
        """
        Validate that a file path is safe for operations.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path).resolve()

            # Check if path is within project root
            try:
                path.relative_to(self.project_root.resolve())
            except ValueError:
                return False, "Path is outside project directory"

            # Check for blocked patterns
            path_str = str(path)
            for pattern in self.blocked_patterns:
                if re.search(pattern, path_str, re.IGNORECASE):
                    return False, f"Path contains blocked pattern: {pattern}"

            # Check file extension if it's a file
            if path.suffix and path.suffix.lower() not in self.allowed_extensions:
                return False, f"File extension not allowed: {path.suffix}"

            return True, ""

        except Exception as e:
            logger.error(f"Error validating path {file_path}: {e}")
            return False, f"Path validation error: {e}"

    def sanitize_command_input(
        self, command: str | list[str]
    ) -> tuple[bool, str | list[str], str]:
        """
        Sanitize command input to prevent injection attacks.

        Args:
            command: Command string or list to sanitize

        Returns:
            Tuple of (is_safe, sanitized_command, error_message)
        """
        try:
            if isinstance(command, str):
                # Check for dangerous characters and patterns
                dangerous_chars = ["|", "&", ";", "`", "$", "<", ">", "\\"]
                dangerous_patterns = [
                    r"rm\s+-rf",
                    r"del\s+/[sq]",
                    r"format\s+c:",
                    r"nc\s+",
                    r"netcat",
                ]

                # Check for dangerous characters
                if any(char in command for char in dangerous_chars):
                    return False, command, "Command contains dangerous characters"

                # Check for dangerous patterns
                for pattern in dangerous_patterns:
                    if re.search(pattern, command, re.IGNORECASE):
                        return (
                            False,
                            command,
                            f"Command contains dangerous pattern: {pattern}",
                        )

                # Use shlex to properly quote the command
                sanitized = shlex.quote(command)
                return True, sanitized, ""

            elif isinstance(command, list):
                sanitized_list = []
                for arg in command:
                    if not isinstance(arg, str):
                        return False, command, "All command arguments must be strings"

                    # Check for dangerous characters in each argument
                    dangerous_chars = ["|", "&", ";", "`", "$", "<", ">", "\\"]
                    if any(char in arg for char in dangerous_chars):
                        return (
                            False,
                            command,
                            f"Argument contains dangerous characters: {arg}",
                        )

                    sanitized_list.append(shlex.quote(arg))

                return True, sanitized_list, ""

            else:
                return False, command, "Command must be string or list"

        except Exception as e:
            logger.error(f"Error sanitizing command: {e}")
            return False, command, f"Command sanitization error: {e}"

    def validate_service_name(self, service_name: str) -> tuple[bool, str]:
        """
        Validate service name to prevent injection.

        Args:
            service_name: Service name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Only allow alphanumeric characters and underscores
        if not re.match(r"^[a-zA-Z0-9_]+$", service_name):
            return False, "Service name contains invalid characters"

        # Check length
        if len(service_name) > 50:
            return False, "Service name too long"

        if len(service_name) == 0:
            return False, "Service name cannot be empty"

        return True, ""

    def validate_config_value(self, key: str, value: Any) -> tuple[bool, str]:
        """
        Validate configuration values for security.

        Args:
            key: Configuration key
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check for dangerous values in string fields
            if isinstance(value, str):
                # Check for script injection patterns
                script_patterns = [
                    r"<script",
                    r"javascript:",
                    r"eval\(",
                    r"exec\(",
                    r"system\(",
                    r"subprocess\.",
                    r"os\.",
                ]

                for pattern in script_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return (
                            False,
                            f"Value contains potentially dangerous pattern: {pattern}",
                        )

                # Check for path traversal in file paths
                if "path" in key.lower() or "file" in key.lower():
                    is_valid, error = self.validate_file_path(value)
                    if not is_valid:
                        return False, f"Invalid file path: {error}"

            # Validate numeric ranges for ports
            if "port" in key.lower() and isinstance(value, int):
                if not (1024 <= value <= 65535):
                    return False, "Port must be between 1024 and 65535"

            return True, ""

        except Exception as e:
            logger.error(f"Error validating config value {key}: {e}")
            return False, f"Validation error: {e}"


class SecureBackupManager:
    """Handles secure backup operations."""

    def __init__(self, backup_dir: Path, security_validator: SecurityValidator):
        """
        Initialize secure backup manager.

        Args:
            backup_dir: Directory for storing backups
            security_validator: Security validator instance
        """
        self.backup_dir = backup_dir
        self.security_validator = security_validator
        self.max_backups = 50  # Limit number of backups
        self.max_backup_size = 10 * 1024 * 1024  # 10MB max backup size

    def validate_backup_operation(self, backup_path: Path) -> tuple[bool, str]:
        """
        Validate backup operation for security.

        Args:
            backup_path: Path to backup file

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate path
        is_valid, error = self.security_validator.validate_file_path(backup_path)
        if not is_valid:
            return False, f"Invalid backup path: {error}"

        # Check if backup is within backup directory
        try:
            backup_path.resolve().relative_to(self.backup_dir.resolve())
        except ValueError:
            return False, "Backup path is outside backup directory"

        # Check file size if it exists
        if backup_path.exists():
            size = backup_path.stat().st_size
            if size > self.max_backup_size:
                return False, f"Backup file too large: {size} bytes"

        return True, ""

    def cleanup_old_backups(self) -> tuple[int, list[str]]:
        """
        Clean up old backup files to prevent disk space issues.

        Returns:
            Tuple of (files_deleted, error_messages)
        """
        try:
            if not self.backup_dir.exists():
                return 0, []

            # Get all backup files sorted by modification time
            backup_files = []
            for file_path in self.backup_dir.glob("*.yaml"):
                if file_path.is_file():
                    backup_files.append((file_path.stat().st_mtime, file_path))

            backup_files.sort(reverse=True)  # Newest first

            # Keep only the most recent backups
            files_to_delete = backup_files[self.max_backups :]
            deleted_count = 0
            errors = []

            for _, file_path in files_to_delete:
                try:
                    # Validate before deletion
                    is_valid, error = self.validate_backup_operation(file_path)
                    if is_valid:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️ Deleted old backup: {file_path.name}")
                    else:
                        errors.append(f"Cannot delete {file_path.name}: {error}")
                except Exception as e:
                    errors.append(f"Error deleting {file_path.name}: {e}")

            return deleted_count, errors

        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            return 0, [f"Cleanup error: {e}"]


class SessionManager:
    """Basic session management for access control."""

    def __init__(self) -> None:
        """Initialize session manager."""
        self.session_timeout = 3600  # 1 hour
        self.max_concurrent_sessions = 5
        self.active_sessions: dict[str, dict[str, Any]] = {}

    def create_session(
        self, session_id: str, user_info: dict[str, Any] | None = None
    ) -> bool:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            user_info: Optional user information

        Returns:
            True if session created successfully
        """
        try:
            # Check session limit
            if len(self.active_sessions) >= self.max_concurrent_sessions:
                # Remove oldest session
                oldest_session = min(
                    self.active_sessions.items(), key=lambda x: x[1]["created_at"]
                )
                del self.active_sessions[oldest_session[0]]
                logger.warning(
                    f"⚠️ Removed oldest session due to limit: {oldest_session[0]}"
                )

            # Create new session
            self.active_sessions[session_id] = {
                "created_at": time.time(),
                "last_activity": time.time(),
                "user_info": user_info or {},
                "operations_count": 0,
            }

            logger.info(f"✅ Created session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
            return False

    def validate_session(self, session_id: str) -> tuple[bool, str]:
        """
        Validate an existing session.

        Args:
            session_id: Session identifier to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if session_id not in self.active_sessions:
            return False, "Session not found"

        session = self.active_sessions[session_id]
        current_time = time.time()

        # Check timeout
        if current_time - session["last_activity"] > self.session_timeout:
            del self.active_sessions[session_id]
            return False, "Session expired"

        # Update last activity
        session["last_activity"] = current_time
        session["operations_count"] += 1

        return True, ""

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if current_time - session["last_activity"] > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"🧹 Cleaned up expired session: {session_id}")

        return len(expired_sessions)


# Global security instances
_security_validator: SecurityValidator | None = None
_session_manager: SessionManager | None = None


def get_security_validator() -> SecurityValidator:
    """Get global security validator instance."""
    global _security_validator
    if _security_validator is None:
        _security_validator = SecurityValidator()
    return _security_validator


def get_session_manager() -> SessionManager:
    """Get global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def validate_operation_security(operation: str, **kwargs: Any) -> tuple[bool, str]:
    """
    Validate security for a specific operation.

    Args:
        operation: Operation type (e.g., 'file_access', 'service_control', 'config_edit')
        **kwargs: Operation-specific parameters

    Returns:
        Tuple of (is_allowed, error_message)
    """
    try:
        validator = get_security_validator()

        if operation == "file_access":
            file_path = kwargs.get("file_path")
            if not file_path:
                return False, "File path required for file access operation"
            return validator.validate_file_path(file_path)

        elif operation == "service_control":
            service_name = kwargs.get("service_name")
            command = kwargs.get("command")

            if service_name:
                is_valid, error = validator.validate_service_name(service_name)
                if not is_valid:
                    return False, f"Invalid service name: {error}"

            if command:
                is_valid, _, error = validator.sanitize_command_input(command)
                if not is_valid:
                    return False, f"Invalid command: {error}"

        elif operation == "config_edit":
            key = kwargs.get("key")
            value = kwargs.get("value")

            if key and value is not None:
                is_valid, error = validator.validate_config_value(key, value)
                if not is_valid:
                    return False, f"Invalid config value: {error}"

        return True, ""

    except Exception as e:
        logger.error(f"Error validating operation security: {e}")
        return False, f"Security validation error: {e}"
