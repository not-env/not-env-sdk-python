#!/usr/bin/env python3
"""
Example usage of not-env-sdk-python

This example demonstrates how to use the SDK to fetch environment variables
from not-env and use them in your application.
"""

import not_env_sdk.register
import os

print("Database Configuration:")
print(f"  Host: {os.environ.get('DB_HOST', 'not set')}")
print(f"  Port: {os.environ.get('DB_PORT', 'not set')}")
print(f"  Name: {os.environ.get('DB_NAME', 'not set')}")

# Use variables as normal
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

if all([db_user, db_password, db_host, db_port, db_name]):
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"Connection: {connection_string}")
else:
    print("Some database variables are missing")

