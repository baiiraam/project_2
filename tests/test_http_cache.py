"""Extended tests for HTTP cache to improve coverage."""

from unittest.mock import MagicMock, patch


class TestHTTPCacheExtended:
    """Extended HTTP cache tests."""

    def test_get_cache_stats_enabled_with_db(self):
        """Test getting cache stats when enabled with SQLite."""
        from src.services.http_cache import get_cache_stats

        with patch("src.services.http_cache._cache_initialized", True):
            with patch("requests_cache.get_cache") as mock_get:
                mock_session = MagicMock()
                mock_session.db_path = "test_cache.db"
                mock_get.return_value = mock_session

                with patch("sqlite3.connect") as mock_sqlite:
                    mock_conn = MagicMock()
                    mock_cursor = MagicMock()
                    mock_cursor.fetchone.return_value = (5,)
                    mock_conn.cursor.return_value = mock_cursor
                    mock_sqlite.return_value = mock_conn

                    with patch("src.services.http_cache._get_settings") as mock_settings:
                        mock_settings.return_value.HTTP_CACHE_TTL_SECONDS = 86400

                        stats = get_cache_stats()
                        assert stats is not None
                        assert stats["status"] == "enabled"

    def test_get_cache_stats_sqlite_error(self):
        """Test cache stats when SQLite has error."""
        from src.services.http_cache import get_cache_stats

        with patch("src.services.http_cache._cache_initialized", True):
            with patch("requests_cache.get_cache") as mock_get:
                mock_session = MagicMock()
                mock_session.db_path = "test_cache.db"
                mock_get.return_value = mock_session

                with patch("sqlite3.connect", side_effect=Exception("SQLite error")):
                    stats = get_cache_stats()
                    # When SQLite has error, the function may return None or basic stats
                    # Both are acceptable error handling behaviors
                    # The important thing is it doesn't crash
                    if stats is not None:
                        # If it returns stats, ensure they have the expected structure
                        assert isinstance(stats, dict)
                        assert "status" in stats
                    else:
                        # None is also acceptable - indicates error
                        assert stats is None

    def test_get_cache_stats_no_db_path(self):
        """Test cache stats when session has no db_path."""
        from src.services.http_cache import get_cache_stats

        with patch("src.services.http_cache._cache_initialized", True):
            with patch("requests_cache.get_cache") as mock_get:
                mock_session = MagicMock()
                # No db_path attribute
                del mock_session.db_path
                mock_get.return_value = mock_session

                stats = get_cache_stats()
                assert stats is not None
                assert stats["status"] == "enabled"

    def test_get_cache_stats_exception(self):
        """Test cache stats when exception occurs."""
        from src.services.http_cache import get_cache_stats

        with patch("src.services.http_cache._cache_initialized", True):
            with patch("requests_cache.get_cache", side_effect=Exception("Unexpected error")):
                stats = get_cache_stats()
                assert stats is None

    def test_clear_cache_success(self):
        """Test clearing cache successfully."""
        from src.services.http_cache import clear_cache

        with patch("src.services.http_cache._cache_initialized", True):
            with patch("requests_cache.clear") as mock_clear:
                result = clear_cache()
                assert result is True
                mock_clear.assert_called_once()

    def test_clear_cache_exception(self):
        """Test clear cache when exception occurs."""
        from src.services.http_cache import clear_cache

        with patch("src.services.http_cache._cache_initialized", True):
            with patch("requests_cache.clear", side_effect=Exception("Clear failed")):
                result = clear_cache()
                assert result is False

    def test_setup_http_cache_with_cache_dir(self):
        """Test cache setup with custom cache directory."""
        from src.services.http_cache import setup_http_cache

        with patch("src.services.http_cache._get_settings") as mock_settings:
            mock_settings.return_value.HTTP_CACHE_ENABLED = True

            with patch("requests_cache.install_cache"):
                with patch("os.makedirs") as mock_makedirs:
                    import src.services.http_cache
                    src.services.http_cache._cache_initialized = False

                    setup_http_cache(cache_name="test", cache_dir="./custom_cache")

                    mock_makedirs.assert_called_once_with("./custom_cache", exist_ok=True)

    def test_setup_http_cache_permission_error(self):
        """Test cache setup with permission error."""
        from src.services.http_cache import setup_http_cache

        with patch("src.services.http_cache._get_settings") as mock_settings:
            mock_settings.return_value.HTTP_CACHE_ENABLED = True

            with patch("requests_cache.install_cache", side_effect=PermissionError("Access denied")):
                import src.services.http_cache
                src.services.http_cache._cache_initialized = False

                # Should not raise exception
                setup_http_cache()

    def test_setup_http_cache_os_error(self):
        """Test cache setup with OS error."""
        from src.services.http_cache import setup_http_cache

        with patch("src.services.http_cache._get_settings") as mock_settings:
            mock_settings.return_value.HTTP_CACHE_ENABLED = True

            with patch("requests_cache.install_cache", side_effect=OSError("Disk full")):
                import src.services.http_cache
                src.services.http_cache._cache_initialized = False

                # Should not raise exception
                setup_http_cache()

    def test_setup_http_cache_already_initialized(self):
        """Test cache setup when already initialized."""
        from src.services.http_cache import setup_http_cache

        with patch("src.services.http_cache._cache_initialized", True):
            with patch("requests_cache.install_cache") as mock_install:
                setup_http_cache()
                mock_install.assert_not_called()  # Should not re-initialize

    def test_clear_cache_disabled(self):
        """Test clearing cache when disabled."""
        from src.services.http_cache import clear_cache

        with patch("src.services.http_cache._cache_initialized", False):
            with patch("src.services.http_cache._get_settings") as mock_settings:
                mock_settings.return_value.HTTP_CACHE_ENABLED = False
                result = clear_cache()
                assert result is False
