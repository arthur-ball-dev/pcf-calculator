#!/usr/bin/env python3
"""Verify no PROXY emission factors remain in the database."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.database.connection import db_context
from backend.models import EmissionFactor

with db_context() as s:
    proxy_count = s.query(EmissionFactor).filter(EmissionFactor.data_source == "PROXY").count()
    print(f"PROXY emission factors: {proxy_count}")
    null_ef = s.execute(text("SELECT COUNT(*) FROM bill_of_materials WHERE emission_factor_id IS NULL")).scalar()
    print(f"BOM entries with NULL emission_factor_id: {null_ef}")
    total = s.query(EmissionFactor).count()
    print(f"Total emission factors: {total}")
