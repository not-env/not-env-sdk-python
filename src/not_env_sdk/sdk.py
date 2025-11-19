"""
Core SDK implementation for not-env Python SDK.
"""

import os
import sys
from typing import Dict, Optional
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
            raise ValueError("NOT_ENV_URL environment variable is required")
        if not self._api_key:
            raise ValueError("NOT_ENV_API_KEY environment variable is required")

    def fetch_variables(self) -> Dict[str, str]:
        """
        Fetch all variables from the not-env backend.

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
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"Failed to fetch variables: {response.status} - {response.reason}"
                    )
                data = json.loads(response.read().decode("utf-8"))
                # Assuming the API returns a dict or list of dicts with key/value pairs
                # Adjust based on actual API response format
                if isinstance(data, dict):
                    return data
                elif isinstance(data, list):
                    # If it's a list of {key: ..., value: ...} objects
                    return {item["key"]: item["value"] for item in data}
                else:
                    raise RuntimeError(f"Unexpected response format: {type(data)}")
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Failed to fetch variables: {e.code} - {e.reason}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Request failed: {e.reason}") from e

    def initialize(self) -> None:
        """
        Initialize the SDK by fetching variables and patching os.environ.
        """
        self._variables = self.fetch_variables()

        # Create a custom dict-like class that intercepts access to os.environ
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

            def __iter__(self):
                # Return iterator over all keys (not-env + preserved)
                return iter(self._all_keys)

            def keys(self):
                """Return a dict_keys view of all keys."""
                return self._all_keys

            def values(self):
                """Return a dict_values view of all values."""
                return [self[k] for k in self._all_keys]

            def items(self):
                """Return a dict_items view of all key-value pairs."""
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

            def popitem(self):
                """Popitem is not allowed (hermetic behavior)."""
                raise RuntimeError(
                    "Cannot pop environment variables. Variables are managed by not-env."
                )

            def update(self, *args, **kwargs):
                """Update is not allowed (hermetic behavior)."""
                raise RuntimeError(
                    "Cannot update environment variables. Variables are managed by not-env."
                )

            def clear(self):
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
    Initialize the not-env SDK.

    This function fetches variables from not-env and patches os.environ.

    Args:
        url: Backend URL (defaults to NOT_ENV_URL env var)
        api_key: API key (defaults to NOT_ENV_API_KEY env var)

    Raises:
        ValueError: If required environment variables are missing
        RuntimeError: If initialization fails
    """
    sdk = NotEnvSDK(url=url, api_key=api_key)
    try:
        sdk.initialize()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

