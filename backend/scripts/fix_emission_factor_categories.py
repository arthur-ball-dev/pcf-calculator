"""
Script to fix emission factor categories in the database
All factors currently have category=null, this assigns proper categories
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from backend.config import settings

# Category mappings based on activity names
CATEGORY_MAPPINGS = {
    # Materials
    'cotton': 'material',
    'polyester': 'material',
    'plastic_pet': 'material',
    'plastic_abs': 'material',
    'plastic_hdpe': 'material',
    'aluminum': 'material',
    'steel': 'material',
    'glass': 'material',
    'paper': 'material',
    'rubber': 'material',
    'copper': 'material',
    'wood': 'material',
    'leather': 'material',
    'nylon': 'material',
    'ceramic': 'material',
    'foam': 'material',

    # Energy
    'electricity_us': 'energy',

    # Transport
    'transport_truck': 'transport',
    'transport_ship': 'transport',

    # Other
    'water': 'other',
}

def fix_categories():
    """Update emission factor categories in database"""

    # Create database engine
    engine = create_engine(settings.database_url)

    print("Fixing emission factor categories...")
    print("-" * 50)

    with engine.connect() as conn:
        # Get all emission factors
        result = conn.execute(text("SELECT id, activity_name, category FROM emission_factors"))
        factors = result.fetchall()

        print(f"Found {len(factors)} emission factors")

        updated_count = 0
        for factor_id, activity_name, current_category in factors:
            # Get the correct category
            correct_category = CATEGORY_MAPPINGS.get(activity_name)

            if correct_category and current_category != correct_category:
                # Update the factor
                conn.execute(
                    text("UPDATE emission_factors SET category = :category WHERE id = :id"),
                    {"category": correct_category, "id": factor_id}
                )
                print(f"✓ Updated {activity_name}: null → {correct_category}")
                updated_count += 1
            elif not correct_category:
                print(f"⚠ No category mapping for: {activity_name}")

        # Commit the transaction
        conn.commit()

        print("-" * 50)
        print(f"Updated {updated_count} emission factors")

        # Verify the update
        print("\nVerifying updates...")
        result = conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM emission_factors
            GROUP BY category
        """))

        for category, count in result.fetchall():
            print(f"  {category or 'null'}: {count}")

    print("\n✅ Emission factor categories fixed!")

if __name__ == "__main__":
    fix_categories()
