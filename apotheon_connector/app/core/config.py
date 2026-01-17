import os

# Target website base URL to crawl/index.
# Prefer CONNECTOR_TARGET_URL; fall back to legacy CONNECTOR_BASE_URL; default to Vite port.
CONNECTOR_BASE_URL = (
    os.getenv('CONNECTOR_TARGET_URL')
    or os.getenv('CONNECTOR_BASE_URL')
    or 'http://127.0.0.1:5173'
)

CONNECTOR_BUILD_DIR = os.getenv('CONNECTOR_BUILD_DIR')
CONNECTOR_SITE_ID = os.getenv('CONNECTOR_SITE_ID', 'apotheon-dev')
CONNECTOR_SOURCE = os.getenv('CONNECTOR_SOURCE', 'crawl')
CHROMA_DIR = os.getenv('CONNECTOR_CHROMA_DIR', './.chroma')

# Token configuration
# If specific tokens are not provided, default to CONNECTOR_TOKEN when present.
READ_TOKEN = os.getenv('CONNECTOR_READ_TOKEN') or os.getenv('CONNECTOR_TOKEN') or 'read-token'
ADMIN_TOKEN = os.getenv('CONNECTOR_ADMIN_TOKEN') or os.getenv('CONNECTOR_TOKEN') or 'admin-token'
