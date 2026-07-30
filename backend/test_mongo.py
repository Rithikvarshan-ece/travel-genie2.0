import sys
import os

# Run from backend directory so .env is found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError

settings = get_settings()
uri = settings.mongodb_url

print(f"MONGODB_URL loaded: {bool(uri)}", flush=True)
if uri:
    # Mask password for display
    display = uri[:30] + "..." if len(uri) > 30 else uri
    print(f"URI prefix: {display}", flush=True)

if not uri:
    print("ERROR: MONGODB_URL is not set in .env", flush=True)
    sys.exit(1)

print("Attempting PyMongo connection...", flush=True)
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    result = client.admin.command("ping")
    print(f"PING OK: {result}", flush=True)
    db = client[settings.mongodb_database]
    # Test write
    db.connection_test.insert_one({"test": True})
    db.connection_test.delete_many({"test": True})
    print(f"READ/WRITE OK on database: {settings.mongodb_database}", flush=True)
    client.close()
    print("MongoDB connection VERIFIED", flush=True)
except ConfigurationError as e:
    print(f"CONFIG ERROR (bad URI): {e}", flush=True)
    sys.exit(1)
except ServerSelectionTimeoutError as e:
    print(f"TIMEOUT ERROR (cannot reach server): {e}", flush=True)
    sys.exit(1)
except ConnectionFailure as e:
    print(f"CONNECTION FAILURE: {e}", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"UNEXPECTED ERROR [{type(e).__name__}]: {e}", flush=True)
    sys.exit(1)
