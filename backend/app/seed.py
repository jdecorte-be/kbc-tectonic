"""Generate and persist synthetic clients without overwriting existing evidence."""
from __future__ import annotations

import argparse
import sys

from app.banking import BankData
from app.crud import BankRepository


def _client_count(value: str) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("count must be an integer from 1 to 10000") from None
    if not 1 <= count <= 10000:
        raise argparse.ArgumentTypeError("count must be an integer from 1 to 10000")
    return count


def _summary(action: str, counts: dict[str, int]) -> str:
    return (f"{action} {counts['clients']:,} clients, {counts['accounts']:,} accounts, "
            f"{counts['transactions']:,} transactions and {counts['products']:,} products.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed synthetic banking data. Existing customer evidence is preserved.")
    parser.add_argument("--count", type=_client_count, default=None, metavar="N",
                        help="generated clients on an empty database, plus one limited-history example (default: 1000; maximum: 10000)")
    arguments = parser.parse_args(argv)
    requested = arguments.count if arguments.count is not None else 1000
    repository = None
    status = 0
    try:
        # Keep settings validation inside the error boundary; never expose a database URL.
        from app.config import Settings
        configuration = Settings()
        repository = BankRepository(configuration.DATABASE_URL)
        if repository.is_seeded():
            counts = repository.counts()
            print(_summary("Reused", counts))
            existing_generated = counts["clients"] - int(repository.has_client("SYN-SPARSE"))
            if arguments.count is not None and existing_generated != requested:
                print(f"Requested {requested:,} generated clients; the database already contains {existing_generated:,}. "
                      "Use a fresh DATABASE_URL to generate a different population. Existing data was preserved.", file=sys.stderr)
                status = 2
        else:
            BankData(generated_count=requested, products_path=configuration.PRODUCTS_PATH, repository=repository)
            print(_summary("Seeded", repository.counts()))
            print(f"Population: {requested:,} generated clients plus one limited-history example. No AI calls were made.")
    except Exception:
        print("Seeding failed. Check DATABASE_URL, database availability and the configured product catalogue. "
              "Existing data was preserved.", file=sys.stderr)
        status = 1
    finally:
        if repository is not None:
            try:
                repository.close()
            except Exception:
                print("Database cleanup failed. Check database availability.", file=sys.stderr)
                status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
