"""
Entry point for automatic registration of not-env SDK.

Import this module at the very beginning of your application to automatically
initialize the SDK and patch os.environ.

This module executes synchronously - it blocks until environment variables are
fetched from the not-env backend, ensuring they are available before any code
can access os.environ.
"""

from .sdk import initialize

# Automatically initialize on import (synchronously - blocks until variables are loaded)
initialize()

