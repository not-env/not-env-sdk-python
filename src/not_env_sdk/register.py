"""
Entry point for automatic registration of not-env SDK.

Import this module at the very beginning of your application to automatically
initialize the SDK and patch os.environ.
"""

from .sdk import initialize

# Automatically initialize on import
initialize()

