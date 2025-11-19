"""
not-env Python SDK

A Python SDK that fetches environment variables from not-env and transparently
overrides os.environ so existing code using os.environ['FOO'] or os.getenv('FOO')
works unchanged.
"""

__version__ = "0.1.0"

from .sdk import NotEnvSDK, initialize

__all__ = ["NotEnvSDK", "initialize"]

