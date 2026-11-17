"""Validate and optionally upload the GO guides corpus to Pinecone.

Dry-run by default. `--apply` upserts into namespace `go-guides-v1` on the
existing strategy index. It does not create an index and it does not write
`strategy-v1`.
"""

import argparse
import json
import os
from typing import Any

from pinecone import Pinecone

from data.go_guides import GO_GUIDE_RECORDS, GoGuideRecord

INDEX_NAME = "pokeagent-strategy"
NAMESPACE = "go-guides-v1"


def pinecone_record(record: GoGuideRecord) -> dict[str, Any]:
    """Flatten one guide, leaving licensing notes in the repository."""
    payload = record.model_dump(
        mode="json",
        exclude={"discovery_urls", "license"},
        exclude_none=True,
    )
    payload["_id"] = payload.pop("id")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upload the validated records into the GO guides namespace.",
    )
    args = parser.parse_args()
    records = [pinecone_record(record) for record in GO_GUIDE_RECORDS]

    if not args.apply:
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "index": INDEX_NAME,
                    "namespace": NAMESPACE,
                    "record_count": len(records),
                    "record_ids": [record["_id"] for record in records],
                },
                indent=2,
            )
        )
        return

    if not os.environ.get("PINECONE_API_KEY"):
        raise SystemExit("PINECONE_API_KEY is required with --apply.")

    client = Pinecone()
    if not client.has_index(INDEX_NAME):
        raise SystemExit(
            f"Index {INDEX_NAME} is missing. This script does not create it."
        )
    client.Index(INDEX_NAME).upsert_records(namespace=NAMESPACE, records=records)
    print(f"Uploaded {len(records)} records to {INDEX_NAME}/{NAMESPACE}.")


if __name__ == "__main__":
    main()
