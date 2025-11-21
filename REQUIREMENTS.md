# not-env-sdk-python Requirements

## Summary

not-env-sdk-python is a Python SDK that fetches environment variables from not-env and transparently overrides `os.environ`. Key features:

- **Synchronous Loading**: Variables fetched synchronously during import (blocks until complete)
- **Transparent Integration**: Existing code using `os.environ['FOO']` works unchanged
- **Hermetic Behavior**: Only variables from not-env are available (no OS env fallback)
- **Preserved Variables**: `NOT_ENV_URL` and `NOT_ENV_API_KEY` preserved from OS environment
- **Dict-like Interface**: Uses custom dict-like class to intercept `os.environ` access
- **Error Handling**: Exits process on initialization failure (prevents running with invalid config)

## Quick Reference

| Requirement | Specification |
|-------------|---------------|
| **Python Version** | 3.8 or later |
| **HTTP Client** | Python built-in `urllib.request` module |
| **Initialization** | Synchronous (blocks during import) |
| **Timeout** | 30 seconds for HTTP requests |
| **Error Behavior** | Exits process with code 1 on failure |

## Detailed Requirements

See appendices below for complete functional and non-functional requirements.

---

## Appendix A: Functional Requirements

### FR1: Initialization

**FR1.1:** The SDK must read `NOT_ENV_URL` and `NOT_ENV_API_KEY` from `os.environ` on import.

**FR1.2:** If `NOT_ENV_URL` is missing, the SDK must raise a `ValueError`: `NOT_ENV_URL environment variable is required`.

**FR1.3:** If `NOT_ENV_API_KEY` is missing, the SDK must raise a `ValueError`: `NOT_ENV_API_KEY environment variable is required`.

**FR1.4:** The SDK must fetch all variables from the backend `/variables` endpoint using HTTPS (or HTTP for localhost).

**FR1.5:** The SDK must use the `Authorization: Bearer <API_KEY>` header for authentication.

**FR1.6:** If the fetch fails, the SDK must:
- Print error to stderr
- Exit the process with code 1

**FR1.7:** The SDK must build a dictionary of variables (key → value) from the response.

**FR1.8:** Initialization must happen synchronously during import (before any other code runs).

### FR2: os.environ Patching

**FR2.1:** The SDK must create a custom dict-like class (`PatchedEnviron`) that replaces `os.environ`.

**FR2.2:** For `NOT_ENV_URL` and `NOT_ENV_API_KEY`:
- Must return values from original OS environment
- Must allow reading these values
- Must preserve them regardless of not-env state

**FR2.3:** For any other key:
- If key exists in not-env → return its value
- If key does not exist in not-env → raise `KeyError`
- Must not fall back to OS environment variables (hermetic behavior)

**FR2.4:** Setting variables (except `NOT_ENV_URL` and `NOT_ENV_API_KEY`) must be prevented:
- `os.environ['KEY'] = value` must raise `RuntimeError`
- Variables cannot be modified at runtime

**FR2.5:** The `in` operator must work correctly:
- `'KEY' in os.environ` returns `True` only if key exists in not-env
- `'NOT_ENV_URL' in os.environ` returns `True` if set in OS env
- `'NOT_ENV_API_KEY' in os.environ` returns `True` if set in OS env

**FR2.6:** `os.environ.keys()` must return:
- All keys from not-env
- `NOT_ENV_URL` if present in OS env
- `NOT_ENV_API_KEY` if present in OS env

**FR2.7:** `os.environ.get(key, default)` must return the value if exists, otherwise return `default`.

**FR2.8:** `os.environ.copy()` must return a dictionary with all not-env variables plus preserved keys.

**FR2.9:** Mutating methods (`pop`, `popitem`, `update`, `clear`) must raise `RuntimeError`.

### FR3: Variable Fetching

**FR3.1:** The SDK must make an HTTPS GET request to `{NOT_ENV_URL}/variables`.

**FR3.2:** The request must include:
- `Authorization: Bearer {NOT_ENV_API_KEY}` header
- `Content-Type: application/json` header

**FR3.3:** The SDK must parse the JSON response:
```json
{
  "variables": [
    { "key": "KEY1", "value": "value1" },
    { "key": "KEY2", "value": "value2" }
  ]
}
```

**FR3.4:** The SDK must handle HTTP errors:
- 401 Unauthorized: Invalid API key
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Backend endpoint not found
- 500 Server Error: Backend error
- Network errors: Connection failures

**FR3.5:** All errors must include descriptive messages.

### FR4: Error Handling

**FR4.1:** Missing environment variables must raise clear `ValueError` exceptions with variable names.

**FR4.2:** Network errors must include error details (hostname, port, etc.).

**FR4.3:** HTTP errors must include status code and error message from backend.

**FR4.4:** Parse errors must indicate JSON parsing failure.

**FR4.5:** All errors must be printed to stderr before process exit.

### FR5: Usage Patterns

**FR5.1:** The SDK must support import via register module:
```python
import not_env_sdk.register
```

**FR5.2:** The SDK must work when imported at the top of entry files.

**FR5.3:** The SDK must work when imported before any code that uses `os.environ`.

**FR5.4:** The SDK must support manual initialization:
```python
from not_env_sdk.sdk import initialize
initialize(url="http://localhost:1212", api_key="...")
```

## Appendix B: Non-Functional Requirements

### NFR1: Performance

**NFR1.1:** Variable fetching must complete within 30 seconds (timeout).

**NFR1.2:** `os.environ` access after initialization must be O(1) (dictionary lookup).

**NFR1.3:** Initialization must not block for more than 30 seconds.

### NFR2: Security

**NFR2.1:** The SDK must use HTTPS for all backend communication (or HTTP for localhost).

**NFR2.2:** API keys must never be logged or exposed in error messages.

**NFR2.3:** The SDK must validate URL format before making requests.

### NFR3: Compatibility

**NFR3.1:** The SDK must work with Python 3.8+.

**NFR3.2:** The SDK must work with:
- Django
- Flask
- FastAPI
- Any Python application using `os.environ`

**NFR3.3:** The SDK must not require any build step for end users (pure Python).

### NFR4: Reliability

**NFR4.1:** The SDK must handle network timeouts gracefully.

**NFR4.2:** The SDK must handle malformed JSON responses gracefully.

**NFR4.3:** The SDK must not crash the process silently (always exit with error on failure).

### NFR5: Observability

**NFR5.1:** Errors must include sufficient context (URL, status code, error message).

**NFR5.2:** The SDK must not log successful operations (silent on success).

## Appendix C: Implementation Constraints

### IC1: Technology Stack

**IC1.1:** Language: Python 3.8+.

**IC1.2:** HTTP Client: Python built-in `urllib.request` module (synchronous).

**IC1.3:** Dependencies: None (pure Python, uses only standard library).

### IC2: Module System

**IC2.1:** Must support Python import system.

**IC2.2:** Main entry point: `src/not_env_sdk/register.py`.

**IC2.3:** Core implementation: `src/not_env_sdk/sdk.py`.

### IC3: os.environ Behavior

**IC3.1:** Must replace `os.environ` with custom dict-like class (`PatchedEnviron`).

**IC3.2:** Must preserve original `os.environ` for `NOT_ENV_URL` and `NOT_ENV_API_KEY`.

**IC3.3:** Must implement all dict-like methods (`__getitem__`, `__setitem__`, `__contains__`, `keys`, `values`, `items`, `get`, `copy`, etc.).

### IC4: Error Behavior

**IC4.1:** Initialization errors must exit the process (cannot continue with invalid state).

**IC4.2:** Runtime errors (variable access) must raise `KeyError` (not return `None`).

## Appendix D: Expected Behaviors

### EB1: Successful Initialization

1. SDK is imported: `import not_env_sdk.register`
2. SDK reads `NOT_ENV_URL` and `NOT_ENV_API_KEY`
3. SDK makes HTTPS GET to `{NOT_ENV_URL}/variables` synchronously
4. SDK receives JSON response with variables
5. SDK builds dictionary of variables
6. SDK creates `PatchedEnviron` and replaces `os.environ`
7. Application code can use `os.environ['KEY']` and get values from not-env

### EB2: Variable Access

1. Code accesses `os.environ['DB_HOST']`
2. `PatchedEnviron.__getitem__` checks if `DB_HOST` is preserved → no
3. `PatchedEnviron.__getitem__` checks if `DB_HOST` exists in not-env dict → yes
4. `PatchedEnviron.__getitem__` returns value from not-env dict
5. Code receives value: `"localhost"`

### EB3: Missing Variable

1. Code accesses `os.environ['NONEXISTENT']`
2. `PatchedEnviron.__getitem__` checks if key is preserved → no
3. `PatchedEnviron.__getitem__` checks if key exists in not-env dict → no
4. `PatchedEnviron.__getitem__` raises `KeyError`
5. Code receives `KeyError` exception (hermetic behavior)

### EB4: Preserved Variables

1. Code accesses `os.environ['NOT_ENV_URL']`
2. `PatchedEnviron.__getitem__` checks if key is preserved → yes
3. `PatchedEnviron.__getitem__` returns value from original OS environment
4. Code receives original value

### EB5: Initialization Failure

1. SDK is imported
2. `NOT_ENV_URL` is missing
3. SDK raises `ValueError`: `NOT_ENV_URL environment variable is required`
4. Error is printed to stderr
5. Process exits with code 1
6. Application does not start

## Appendix E: Testing Scenarios

### TS1: Basic Usage

- Set `NOT_ENV_URL` and `NOT_ENV_API_KEY`
- Import SDK
- Access `os.environ['KEY']` that exists in not-env
- Verify value is returned

### TS2: Missing Variable

- Set environment variables
- Import SDK
- Access `os.environ['KEY']` that doesn't exist in not-env
- Verify `KeyError` is raised

### TS3: Preserved Variables

- Set `NOT_ENV_URL` in OS environment
- Import SDK
- Access `os.environ['NOT_ENV_URL']`
- Verify original value is returned

### TS4: Initialization Failure

- Don't set `NOT_ENV_URL`
- Import SDK
- Verify `ValueError` is raised and process exits

### TS5: Network Error

- Set invalid `NOT_ENV_URL`
- Import SDK
- Verify network error is caught and process exits

### TS6: Invalid API Key

- Set valid URL but invalid API key
- Import SDK
- Verify 401 error is caught and process exits

### TS7: Dict-like Methods

- Import SDK
- Verify `os.environ.keys()` returns all keys
- Verify `os.environ.values()` returns all values
- Verify `os.environ.items()` returns all key-value pairs
- Verify `os.environ.get('KEY', 'default')` works correctly
- Verify `os.environ.copy()` returns a dictionary

### TS8: Mutating Methods

- Import SDK
- Verify `os.environ['KEY'] = 'value'` raises `RuntimeError`
- Verify `os.environ.pop('KEY')` raises `RuntimeError`
- Verify `os.environ.update({})` raises `RuntimeError`
- Verify `os.environ.clear()` raises `RuntimeError`

