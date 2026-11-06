PRAGMA foreign_keys = ON;

-- 1. Companies being monitored
CREATE TABLE IF NOT EXISTS companies (
    company_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE,
    portal_url   TEXT
);

-- 2. Job titles found at each company (each title stored once)
CREATE TABLE IF NOT EXISTS vacancies (
    vacancy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    title      TEXT NOT NULL,
    first_seen TEXT NOT NULL,   -- 'YYYY-MM-DD HH:MM:SS', set once when first found
    last_seen  TEXT NOT NULL,   -- updated every run the title is still listed
    is_active  INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE (company_id, title)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_active
ON vacancies(is_active);