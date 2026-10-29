"""Start the local application with explicit transport limits."""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    port = parser.parse_args().port
    if not 1024 <= port <= 65535:
        parser.error("Choose a port between 1024 and 65535.")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port,
                proxy_headers=False, server_header=False, limit_concurrency=32,
                timeout_keep_alive=5, h11_max_incomplete_event_size=16 * 1024,
                access_log=False)


if __name__ == "__main__":
    main()
