# not-env-sdk-python

not-env-sdk-python is a Python SDK that fetches environment variables from not-env and transparently overrides `os.environ` so existing code using `os.environ['FOO']` or `os.getenv('FOO')` works unchanged.

## Overview

The SDK:

* Fetches all variables from not-env at startup
* Monkey-patches `os.environ` to return not-env values
* Preserves `NOT_ENV_URL` and `NOT_ENV_API_KEY` from OS environment
* Makes other keys raise `KeyError` if not in not-env (hermetic behavior)
* Works transparently with existing code

## Installation

```bash
pip install not-env-sdk
```

Or with poetry:

```bash
poetry add not-env-sdk
```

## Prerequisites

* Python 3.8 or later
* A running not-env backend
* An ENV_READ_ONLY or ENV_ADMIN API key

## Quick Start

### 1. Set Environment Variables

Set the backend URL and API key as OS environment variables:

```bash
export NOT_ENV_URL="https://not-env.example.com"
export NOT_ENV_API_KEY="your-env-read-only-key-here"
```

### 2. Import the SDK

Import the SDK at the very beginning of your application (before any other code that uses `os.environ`):

```python
# main.py
import not_env_sdk.register

# Now os.environ is patched
print(os.environ['DB_HOST'])      # comes from not-env
print(os.environ['DB_PASSWORD'])  # comes from not-env
```

Or using the direct import:

```python
# main.py
from not_env_sdk import initialize

initialize()

print(os.environ['DB_HOST'])
```

### 3. Run Your Application

```bash
python main.py
```

**Expected output:**

```
localhost
secret123
```

**If this works correctly, you should see:**

* Variable values from not-env printed
* Your application can now use `os.environ` as usual

## Usage Examples

### Basic Usage

```python
# app.py
import not_env_sdk.register
import os

db_host = os.environ['DB_HOST']
db_port = os.environ['DB_PORT']

print(f"Connecting to {db_host}:{db_port}")
```

### Using os.getenv()

The SDK also works with `os.getenv()`:

```python
# app.py
import not_env_sdk.register
import os

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')  # with default

print(f"Connecting to {db_host}:{db_port}")
```

### Programmatic Initialization

You can also initialize the SDK programmatically:

```python
# app.py
from not_env_sdk import initialize

initialize(
    url="https://not-env.example.com",
    api_key="your-key-here"
)

import os
print(os.environ['DB_HOST'])
```

### With Django

For Django applications, import in your `settings.py`:

```python
# settings.py
import not_env_sdk.register
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}
```

### With Flask

For Flask applications, import at the top of your application file:

```python
# app.py
import not_env_sdk.register
import os
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['DATABASE_URL'] = os.environ['DATABASE_URL']
```

## How It Works

1. **On Import**: The SDK immediately:
   * Reads `NOT_ENV_URL` and `NOT_ENV_API_KEY` from `os.environ`
   * Fetches all variables from the `/variables` endpoint
   * Replaces `os.environ` with a custom dict-like object
2. **os.environ Behavior**:
   * `NOT_ENV_URL` and `NOT_ENV_API_KEY`: Returned from original OS environment
   * Other keys: Returned from not-env if they exist, otherwise raise `KeyError`
   * Setting variables: Prevented (hermetic behavior)
3. **Transparent Integration**: Existing code using `os.environ['FOO']` or `os.getenv('FOO')` works without changes.

## Environment Variables

### Required

* `NOT_ENV_URL`: Backend URL (e.g., `https://not-env.example.com`)
* `NOT_ENV_API_KEY`: ENV_READ_ONLY or ENV_ADMIN API key

### Example

```bash
export NOT_ENV_URL="https://not-env.example.com"
export NOT_ENV_API_KEY="dGVzdF9lbnZfcmVhZG9ubHlfa2V5X2hlcmU..."
```

## Example Application

Create a simple example:

```python
# example.py
import not_env_sdk.register
import os

print("Database Configuration:")
print(f"  Host: {os.environ['DB_HOST']}")
print(f"  Port: {os.environ['DB_PORT']}")
print(f"  Name: {os.environ['DB_NAME']}")

# Use variables as normal
connection_string = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
print(f"Connection: {connection_string}")
```

Run it:

```bash
NOT_ENV_URL="https://not-env.example.com" \
NOT_ENV_API_KEY="your-key" \
python example.py
```

**Expected output:**

```
Database Configuration:
  Host: localhost
  Port: 5432
  Name: myapp
Connection: postgresql://user:pass@localhost:5432/myapp
```

**If this works correctly, you should see:**

* All variables printed from not-env
* Connection string built using those variables
* No errors or KeyError exceptions (assuming variables exist in not-env)

## Error Handling

### Missing Environment Variables

If `NOT_ENV_URL` or `NOT_ENV_API_KEY` are missing:

```
ValueError: NOT_ENV_URL environment variable is required
```

**Solution:** Set both environment variables before running your application.

### Backend Unreachable

If the backend is unreachable:

```
RuntimeError: Request failed: getaddrinfo ENOTFOUND not-env.example.com
```

**Solution:** Check the `NOT_ENV_URL` and ensure the backend is running and accessible.

### Invalid API Key

If the API key is invalid:

```
RuntimeError: Failed to fetch variables: 401 - Unauthorized
```

**Solution:** Verify your `NOT_ENV_API_KEY` is correct and not revoked.

### Initialization Failure

If initialization fails, the SDK will:

* Print an error to stderr
* Exit the process with code 1

This ensures your application doesn't run with incorrect configuration.

## Behavior Details

### Hermetic Behavior

The SDK provides hermetic behavior:

* Variables not in not-env raise `KeyError` when accessed via `os.environ['KEY']`
* Variables not in not-env return `None` (or default) when accessed via `os.getenv('KEY')`
* No fallback to OS environment variables (except `NOT_ENV_URL` and `NOT_ENV_API_KEY`)
* Prevents setting variables at runtime

### Preserved Variables

These variables are always preserved from OS environment:

* `NOT_ENV_URL`
* `NOT_ENV_API_KEY`

### Variable Access

* `os.environ['KEY']`: Returns value from not-env if exists, otherwise raises `KeyError`
* `os.getenv('KEY')`: Returns value from not-env if exists, otherwise returns `None`
* `os.getenv('KEY', default)`: Returns value from not-env if exists, otherwise returns `default`
* `os.environ['KEY'] = value`: Prevented (raises `RuntimeError`)
* `'KEY' in os.environ`: Returns `True` only if key exists in not-env (or preserved vars)
* `list(os.environ.keys())`: Returns only keys from not-env (plus preserved vars)

## Compatibility

### Supported Runtimes

* Python 3.8+
* Django
* Flask
* FastAPI
* Any Python application

### Not Supported

* Python 2.x (end of life)
* Python 3.7 and earlier

## Integration with CLI

The SDK works alongside the CLI:

1. **CLI**: Use `not-env env set` to load variables into your shell
2. **SDK**: Use `import not_env_sdk.register` to load variables in Python

Both can be used together - CLI for shell scripts, SDK for Python applications.

## Troubleshooting

### Variables raise KeyError

* Check that variables exist in not-env: `not-env var list`
* Verify you're using the correct API key (ENV_READ_ONLY or ENV_ADMIN)
* Ensure the SDK is imported before any code that uses `os.environ`
* Use `os.getenv('KEY')` instead of `os.environ['KEY']` if you want `None` instead of `KeyError`

### SDK not loading

* Ensure the SDK is imported at the very top of your entry file
* Check that `NOT_ENV_URL` and `NOT_ENV_API_KEY` are set
* Verify the backend is accessible

### Performance concerns

* Variables are fetched once at startup
* No caching beyond the initial fetch
* Network request happens synchronously during import

## Security Notes

* **API Keys**: Store `NOT_ENV_API_KEY` securely. Never commit it to version control.
* **HTTPS**: Always use HTTPS for `NOT_ENV_URL` in production.
* **Read-Only Keys**: Use ENV_READ_ONLY keys when possible for better security.

## Next Steps

* Set up your backend
* Use the CLI to manage variables
* Integrate the SDK into your Python applications

## License

MIT License

