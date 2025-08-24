"""
Performance Optimization Utilities

Implements caching, session state management, and UI optimizations
for improved user experience and application performance.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Handles performance optimizations for the frontend application."""

    def __init__(self) -> None:
        """Initialize performance optimizer."""
        self.cache_stats = {"hits": 0, "misses": 0, "total_time_saved": 0.0}
        self._initialize_session_cache()

    def _initialize_session_cache(self) -> None:
        """Initialize session-level cache."""
        if "performance_cache" not in st.session_state:
            st.session_state.performance_cache = {}
        if "cache_timestamps" not in st.session_state:
            st.session_state.cache_timestamps = {}

    @staticmethod
    def cached_operation(ttl_seconds: int = 300, key_prefix: str = "") -> Any:
        """
        Decorator for caching expensive operations in session state.

        Args:
            ttl_seconds: Time to live for cached results
            key_prefix: Prefix for cache keys
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                cache_key = f"{key_prefix}_{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

                # Initialize cache if needed
                if "performance_cache" not in st.session_state:
                    st.session_state.performance_cache = {}
                if "cache_timestamps" not in st.session_state:
                    st.session_state.cache_timestamps = {}

                current_time = time.time()

                # Check if cached result exists and is still valid
                if (
                    cache_key in st.session_state.performance_cache
                    and cache_key in st.session_state.cache_timestamps
                ):

                    cache_time = st.session_state.cache_timestamps[cache_key]
                    if current_time - cache_time < ttl_seconds:
                        logger.debug(f"🚀 Cache hit for {func.__name__}")
                        return st.session_state.performance_cache[cache_key]

                # Cache miss - execute function
                logger.debug(f"⏱️ Cache miss for {func.__name__} - executing")
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Store result in cache
                st.session_state.performance_cache[cache_key] = result
                st.session_state.cache_timestamps[cache_key] = current_time

                logger.debug(
                    f"💾 Cached result for {func.__name__} (took {execution_time:.3f}s)"
                )
                return result

            return wrapper

        return decorator

    def clear_cache(self, pattern: str | None = None) -> int:
        """
        Clear cached results.

        Args:
            pattern: Optional pattern to match cache keys

        Returns:
            Number of cache entries cleared
        """
        if "performance_cache" not in st.session_state:
            return 0

        if pattern is None:
            # Clear all cache
            count = len(st.session_state.performance_cache)
            st.session_state.performance_cache.clear()
            st.session_state.cache_timestamps.clear()
            logger.info(f"🧹 Cleared all cache ({count} entries)")
            return count

        # Clear cache entries matching pattern
        keys_to_remove = [
            key for key in st.session_state.performance_cache.keys() if pattern in key
        ]

        for key in keys_to_remove:
            del st.session_state.performance_cache[key]
            if key in st.session_state.cache_timestamps:
                del st.session_state.cache_timestamps[key]

        logger.info(
            f"🧹 Cleared {len(keys_to_remove)} cache entries matching '{pattern}'"
        )
        return len(keys_to_remove)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        cache_size = len(st.session_state.get("performance_cache", {}))
        return {
            "cache_entries": cache_size,
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": (
                self.cache_stats["hits"]
                / max(1, self.cache_stats["hits"] + self.cache_stats["misses"])
            )
            * 100,
            "time_saved": self.cache_stats["total_time_saved"],
        }


class UIOptimizer:
    """Handles UI optimizations and responsive design."""

    @staticmethod
    def show_loading_spinner(message: str = "Cargando...") -> Any:
        """Show a loading spinner with message."""
        return st.spinner(message)

    @staticmethod
    def show_progress_bar(progress: float, message: str = "") -> Any:
        """
        Show a progress bar.

        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional message to display
        """
        if message:
            st.write(message)
        return st.progress(progress)

    @staticmethod
    def create_responsive_columns(num_columns: int, ratios: list | None = None) -> Any:
        """
        Create responsive columns that adapt to screen size.

        Args:
            num_columns: Number of columns
            ratios: Optional column ratios

        Returns:
            Column objects
        """
        if ratios is None:
            return st.columns(num_columns)
        return st.columns(ratios)

    @staticmethod
    def add_loading_state(key: str, default: bool = False) -> bool:
        """
        Add loading state management.

        Args:
            key: Unique key for the loading state
            default: Default loading state

        Returns:
            Current loading state
        """
        loading_key = f"loading_{key}"
        if loading_key not in st.session_state:
            st.session_state[loading_key] = default
        return bool(st.session_state[loading_key])

    @staticmethod
    def set_loading_state(key: str, loading: bool) -> None:
        """
        Set loading state.

        Args:
            key: Unique key for the loading state
            loading: Loading state to set
        """
        loading_key = f"loading_{key}"
        st.session_state[loading_key] = loading

    @staticmethod
    def create_expandable_section(
        title: str, expanded: bool = False, key: str | None = None
    ) -> Any:
        """
        Create an expandable section with state management.

        Args:
            title: Section title
            expanded: Default expanded state
            key: Optional unique key

        Returns:
            Expander object
        """
        if key:
            expanded_key = f"expanded_{key}"
            if expanded_key not in st.session_state:
                st.session_state[expanded_key] = expanded
            expanded = st.session_state[expanded_key]

        return st.expander(title, expanded=expanded)


class SessionStateManager:
    """Efficient session state management."""

    @staticmethod
    def initialize_if_missing(key: str, default_value: Any) -> Any:
        """
        Initialize session state key if missing.

        Args:
            key: Session state key
            default_value: Default value to set

        Returns:
            Current value
        """
        if key not in st.session_state:
            st.session_state[key] = default_value
        return st.session_state[key]

    @staticmethod
    def update_if_changed(key: str, new_value: Any) -> bool:
        """
        Update session state only if value changed.

        Args:
            key: Session state key
            new_value: New value to set

        Returns:
            True if value was updated
        """
        if key not in st.session_state or st.session_state[key] != new_value:
            st.session_state[key] = new_value
            return True
        return False

    @staticmethod
    def get_with_default(key: str, default: Any) -> Any:
        """
        Get session state value with default.

        Args:
            key: Session state key
            default: Default value if key doesn't exist

        Returns:
            Session state value or default
        """
        return st.session_state.get(key, default)

    @staticmethod
    def cleanup_old_keys(max_age_seconds: int = 3600) -> int:
        """
        Clean up old session state keys.

        Args:
            max_age_seconds: Maximum age for keys

        Returns:
            Number of keys cleaned up
        """
        current_time = time.time()
        keys_to_remove = []

        # Look for timestamped keys
        for key in st.session_state.keys():
            if isinstance(key, str) and key.startswith("temp_") and "_timestamp" in key:
                timestamp_key = str(key) + "_timestamp"
                if timestamp_key in st.session_state:
                    timestamp = st.session_state[timestamp_key]
                    if current_time - timestamp > max_age_seconds:
                        keys_to_remove.extend([key, timestamp_key])

        # Remove old keys
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]

        if keys_to_remove:
            logger.info(f"🧹 Cleaned up {len(keys_to_remove)} old session state keys")

        return len(keys_to_remove)


# Global instances
_performance_optimizer: PerformanceOptimizer | None = None
_ui_optimizer: UIOptimizer | None = None
_session_manager: SessionStateManager | None = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def get_ui_optimizer() -> UIOptimizer:
    """Get global UI optimizer instance."""
    global _ui_optimizer
    if _ui_optimizer is None:
        _ui_optimizer = UIOptimizer()
    return _ui_optimizer


def get_session_manager() -> SessionStateManager:
    """Get global session state manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionStateManager()
    return _session_manager


# Streamlit cache decorators for expensive operations
@st.cache_data(ttl=300)  # 5 minutes TTL
def cached_config_load(config_path: str) -> dict[str, Any]:
    """Cache configuration loading."""
    from src.traffic_system.frontend.utils.config_handler import ConfigHandler

    handler = ConfigHandler(config_path)
    return handler.read_config()


@st.cache_data(ttl=60)  # 1 minute TTL
def cached_service_status() -> dict[str, Any]:
    """Cache service status checks."""
    from src.traffic_system.frontend.utils.service_manager import ServiceManager

    manager = ServiceManager()
    return {
        name: status.__dict__
        for name, status in manager.get_all_services_status().items()
    }


@st.cache_data(ttl=600)  # 10 minutes TTL
def cached_backup_list(backup_dir: str) -> list:
    """Cache backup file listing."""
    from src.traffic_system.frontend.utils.config_handler import ConfigHandler

    handler = ConfigHandler()
    return handler.list_backups()


def optimize_streamlit_config() -> None:
    """Apply Streamlit configuration optimizations."""
    # Set page config for better performance
    if not hasattr(st, "_is_running_with_streamlit"):
        return

    # These optimizations are applied at the app level
    st.set_page_config(
        page_title="Traffic System Config",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": None,
            "Report a bug": None,
            "About": "Traffic System Configuration Frontend",
        },
    )


def add_performance_metrics_sidebar() -> None:
    """Add performance metrics to sidebar."""
    try:
        optimizer = get_performance_optimizer()
        stats = optimizer.get_cache_stats()

        with st.sidebar.expander("📊 Performance", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Cache Entries", stats["cache_entries"])
                st.metric("Hit Rate", f"{stats['hit_rate']:.1f}%")

            with col2:
                st.metric("Cache Hits", stats["hits"])
                st.metric("Time Saved", f"{stats['time_saved']:.2f}s")

            if st.button("🧹 Clear Cache", key="clear_cache_btn"):
                cleared = optimizer.clear_cache()
                st.success(f"Cleared {cleared} cache entries")
                st.rerun()

    except Exception as e:
        logger.error(f"Error displaying performance metrics: {e}")


def debounce_input(key: str, delay_ms: int = 500) -> Any:
    """
    Debounce user input to reduce unnecessary operations.

    Args:
        key: Unique key for the debounced input
        delay_ms: Delay in milliseconds

    Returns:
        True if input should be processed
    """
    current_time = time.time() * 1000  # Convert to milliseconds
    last_input_key = f"last_input_{key}"

    if last_input_key not in st.session_state:
        st.session_state[last_input_key] = 0

    time_since_last = current_time - st.session_state[last_input_key]

    if time_since_last >= delay_ms:
        st.session_state[last_input_key] = current_time
        return True

    return False
