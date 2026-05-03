import os
import hashlib
import json
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get('DATABASE_URL', '')


class Row:
    """Supports row['key'] and row[index] access — mirrors sqlite3.Row behaviour."""
    def __init__(self, data):
        self._data = dict(data)
        self._keys = list(data.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[self._keys[key]]
        return self._data[key]

    def __iter__(self):
        return iter(self._data.values())

    def keys(self):
        return self._keys

    def get(self, key, default=None):
        return self._data.get(key, default)


class PGCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        row = self._cursor.fetchone()
        return Row(row) if row else None

    def fetchall(self):
        return [Row(r) for r in (self._cursor.fetchall() or [])]


class PGConnection:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params if params is not None else ())
        return PGCursor(cur)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return PGConnection(conn)


def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    tables = [
        """CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL DEFAULT 'staff',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS participants (
            id SERIAL PRIMARY KEY,
            participant_id TEXT UNIQUE,
            full_name TEXT NOT NULL,
            ndis_number TEXT,
            date_of_birth TEXT,
            plan_start TEXT,
            plan_end TEXT,
            support_type TEXT,
            primary_diagnosis TEXT,
            plan_manager TEXT,
            total_funding REAL,
            core_funding REAL,
            cb_funding REAL,
            sc_funding REAL,
            iscp_funding REAL,
            support_coordinator TEXT,
            emergency_contact TEXT,
            emergency_phone TEXT,
            language TEXT,
            interpreter_required TEXT,
            status TEXT DEFAULT 'Active',
            sw_schedule TEXT,
            goals_summary TEXT,
            risk_flag TEXT,
            next_review_date TEXT,
            plan_status TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS income_entries (
            id SERIAL PRIMARY KEY,
            entry_date TEXT NOT NULL,
            month_period TEXT,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            support_category TEXT,
            ndis_item_code TEXT,
            invoice_number TEXT,
            amount REAL NOT NULL,
            plan_manager_type TEXT,
            notes TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS expenditure_entries (
            id SERIAL PRIMARY KEY,
            entry_date TEXT NOT NULL,
            month_period TEXT,
            category TEXT,
            sub_category TEXT,
            description TEXT,
            supplier TEXT,
            amount REAL NOT NULL,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            invoice_number TEXT,
            payment_method TEXT,
            notes TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS staff_costs (
            id SERIAL PRIMARY KEY,
            pay_date TEXT NOT NULL,
            month_period TEXT,
            staff_name TEXT NOT NULL,
            role TEXT,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            shift_type TEXT,
            schedule_notes TEXT,
            qty_hours REAL,
            ndis_rate REAL,
            ndis_revenue REAL,
            actual_rate REAL,
            actual_wage REAL,
            super_amount REAL,
            total_cost REAL,
            margin REAL,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS petty_cash (
            id SERIAL PRIMARY KEY,
            entry_date TEXT NOT NULL,
            description TEXT NOT NULL,
            expense REAL DEFAULT 0,
            cash_in REAL DEFAULT 0,
            balance REAL,
            location TEXT,
            receipt_obtained TEXT DEFAULT 'No',
            notes TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            task_id TEXT UNIQUE,
            title TEXT NOT NULL,
            priority TEXT,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            assigned_to TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Not Started',
            completed_date TEXT,
            notes TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS communications (
            id SERIAL PRIMARY KEY,
            comm_date TEXT NOT NULL,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            contact_type TEXT,
            person_assigned TEXT,
            organisation_role TEXT,
            reason TEXT,
            outcome TEXT,
            follow_up TEXT,
            follow_up_date TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS issues (
            id SERIAL PRIMARY KEY,
            issue_id TEXT UNIQUE,
            issue_date TEXT NOT NULL,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            description TEXT NOT NULL,
            risk_level TEXT,
            action_required TEXT,
            assigned_to TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Open',
            resolution TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS plan_reviews (
            id SERIAL PRIMARY KEY,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            next_review TEXT,
            prep_start TEXT,
            progress_reports TEXT,
            allied_health TEXT,
            family_feedback TEXT,
            sw_reports TEXT,
            review_meeting TEXT,
            outcome TEXT,
            prep_status TEXT,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS goals (
            id SERIAL PRIMARY KEY,
            participant_id INTEGER REFERENCES participants(id),
            participant_name TEXT,
            goal_area TEXT,
            goal_description TEXT,
            current_progress TEXT,
            evidence TEXT,
            barriers TEXT,
            actions_to_improve TEXT,
            status TEXT DEFAULT 'In Progress',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            username TEXT,
            action TEXT,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            month_period TEXT NOT NULL,
            category TEXT NOT NULL,
            sub_category TEXT,
            description TEXT,
            participant_name TEXT,
            budget_amount REAL NOT NULL DEFAULT 0,
            notes TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS petty_cash_settings (
            id SERIAL PRIMARY KEY,
            month_period TEXT UNIQUE NOT NULL,
            opening_balance REAL DEFAULT 0,
            monthly_topup REAL DEFAULT 500,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
    ]

    for stmt in tables:
        cur.execute(stmt)

    # Income breakdown columns (safe to run on existing tables)
    for col in [
        "ALTER TABLE income_entries ADD COLUMN IF NOT EXISTS amount_sil REAL DEFAULT 0",
        "ALTER TABLE income_entries ADD COLUMN IF NOT EXISTS amount_is_support REAL DEFAULT 0",
        "ALTER TABLE income_entries ADD COLUMN IF NOT EXISTS amount_allied_health REAL DEFAULT 0",
        "ALTER TABLE income_entries ADD COLUMN IF NOT EXISTS amount_other REAL DEFAULT 0",
    ]:
        cur.execute(col)

    admin_hash = hashlib.sha256("Admin@123".encode()).hexdigest()
    cur.execute("""
        INSERT INTO users (username, password_hash, full_name, role)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ('admin', admin_hash, 'Administrator', 'admin'))

    staff_hash = hashlib.sha256("Staff@123".encode()).hexdigest()
    cur.execute("""
        INSERT INTO users (username, password_hash, full_name, role)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ('staff', staff_hash, 'Staff User', 'staff'))

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialised successfully.")


def log_audit(user_id, username, action, table_name, record_id=None, old_vals=None, new_vals=None, ip=None):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_log (user_id, username, action, table_name, record_id, old_values, new_values, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, username, action, table_name, record_id,
        json.dumps(old_vals) if old_vals else None,
        json.dumps(new_vals) if new_vals else None,
        ip
    ))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == '__main__':
    init_db()
