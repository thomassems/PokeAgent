"""Validate and optionally upload the canonical strategy corpus to Pinecone."""

import argparse
import json
import os
from typing import Any

from pinecone import Pinecone

from data.strategy import STRATEGY_RECORDS, StrategyRecord

INDEX_NAME = "pokeagent-strategy"
NAMESPACE = "strategy-v1"
EMBED_MODEL = "llama-text-embed-v2"


def pinecone_record(record: StrategyRecord) -> dict[str, Any]:
    """Flatten one canonical record, excluding repository-only licensing data."""
    payload = record.model_dump(
        mode="json",
        exclude={"discovery_urls", "license"},
        exclude_none=True,
    )
    payload["_id"] = payload.pop("id")
    return payload


def ensure_index(client: Pinecone, index_name: str) -> None:
    if client.has_index(index_name):
        return
    client.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model": EMBED_MODEL,
            "field_map": {"text": "chunk_text"},
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create the index if needed and upload the validated records.",
    )
    args = parser.parse_args()
    records = [pinecone_record(record) for record in STRATEGY_RECORDS]

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
    ensure_index(client, INDEX_NAME)
    client.Index(INDEX_NAME).upsert_records(namespace=NAMESPACE, records=records)
    print(f"Uploaded {len(records)} records to {INDEX_NAME}/{NAMESPACE}.")


if __name__ == "__main__":
    main()
