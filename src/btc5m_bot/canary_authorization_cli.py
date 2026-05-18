from __future__ import annotations

import argparse
from pathlib import Path

from .canary_authorization import DEFAULT_AUTHORIZATION_PACKET, write_canary_authorization_packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_AUTHORIZATION_PACKET)
    args = parser.parse_args()
    print(write_canary_authorization_packet(output_path=args.output))


if __name__ == "__main__":
    main()
