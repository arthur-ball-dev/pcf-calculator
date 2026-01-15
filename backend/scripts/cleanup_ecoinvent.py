#!/usr/bin/env python3
"""Remove Ecoinvent references from database.

Ecoinvent requires a commercial license. This script replaces
Ecoinvent data source references with EPA.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import SessionLocal
from backend.models import EmissionFactor
from sqlalchemy import update


def cleanup_ecoinvent():
    """Replace Ecoinvent data source with EPA."""
    with SessionLocal() as db:
        # Count before
        before = db.query(EmissionFactor).filter(
            EmissionFactor.data_source == 'Ecoinvent'
        ).count()
        print(f"Ecoinvent emission factors found: {before}")

        if before == 0:
            print("No Ecoinvent data to clean up.")
            return

        # Update Ecoinvent to EPA
        result = db.execute(
            update(EmissionFactor)
            .where(EmissionFactor.data_source == 'Ecoinvent')
            .values(data_source='EPA')
        )
        db.commit()
        print(f"Updated {result.rowcount} emission factors from Ecoinvent to EPA")

        # Verify
        after = db.query(EmissionFactor).filter(
            EmissionFactor.data_source == 'Ecoinvent'
        ).count()
        print(f"Remaining Ecoinvent records: {after}")

        if after == 0:
            print("✓ Ecoinvent cleanup complete!")
        else:
            print("⚠ Warning: Some Ecoinvent records remain")


if __name__ == "__main__":
    cleanup_ecoinvent()
