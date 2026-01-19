#!/usr/bin/env python3
"""
Download External Data Script.

TASK-DATA-P9: Download and cache EPA/DEFRA emission factor files locally.

This script downloads emission factor files from EPA and DEFRA official sources
and saves them locally for use by the data ingestion system.

Files downloaded:
- EPA GHG Emission Factors Hub (fuels): data/epa/ghg-emission-factors-hub-2024.xlsx
- EPA eGRID (electricity): data/epa/egrid2022_data.xlsx
- DEFRA Conversion Factors: data/defra/ghg-conversion-factors-2024.xlsx

Usage:
    python backend/scripts/download_external_data.py
    python backend/scripts/download_external_data.py --force  # Re-download existing files
    python backend/scripts/download_external_data.py --source epa  # Only EPA
    python backend/scripts/download_external_data.py --source defra  # Only DEFRA
"""

import argparse
import sys
from pathlib import Path

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# File configurations with official URLs
FILES = {
    "epa_fuels": {
        "url": "https://www.epa.gov/system/files/documents/2024-02/ghg-emission-factors-hub-2024.xlsx",
        "local_path": "data/epa/ghg-emission-factors-hub-2024.xlsx",
        "description": "EPA GHG Emission Factors Hub (fuels)",
    },
    "epa_egrid": {
        "url": "https://www.epa.gov/system/files/documents/2024-01/egrid2022_data.xlsx",
        "local_path": "data/epa/egrid2022_data.xlsx",
        "description": "EPA eGRID (electricity by subregion)",
    },
    "defra": {
        "url": (
            "https://assets.publishing.service.gov.uk/media/6722567487df31a87d8c497e/"
            "ghg-conversion-factors-2024-full_set__for_advanced_users__v1_1.xlsx"
        ),
        "local_path": "data/defra/ghg-conversion-factors-2024.xlsx",
        "description": "DEFRA UK Conversion Factors",
    },
}


def download_file(url: str, local_path: Path, description: str) -> bool:
    """
    Download a file from URL to local path.

    Args:
        url: URL to download from
        local_path: Path to save the file
        description: Human-readable description for logging

    Returns:
        True if successful, False otherwise
    """
    print(f"  Downloading: {description}")
    print(f"  URL: {url}")
    print(f"  To: {local_path}")

    try:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(local_path, "wb") as f:
                f.write(response.content)

            size_mb = len(response.content) / (1024 * 1024)
            print(f"  Downloaded: {size_mb:.2f} MB")
            return True

    except httpx.HTTPStatusError as e:
        print(f"  ERROR: HTTP {e.response.status_code} - {e.response.reason_phrase}")
        return False
    except httpx.ConnectError as e:
        print(f"  ERROR: Connection failed - {e}")
        return False
    except Exception as e:
        print(f"  ERROR: {type(e).__name__} - {e}")
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download EPA/DEFRA emission factor files"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if files exist",
    )
    parser.add_argument(
        "--source",
        choices=["epa", "defra", "all"],
        default="all",
        help="Which data source to download (default: all)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PCF Calculator - External Data Download")
    print("=" * 60)
    print()

    # Filter files based on source argument
    files_to_download = {}
    for key, config in FILES.items():
        if args.source == "all":
            files_to_download[key] = config
        elif args.source == "epa" and key.startswith("epa"):
            files_to_download[key] = config
        elif args.source == "defra" and key == "defra":
            files_to_download[key] = config

    success_count = 0
    skip_count = 0
    fail_count = 0

    for key, config in files_to_download.items():
        print(f"\n[{key.upper()}]")
        local_path = project_root / config["local_path"]

        # Check if file already exists
        if local_path.exists() and not args.force:
            size_mb = local_path.stat().st_size / (1024 * 1024)
            print(f"  Already exists: {local_path}")
            print(f"  Size: {size_mb:.2f} MB")
            print("  Use --force to re-download")
            skip_count += 1
            continue

        if download_file(config["url"], local_path, config["description"]):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Downloaded: {success_count}")
    print(f"  Skipped (existing): {skip_count}")
    print(f"  Failed: {fail_count}")

    if fail_count > 0:
        print()
        print("WARNING: Some downloads failed. Check your network connection.")
        print("You may need to manually download the files or try again later.")
        return 1

    if success_count > 0 or skip_count > 0:
        print()
        print("Files are ready for use by load_production_data.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
