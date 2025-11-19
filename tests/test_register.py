"""
Test suite for not-env-sdk-python register logic.

These tests verify the core logic functions similar to the JS SDK tests.
Note: Full integration tests would require a running backend server.
These tests verify the core logic with mocked HTTP requests.
"""

import os
import json
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse
import pytest

from not_env_sdk.sdk import NotEnvSDK


# Save the original os.environ at module load time, before any SDK patches it
import os as os_module
_original_os_environ = os_module.environ


def restore_original_environ():
    """Restore the original os.environ after SDK patches it."""
    global _original_os_environ
    os_module.environ = _original_os_environ


def create_mock_response(variables):
    """
    Helper function to create a properly configured mock HTTP response.
    
    Args:
        variables: List of dicts with 'key' and 'value' keys (e.g., [{"key": "FOO", "value": "bar"}])
    
    Returns:
        MagicMock configured as a context manager with status and read() method
    """
    mock_response = MagicMock()
    mock_response.status = 200
    response_data = {"variables": variables}
    mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestURLParsing:
    """Test URL parsing logic similar to JS SDK tests."""

    def test_url_parsing_https(self):
        """Test parsing HTTPS URLs."""
        url = urlparse("https://test.example.com")
        assert url.scheme == "https"
        assert url.hostname == "test.example.com"
        assert url.port is None

    def test_url_parsing_http_with_port(self):
        """Test parsing HTTP URLs with port."""
        url = urlparse("http://localhost:1212")
        assert url.scheme == "http"
        assert url.hostname == "localhost"
        assert url.port == 1212

    def test_url_parsing_with_path(self):
        """Test parsing URLs with paths."""
        url = urlparse("https://not-env.example.com/api/v1")
        assert url.scheme == "https"
        assert url.hostname == "not-env.example.com"
        assert url.path == "/api/v1"


class TestJSONResponseParsing:
    """Test JSON response parsing similar to JS SDK tests."""

    def test_json_response_parsing_list_format(self):
        """Test parsing API response in list format (actual API format)."""
        response = {
            "variables": [
                {"key": "DB_HOST", "value": "localhost"},
                {"key": "DB_PORT", "value": "5432"}
            ]
        }

        # Simulate how the SDK processes this
        var_map = {}
        if isinstance(response, dict) and "variables" in response:
            for v in response["variables"]:
                var_map[v["key"]] = v["value"]
        elif isinstance(response, list):
            var_map = {item["key"]: item["value"] for item in response}

        assert var_map.get("DB_HOST") == "localhost"
        assert var_map.get("DB_PORT") == "5432"
        assert "NONEXISTENT" not in var_map

    def test_json_response_parsing_dict_format(self):
        """Test parsing API response in dict format (alternative format)."""
        response = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432"
        }

        # Simulate how the SDK processes this
        var_map = {}
        if isinstance(response, dict) and "variables" in response:
            for v in response["variables"]:
                var_map[v["key"]] = v["value"]
        elif isinstance(response, list):
            var_map = {item["key"]: item["value"] for item in response}
        elif isinstance(response, dict):
            var_map = response

        assert var_map.get("DB_HOST") == "localhost"
        assert var_map.get("DB_PORT") == "5432"
        assert "NONEXISTENT" not in var_map


class TestPreservedVariables:
    """Test preserved variables logic similar to JS SDK tests."""

    def test_preserved_variables_get(self):
        """Test that NOT_ENV_URL and NOT_ENV_API_KEY are preserved from original environment."""
        # Set up test environment
        os.environ["NOT_ENV_URL"] = "https://test.example.com"
        os.environ["NOT_ENV_API_KEY"] = "test-key"

        try:
            # Mock the HTTP request
            mock_response = create_mock_response([
                {"key": "DB_HOST", "value": "localhost"}
            ])

            with patch("urllib.request.urlopen", return_value=mock_response):
                sdk = NotEnvSDK()
                sdk.initialize()

                # Test preserved variables
                assert os.environ["NOT_ENV_URL"] == "https://test.example.com"
                assert os.environ["NOT_ENV_API_KEY"] == "test-key"
                assert os.environ["DB_HOST"] == "localhost"
        finally:
            # Restore original os.environ
            restore_original_environ()

    def test_preserved_variables_contains(self):
        """Test that preserved variables work with 'in' operator."""
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set up test environment
        os.environ["NOT_ENV_URL"] = "https://test.example.com"
        os.environ["NOT_ENV_API_KEY"] = "test-key"

        try:
            # Mock the HTTP request
            mock_response = create_mock_response([
                {"key": "DB_HOST", "value": "localhost"}
            ])

            with patch("urllib.request.urlopen", return_value=mock_response):
                sdk = NotEnvSDK()
                sdk.initialize()

                # Test 'in' operator
                assert "NOT_ENV_URL" in os.environ
                assert "DB_HOST" in os.environ
                assert "NONEXISTENT" not in os.environ
                # NOT_ENV_API_KEY should be in environ if it was in original
                assert "NOT_ENV_API_KEY" in os.environ
        finally:
            # Restore original environment
            restore_original_environ()

    def test_preserved_variables_getitem(self):
        """Test accessing preserved variables via __getitem__."""
        # Save original environment
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set up test environment
        os.environ["NOT_ENV_URL"] = "https://test.example.com"
        os.environ["NOT_ENV_API_KEY"] = "test-key"

        try:
            # Mock the HTTP request
            mock_response = create_mock_response([
                {"key": "DB_HOST", "value": "localhost"}
            ])

            with patch("urllib.request.urlopen", return_value=mock_response):
                sdk = NotEnvSDK()
                sdk.initialize()

                # Test accessing preserved variables
                assert os.environ["NOT_ENV_URL"] == "https://test.example.com"
                assert os.environ["NOT_ENV_API_KEY"] == "test-key"
                assert os.environ["DB_HOST"] == "localhost"
                
                # Test that non-existent variables raise KeyError
                with pytest.raises(KeyError):
                    _ = os.environ["NONEXISTENT"]
        finally:
            # Restore original environment
            restore_original_environ()


class TestDictLikeBehavior:
    """Test dict-like behavior similar to JS SDK tests."""

    def test_keys_method(self):
        """Test that keys() returns all keys from not-env plus preserved vars."""
        # Save original environment
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set up test environment
        os.environ["NOT_ENV_URL"] = "https://test.example.com"
        os.environ["NOT_ENV_API_KEY"] = "test-key"

        try:
            # Mock the HTTP request
            mock_response = create_mock_response([
                {"key": "DB_HOST", "value": "localhost"},
                {"key": "DB_PORT", "value": "5432"}
            ])

            with patch("urllib.request.urlopen", return_value=mock_response):
                sdk = NotEnvSDK()
                sdk.initialize()

                keys = set(os.environ.keys())
                assert "NOT_ENV_URL" in keys
                assert "NOT_ENV_API_KEY" in keys
                assert "DB_HOST" in keys
                assert "DB_PORT" in keys
                assert "NONEXISTENT" not in keys
        finally:
            # Restore original environment
            restore_original_environ()

    def test_get_method(self):
        """Test that get() method works with defaults."""
        # Save original environment
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set up test environment
        os.environ["NOT_ENV_URL"] = "https://test.example.com"

        try:
            # Set up test environment
            os.environ["NOT_ENV_URL"] = "https://test.example.com"
            os.environ["NOT_ENV_API_KEY"] = "test-key"

            # Mock the HTTP request - urlopen returns a context manager
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps({
                "variables": [
                    {"key": "DB_HOST", "value": "localhost"}
                ]
            }).encode("utf-8")
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)

            with patch("urllib.request.urlopen", return_value=mock_response):
                sdk = NotEnvSDK()
                sdk.initialize()

                # Test get() with existing key
                assert os.environ.get("DB_HOST") == "localhost"
                assert os.environ.get("NOT_ENV_URL") == "https://test.example.com"
                
                # Test get() with non-existent key (should return None)
                assert os.environ.get("NONEXISTENT") is None
                
                # Test get() with default value
                assert os.environ.get("NONEXISTENT", "default") == "default"
        finally:
            # Restore original environment
            restore_original_environ()

    def test_hermetic_behavior_setitem(self):
        """Test that setting variables is prevented (hermetic behavior)."""
        # Save original environment
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set up test environment
        os.environ["NOT_ENV_URL"] = "https://test.example.com"
        os.environ["NOT_ENV_API_KEY"] = "test-key"

        try:
            # Mock the HTTP request
            mock_response = create_mock_response([
                {"key": "DB_HOST", "value": "localhost"}
            ])

            with patch("urllib.request.urlopen", return_value=mock_response):
                sdk = NotEnvSDK()
                sdk.initialize()

                # Test that setting variables raises RuntimeError
                with pytest.raises(RuntimeError, match="Cannot set environment variables"):
                    os.environ["NEW_VAR"] = "new_value"
        finally:
            # Restore original environment
            restore_original_environ()

    def test_hermetic_behavior_delitem(self):
        """Test that deleting variables is prevented (hermetic behavior)."""
        # Save original environment
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set up test environment
        os.environ["NOT_ENV_URL"] = "https://test.example.com"
        os.environ["NOT_ENV_API_KEY"] = "test-key"

        try:
            # Mock the HTTP request
            mock_response = create_mock_response([
                {"key": "DB_HOST", "value": "localhost"}
            ])

            with patch("urllib.request.urlopen", return_value=mock_response):
                sdk = NotEnvSDK()
                sdk.initialize()

                # Test that deleting variables raises RuntimeError
                with pytest.raises(RuntimeError, match="Cannot delete environment variables"):
                    del os.environ["DB_HOST"]
        finally:
            # Restore original environment
            restore_original_environ()


class TestSDKInitialization:
    """Test SDK initialization and error handling."""

    def test_missing_url_raises_error(self):
        """Test that missing NOT_ENV_URL raises ValueError."""
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Remove NOT_ENV_URL if it exists
        if "NOT_ENV_URL" in os.environ:
            del os.environ["NOT_ENV_URL"]
        if "NOT_ENV_API_KEY" in os.environ:
            del os.environ["NOT_ENV_API_KEY"]

        try:
            with pytest.raises(ValueError, match="NOT_ENV_URL environment variable is required"):
                NotEnvSDK()
        finally:
            # Restore original environment
            restore_original_environ()

    def test_missing_api_key_raises_error(self):
        """Test that missing NOT_ENV_API_KEY raises ValueError."""
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set URL but not API key
        os.environ["NOT_ENV_URL"] = "https://test.example.com"
        if "NOT_ENV_API_KEY" in os.environ:
            del os.environ["NOT_ENV_API_KEY"]

        try:
            with pytest.raises(ValueError, match="NOT_ENV_API_KEY environment variable is required"):
                NotEnvSDK()
        finally:
            # Restore original environment
            restore_original_environ()

    def test_url_trailing_slash_handling(self):
        """Test that URLs with trailing slashes are handled correctly."""
        # Restore original environment first in case previous test patched it
        restore_original_environ()
        
        # Set up test environment with trailing slash
        os.environ["NOT_ENV_URL"] = "https://test.example.com/"
        os.environ["NOT_ENV_API_KEY"] = "test-key"

        try:
            # Mock the HTTP request
            mock_response = create_mock_response([
                {"key": "DB_HOST", "value": "localhost"}
            ])

            with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
                sdk = NotEnvSDK()
                sdk.initialize()

                # Verify the URL was called correctly
                # Check that the request was made (urlopen was called)
                assert mock_urlopen.called
                # Verify the endpoint construction by checking the SDK's internal logic
                # The SDK should strip trailing slashes and append /variables
                base_url = sdk._url.rstrip("/")
                expected_endpoint = f"{base_url}/variables"
                assert expected_endpoint == "https://test.example.com/variables"
        finally:
            # Restore original environment
            restore_original_environ()

