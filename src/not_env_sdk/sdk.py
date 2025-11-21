"""
Core SDK implementation for not-env Python SDK.
"""

import os
import sys
from typing import Dict, Iterator, List, Optional, Tuple, Union
import urllib.request
import urllib.error
import json


class NotEnvSDK:
    """
    SDK that fetches environment variables from not-env and patches os.environ.
    """

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the SDK.

        Args:
            url: Backend URL (defaults to NOT_ENV_URL env var)
            api_key: API key (defaults to NOT_ENV_API_KEY env var)
        """
        self._url = url or os.environ.get("NOT_ENV_URL")
        self._api_key = api_key or os.environ.get("NOT_ENV_API_KEY")
        self._variables: Dict[str, str] = {}
        self._original_environ = os.environ.copy()
        self._preserved_keys = {"NOT_ENV_URL", "NOT_ENV_API_KEY"}

        if not self._url:
            raise ValueError(
                "NOT_ENV_URL environment variable is required. "
                "Set NOT_ENV_URL and NOT_ENV_API_KEY environment variables. "
                "Get your API key from 'not-env env import' or 'not-env env create' output."
            )
        if not self._api_key:
            raise ValueError(
                "NOT_ENV_API_KEY environment variable is required. "
                "Set NOT_ENV_URL and NOT_ENV_API_KEY environment variables. "
                "Get your API key from 'not-env env import' or 'not-env env create' output."
            )

    def fetch_variables(self) -> Dict[str, str]:
        """
        Fetch all variables from the not-env backend synchronously.
        
        This method blocks until the HTTP request completes, ensuring variables
        are loaded before os.environ is patched.

        Returns:
            Dictionary of variable names to values

        Raises:
            RuntimeError: If the request fails
        """
        # Remove trailing slash from URL
        base_url = self._url.rstrip("/")
        endpoint = f"{base_url}/variables"

        req = urllib.request.Request(endpoint)
        req.add_header("Authorization", f"Bearer {self._api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            # urllib.request.urlopen() is synchronous - it blocks until the request completes
            # Timeout matches JavaScript SDK (30 seconds)
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    # Try to parse error response
                    try:
                        error_body = response.read().decode("utf-8")
                        error_data = json.loads(error_body)
                        error_msg = error_data.get("message", "")
                        raise RuntimeError(
                            f"Failed to fetch variables: {response.status} - {error_msg}"
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        raise RuntimeError(
                            f"Failed to fetch variables: {response.status} - {response.reason}"
                        )
                data = json.loads(response.read().decode("utf-8"))
                # Handle the actual API response format: {"variables": [{"key": "...", "value": "..."}]}
                if isinstance(data, dict) and "variables" in data:
                    # API returns {"variables": [{"key": "...", "value": "..."}]}
                    return {item["key"]: item["value"] for item in data["variables"]}
                elif isinstance(data, list):
                    # If it's a list of {key: ..., value: ...} objects
                    return {item["key"]: item["value"] for item in data}
                elif isinstance(data, dict):
                    # Fallback: if it's a plain dict, return as-is
                    return data
                else:
                    raise RuntimeError(f"Unexpected response format: {type(data)}")
        except urllib.error.HTTPError as e:
            # Try to parse error response body
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = error_data.get("message", e.reason)
                raise RuntimeError(
                    f"Failed to fetch variables: {e.code} - {error_msg}"
                ) from e
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                raise RuntimeError(
                    f"Failed to fetch variables: {e.code} - {e.reason}"
                ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Request failed: {e.reason}") from e
        except TimeoutError as e:
            raise RuntimeError("Request timeout: Failed to fetch variables within 30 seconds") from e

    def initialize(self) -> None:
        """
        Initialize the SDK by fetching variables and patching os.environ.
        
        This method is synchronous and blocks until variables are fetched.
        os.environ is only patched after variables are successfully loaded.
        """
        # Fetch variables synchronously (blocks until complete)
        self._variables = self.fetch_variables()

        # Create a custom dict-like class that intercepts access to os.environ
        # This class provides hermetic behavior: only variables from not-env are available
        # NOT_ENV_URL and NOT_ENV_API_KEY are preserved from the original environment
        class PatchedEnviron:
            def __init__(self, sdk_instance):
                self._sdk = sdk_instance
                self._all_keys = self._compute_all_keys()

            def _compute_all_keys(self) -> set:
                """Compute all available keys."""
                preserved = {
                    k for k in self._sdk._preserved_keys
                    if k in self._sdk._original_environ
                }
                return set(self._sdk._variables.keys()) | preserved

            def _refresh_keys(self) -> None:
                """Refresh the keys cache (useful if variables change)."""
                self._all_keys = self._compute_all_keys()

            def __getitem__(self, key: str) -> str:
                # Preserve NOT_ENV_URL and NOT_ENV_API_KEY from original environment
                if key in self._sdk._preserved_keys:
                    if key in self._sdk._original_environ:
                        return self._sdk._original_environ[key]
                    raise KeyError(key)
                # Return from not-env if exists, otherwise raise KeyError
                if key in self._sdk._variables:
                    return self._sdk._variables[key]
                raise KeyError(key)

            def __setitem__(self, key: str, value: str) -> None:
                # Prevent setting variables (hermetic behavior)
                raise RuntimeError(
                    "Cannot set environment variables. Variables are managed by not-env."
                )

            def __delitem__(self, key: str) -> None:
                # Prevent deletion
                raise RuntimeError(
                    "Cannot delete environment variables. Variables are managed by not-env."
                )

            def __contains__(self, key: str) -> bool:
                # Check if key exists in not-env or preserved keys
                if key in self._sdk._preserved_keys:
                    return key in self._sdk._original_environ
                return key in self._sdk._variables

            def __iter__(self) -> Iterator[str]:
                """Return iterator over all keys (not-env + preserved)."""
                return iter(self._all_keys)

            def keys(self) -> set:
                """Return a set-like view of all keys."""
                return self._all_keys

            def values(self) -> List[str]:
                """Return a list of all values."""
                return [self[k] for k in self._all_keys]

            def items(self) -> List[Tuple[str, str]]:
                """Return a list of all key-value pairs."""
                return [(k, self[k]) for k in self._all_keys]

            def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
                """Get value with default."""
                try:
                    return self[key]
                except KeyError:
                    return default

            def copy(self) -> Dict[str, str]:
                """Return a copy of the environment."""
                result = self._sdk._variables.copy()
                for key in self._sdk._preserved_keys:
                    if key in self._sdk._original_environ:
                        result[key] = self._sdk._original_environ[key]
                return result

            def __len__(self) -> int:
                return len(self._all_keys)

            def pop(self, key: str, default: Optional[str] = None) -> Optional[str]:
                """Pop is not allowed (hermetic behavior)."""
                raise RuntimeError(
                    "Cannot pop environment variables. Variables are managed by not-env."
                )

            def popitem(self) -> Tuple[str, str]:
                """Popitem is not allowed (hermetic behavior)."""
                raise RuntimeError(
                    "Cannot pop environment variables. Variables are managed by not-env."
                )

            def update(self, *args, **kwargs) -> None:
                """Update is not allowed (hermetic behavior)."""
                raise RuntimeError(
                    "Cannot update environment variables. Variables are managed by not-env."
                )

            def clear(self) -> None:
                """Clear is not allowed (hermetic behavior)."""
                raise RuntimeError(
                    "Cannot clear environment variables. Variables are managed by not-env."
                )

            def setdefault(self, key: str, default: Optional[str] = None) -> Optional[str]:
                """Setdefault returns the value if exists, otherwise returns default without setting."""
                return self.get(key, default)

        # Replace os.environ with our patched version
        patched = PatchedEnviron(self)
        # Replace os.environ
        os.environ = patched  # type: ignore


def initialize(url: Optional[str] = None, api_key: Optional[str] = None) -> None:
    """
    Initialize the not-env SDK synchronously.

    This function fetches variables from not-env and patches os.environ.
    The function blocks until variables are loaded, ensuring they are available
    before any code can access os.environ.

    Args:
        url: Backend URL (defaults to NOT_ENV_URL env var)
        api_key: API key (defaults to NOT_ENV_API_KEY env var)

    Raises:
        ValueError: If required environment variables are missing
        RuntimeError: If initialization fails
    """
    sdk = NotEnvSDK(url=url, api_key=api_key)
    try:
        # Initialize synchronously - blocks until variables are loaded
        sdk.initialize()
    except Exception as e:
        print(f"Failed to initialize not-env-sdk: {e}", file=sys.stderr)
        sys.exit(1)

