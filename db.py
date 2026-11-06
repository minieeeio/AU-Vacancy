import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent      # folder where db.py lives
DB_PATH = BASE_DIR / "database" / "vacancies.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_connection(db_path=DB_PATH, schema_path=SCHEMA_PATH):
    """Open the database and make sure the tables exist (safe to call every time)."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")   # must be set on every connection
    conn.executescript(Path(schema_path).read_text())   # CREATE ... IF NOT EXISTS
    conn.commit()
    return conn


def init_db(db_path=DB_PATH, schema_path=SCHEMA_PATH):
    """Create the database file and tables explicitly."""
    get_connection(db_path, schema_path).close()


def save_result(conn, name, result):
    """
    Save one company's scrape result.

    name   : company name, e.g. "ANZ"
    result : the inner dict from your scraper, {"count", "url", "titles"},
             or None if the scrape failed.

    Returns a dict like {"status": "ok", "new": 2, "removed": 1, "total": 10}
    or {"status": "skipped"} when the scrape failed / is unsupported.
    """
    # Failed or unsupported scrape: change nothing, so jobs are not wrongly marked removed.
    if not result or result.get("titles") is None:
        return {"status": "skipped"}

    ts = now()
    url = result.get("url")

    # 1. get or create the company
    row = conn.execute(
        "SELECT company_id FROM companies WHERE company_name = ?", (name,)
    ).fetchone()
    if row is None:
        company_id = conn.execute(
            "INSERT INTO companies (company_name, portal_url) VALUES (?, ?)",
            (name, url),
        ).lastrowid
    else:
        company_id = row[0]
        if url:
            conn.execute(
                "UPDATE companies SET portal_url = ? WHERE company_id = ?",
                (url, company_id),
            )

    # 2. insert new titles / refresh existing ones
    titles = list(dict.fromkeys(t.strip() for t in result["titles"] if t and t.strip()))
    new_count = 0
    for title in titles:
        row = conn.execute(
            "SELECT vacancy_id FROM vacancies WHERE company_id = ? AND title = ?",
            (company_id, title),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO vacancies (company_id, title, first_seen, last_seen) "
                "VALUES (?, ?, ?, ?)",
                (company_id, title, ts, ts),
            )
            new_count += 1
        else:
            # existing (or came back after being removed)
            conn.execute(
                "UPDATE vacancies SET last_seen = ?, is_active = 1 WHERE vacancy_id = ?",
                (ts, row[0]),
            )

    # 3. active titles that are missing from today's list = removed
    removed_count = 0
    active = conn.execute(
        "SELECT vacancy_id, title FROM vacancies WHERE company_id = ? AND is_active = 1",
        (company_id,),
    ).fetchall()
    current = set(titles)
    for vacancy_id, title in active:
        if title not in current:
            conn.execute(
                "UPDATE vacancies SET is_active = 0 WHERE vacancy_id = ?", (vacancy_id,)
            )
            removed_count += 1

    conn.commit()
    return {"status": "ok", "new": new_count, "removed": removed_count, "total": len(titles)}


def build_report(conn, new_since=None):
    """
    Build the email text from all active vacancies.

    new_since : a 'YYYY-MM-DD HH:MM:SS' string. Titles first seen at or after it
                get a [NEW] tag. Pass the time your run started.
    """
    companies = conn.execute(
        """
        SELECT c.company_id, c.company_name, c.portal_url
        FROM companies c
        WHERE EXISTS (SELECT 1 FROM vacancies v
                      WHERE v.company_id = c.company_id AND v.is_active = 1)
        ORDER BY c.company_name
        """
    ).fetchall()

    total = 0
    blocks = []
    for company_id, name, url in companies:
        jobs = conn.execute(
            "SELECT title, first_seen FROM vacancies "
            "WHERE company_id = ? AND is_active = 1 ORDER BY title",
            (company_id,),
        ).fetchall()
        total += len(jobs)
        lines = [f"{name}: {url}", ""]
        for i, (title, first_seen) in enumerate(jobs, 1):
            tag = "  [NEW]" if new_since and first_seen >= new_since else ""
            lines.append(f"{i}. {title}{tag}")
        blocks.append("\n".join(lines))

    return f"Total job openings: {total}\n\n" + "\n\n".join(blocks)


if __name__ == "__main__":
    init_db()
    print("Database ready.")