import os

CONNECTOR_BASE_URL = os.getenv('CONNECTOR_BASE_URL', 'http://127.0.0.1:5173')
CONNECTOR_BUILD_DIR = os.getenv('CONNECTOR_BUILD_DIR')
CONNECTOR_SITE_ID = os.getenv('CONNECTOR_SITE_ID', 'apotheon-dev')
CONNECTOR_SOURCE = os.getenv('CONNECTOR_SOURCE', 'crawl')
CHROMA_DIR = os.getenv('CONNECTOR_CHROMA_DIR', './.chroma')
READ_TOKEN = os.getenv('CONNECTOR_READ_TOKEN', 'read-token')
ADMIN_TOKEN = os.getenv('CONNECTOR_ADMIN_TOKEN', 'admin-token')
