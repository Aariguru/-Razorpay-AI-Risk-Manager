"""Generate a JSONL file of safe, reproducible demo transactions."""

import argparse
import json
from pathlib import Path

from app.services.synthetic_data import generate_transactions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("../../data/synthetic/transactions.jsonl"))
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = generate_transactions(args.count, args.seed)
    with args.output.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record.model_dump(mode="json")) + "\n")
    print(f"Wrote {len(records)} synthetic transactions to {args.output}")


if __name__ == "__main__":
    main()
