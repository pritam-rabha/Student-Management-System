"""Load demonstration data into the data directory on request.

    python scripts/seed_sample_data.py            # only if no data file exists
    python scripts/seed_sample_data.py --force    # replace, keeping a backup

The application never does the destructive variant on its own.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from config import load_config  # noqa: E402
from app.storage.json_store import JsonFileStore  # noqa: E402
from app.storage.seed import force_seed, seed_if_missing  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true",
                        help="replace the existing data file (a timestamped backup is kept)")
    args = parser.parse_args()

    config = load_config()
    store = JsonFileStore(config["DATA_DIR"] / "students.json")

    if args.force:
        count, backup = force_seed(store, config["SAMPLE_DATA_FILE"])
        print(f"Wrote {count} sample records to {store.path}.")
        if backup:
            print(f"Previous data kept at {backup}.")
    elif seed_if_missing(store, config["SAMPLE_DATA_FILE"]):
        print(f"Created {store.path} with sample records.")
    else:
        print(f"{store.path} already exists; nothing changed. Use --force to replace it.")


if __name__ == "__main__":
    main()
