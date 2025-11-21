# not-env-sdk-python

Python SDK that fetches environment variables from not-env and transparently overrides `os.environ`.

## 30-Second Example

```bash
export NOT_ENV_URL="http://localhost:1212"
export NOT_ENV_API_KEY="your-env-read-only-key"
```
```python
import not_env_sdk.register
import os
print(os.environ['DB_HOST'])  # That's it!
```

## Quick Reference

| Task | Command/Code |
|------|--------------|
| **Install** | `pip install not-env-sdk` |
| **Set environment variables** | `export NOT_ENV_URL="..."`<br>`export NOT_ENV_API_KEY="..."` |
| **Import SDK** | `import not_env_sdk.register` |
| **Use variables** | `os.environ['DB_HOST']` or `os.getenv('DB_HOST')` |
| **Programmatic init** | `from not_env_sdk import initialize`<br>`initialize(url="...", api_key="...")` |

## Overview

The SDK:
- Fetches all variables from not-env at startup (synchronously)
- Monkey-patches `os.environ` to return not-env values
- Preserves `NOT_ENV_URL` and `NOT_ENV_API_KEY` from OS environment
- Makes other keys raise `KeyError` if not in not-env (hermetic behavior)
- Works transparently with existing code

## Prerequisites

- Python 3.8 or later
- A running not-env backend
- An ENV_READ_ONLY or ENV_ADMIN API key

## Installation

```bash
pip install not-env-sdk
```

## Quick Start

### 1. Set Environment Variables

```bash
export NOT_ENV_URL="https://not-env.example.com"
export NOT_ENV_API_KEY="your-env-read-only-key-here"
```

### 2. Import the SDK

Import at the very beginning of your application (before any code that uses `os.environ`):

```python
# main.py
import not_env_sdk.register
import os

# Now os.environ is patched
print(os.environ['DB_HOST'])      # comes from not-env
print(os.environ['DB_PASSWORD'])  # comes from not-env
```

Or using programmatic initialization:

```python
from not_env_sdk import initialize

initialize(url="https://not-env.example.com", api_key="your-key")
import os
print(os.environ['DB_HOST'])
```

### 3. Run Your Application

```bash
python main.py
```

## Usage Examples

### Basic Usage

```python
import not_env_sdk.register
import os

db_host = os.environ['DB_HOST']
db_port = os.environ['DB_PORT']
print(f"Connecting to {db_host}:{db_port}")
```

### Using os.getenv()

```python
import not_env_sdk.register
import os

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')  # with default
```

### With Django

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

```python
# app.py
import not_env_sdk.register
import os
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['DATABASE_URL'] = os.environ['DATABASE_URL']
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NOT_ENV_URL` | Yes | Backend URL | `https://not-env.example.com` |
| `NOT_ENV_API_KEY` | Yes | ENV_READ_ONLY or ENV_ADMIN API key | `dGVzdF9lbnZfcmVhZG9ubHlfa2V5X2hlcmU...` |

## How It Works

1. **On Import**: The SDK immediately:
   - Reads `NOT_ENV_URL` and `NOT_ENV_API_KEY` from `os.environ`
   - Fetches all variables from the `/variables` endpoint synchronously
   - Replaces `os.environ` with a custom dict-like object

2. **os.environ Behavior**:
   - `NOT_ENV_URL` and `NOT_ENV_API_KEY`: Returned from original OS environment
   - Other keys: Returned from not-env if they exist, otherwise raise `KeyError`
   - Setting variables: Prevented (hermetic behavior)

3. **Transparent Integration**: Existing code using `os.environ['FOO']` or `os.getenv('FOO')` works without changes.

## Error Handling

**Missing environment variables:**
- Error: `NOT_ENV_URL environment variable is required`
- Solution: Set both `NOT_ENV_URL` and `NOT_ENV_API_KEY`

**Backend unreachable:**
- Error: `Request failed: getaddrinfo ENOTFOUND...`
- Solution: Check `NOT_ENV_URL` and ensure backend is running

**Invalid API key:**
- Error: `Failed to fetch variables: 401 - Unauthorized`
- Solution: Verify `NOT_ENV_API_KEY` is correct

**Initialization failure:**
- SDK prints error to stderr and exits with code 1
- Ensures application doesn't run with incorrect configuration

## Behavior Details

### Hermetic Behavior

- Variables not in not-env raise `KeyError` when accessed via `os.environ['KEY']`
- Variables not in not-env return `None` (or default) when accessed via `os.getenv('KEY')`
- No fallback to OS environment variables (except `NOT_ENV_URL` and `NOT_ENV_API_KEY`)
- Prevents setting variables at runtime

### Preserved Variables

These variables are always preserved from OS environment:
- `NOT_ENV_URL`
- `NOT_ENV_API_KEY`

### Variable Access

- `os.environ['KEY']`: Returns value from not-env if exists, otherwise raises `KeyError`
- `os.getenv('KEY')`: Returns value from not-env if exists, otherwise returns `None`
- `os.getenv('KEY', default)`: Returns value from not-env if exists, otherwise returns `default`
- `os.environ['KEY'] = value`: Prevented (raises `RuntimeError`)
- `'KEY' in os.environ`: Returns `True` only if key exists in not-env (or preserved vars)
- `list(os.environ.keys())`: Returns only keys from not-env (plus preserved vars)

## Compatibility

**Supported:**
- Python 3.8+
- Django
- Flask
- FastAPI
- Any Python application

**Not Supported:**
- Python 2.x (end of life)
- Python 3.7 and earlier

## Troubleshooting

**Where do I get ENV_READ_ONLY key?**
- From `not-env env import` or `not-env env create` output. Look for the "ENV_READ_ONLY key:" line.
- This is the key you set as `NOT_ENV_API_KEY` environment variable.

**Variables raise KeyError:**
- Check that variables exist in not-env: `not-env var list`
- Verify you're using the correct API key (ENV_READ_ONLY or ENV_ADMIN)
- Ensure the SDK is imported before any code that uses `os.environ`
- Use `os.getenv('KEY')` instead of `os.environ['KEY']` if you want `None` instead of `KeyError`

**SDK not loading:**
- Ensure the SDK is imported at the very top of your entry file
- Check that `NOT_ENV_URL` and `NOT_ENV_API_KEY` are set
- Verify the backend is accessible

**Performance concerns:**
- Variables are fetched once at startup (synchronously)
- No caching beyond the initial fetch
- Network request happens synchronously during import

## Security Notes

- **API Keys**: Store `NOT_ENV_API_KEY` securely. Never commit it to version control.
- **HTTPS**: Always use HTTPS for `NOT_ENV_URL` in production.
- **Read-Only Keys**: Use ENV_READ_ONLY keys when possible for better security.

## Next Steps

- Set up your [backend](../../not-env-backend/README.md)
- Use the [CLI](../../not-env-cli/README.md) to manage variables
- Integrate the SDK into your Python applications
