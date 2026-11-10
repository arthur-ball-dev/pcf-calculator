"""
Empty-database helper for tests that need no pre-existing rows.

The shared ``db_session`` fixture (conftest.py) runs each test inside a
PostgreSQL transaction that is rolled back afterwards, but the test database
holds the test-mode catalog. Tests that count rows or seed from scratch call
``empty_all_tables`` first: it deletes every row inside that same transaction,
so the catalog is back once the test ends.

DELETE is used rather than TRUNCATE: TRUNCATE takes an ACCESS EXCLUSIVE lock
that would block any other connection the code under test opens.
"""

from sqlalchemy.orm import Session

from backend.models import Base


def empty_all_tables(session: Session) -> None:
    """Delete every row from every mapped table, children first, and commit.

    The commit releases the fixture's savepoint, so a later rollback inside the
    test (after an expected IntegrityError, say) cannot bring the rows back.
    """
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
