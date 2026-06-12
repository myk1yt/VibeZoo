#!/usr/bin/env python3
"""
DEPRECATED — Use REAL Crow server at C:\Users\k1yt\OneDrive\Projects\Crow Memory\

This file is kept as a redirect to avoid breaking existing references.
The REAL Crow server (crow_mcp_server.py in the Crow Memory project) now serves
the same REST API contract via add_rest_routes() on port 9020.

Bridge components (crow_client.py, auto_fixer.py) connect via config.CROW_URL
which defaults to http://localhost:9020 — no changes needed.
"""
import sys

if __name__ == "__main__":
    print(
        "WARNING: This FAKE Crow server is deprecated. "
        "Use the REAL Crow server at C:\\Users\\k1yt\\OneDrive\\Projects\\Crow Memory\\ "
        "(start_crow_sse.bat) which provides the same REST API on port 9020.",
        file=sys.stderr,
    )
    sys.exit(0)
