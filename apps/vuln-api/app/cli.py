"""
CLI entry point for chimera-api.

Usage:
    chimera-api [--host HOST] [--port PORT] [--debug] [--demo-mode {full,strict}]
"""

import argparse
import os


def main():
    parser = argparse.ArgumentParser(
        prog="chimera-api",
        description="Chimera API — multi-domain WAF testing server",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8880, help="Port (default: 8880)")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    parser.add_argument(
        "--demo-mode",
        choices=["full", "strict"],
        default=None,
        help="Demo mode: 'full' enables vulnerabilities, 'strict' disables them",
    )

    args = parser.parse_args()

    # Set env vars before importing the app factory
    if args.demo_mode:
        os.environ["DEMO_MODE"] = args.demo_mode

    from app import create_app

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
