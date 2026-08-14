"""`elastic-display` command-line entrypoint (used over SSH)."""

from __future__ import annotations

import argparse
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="elastic-display",
        description="Administer the Elastic Security desk display.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="Interactive setup wizard (writes the config file)")
    sub.add_parser("test", help="Re-test connectivity of each data source")
    run = sub.add_parser("run", help="Run the display backend in the foreground")
    run.add_argument("--host", default=None, help="Override [server].host")
    run.add_argument("--port", type=int, default=None, help="Override [server].port")

    args = parser.parse_args(argv)

    if args.command == "setup":
        from .wizard import run_setup

        return run_setup()
    if args.command == "test":
        from .wizard import run_test

        return run_test()
    if args.command == "run":
        import uvicorn

        from .config import load_config
        from .main import create_app

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        cfg = load_config()
        uvicorn.run(
            create_app(cfg),
            host=args.host or cfg.server.host,
            port=args.port or cfg.server.port,
            # The SSE stream never ends on its own; without a deadline a
            # SIGTERM (systemctl restart) would hang on the open connection.
            timeout_graceful_shutdown=5,
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
