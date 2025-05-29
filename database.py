import sqlite3

DATABASE_NAME = 'event_management.db'

def initialize_database():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        event_date TEXT,
        event_location TEXT,
        has_tickets BOOLEAN DEFAULT 0
    )
    """)

    # Add has_tickets column if it doesn't exist (for backward compatibility)
    try:
        cursor.execute("PRAGMA table_info(events)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'has_tickets' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN has_tickets BOOLEAN DEFAULT 0")
            print("Added 'has_tickets' column to 'events' table.")
    except sqlite3.Error as e:
        print(f"Error checking/altering events table: {e}")
    # --- End column check/add ---

    # Users Table (Head and Members)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Head', 'Member')), -- 'Head' or 'Member'
        full_name TEXT
    )
    """)
    # Ensure at least one Head user exists (e.g., default admin)
    # In a real app, provide a secure way to set the initial password
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                   ('admin', 'pbkdf2:sha256:600000$YXHqdM3aKImwPnpL$3c7a77852a4b7517e08a8c0f9a6f4c7e01e853e1c753143f175968b30c7f4b55', 'Head', 'Default Admin')) # Example hash for password 'admin'

    # Tasks Table (Predefined Tasks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT NOT NULL UNIQUE,
        description TEXT -- Add column for custom task descriptions
    )
    """)
    
    # --- Add description column if it doesn't exist (for backward compatibility) ---
    try:
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'description' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN description TEXT")
            print("Added 'description' column to 'tasks' table.")
    except sqlite3.Error as e:
        print(f"Error checking/altering tasks table: {e}")
    # --- End column check/add ---
        
    # Add predefined tasks (ensure description is NULL or empty for these initially)
    tasks = [
        ('Vendor Management', None),
        ('Guest List Management', None),
        ('Logistics Management', None),
        ('Schedule Coordination', None),
        ('Team Chat', None)
    ]
    # Use INSERT OR IGNORE to avoid errors if tasks already exist
    cursor.executemany("INSERT OR IGNORE INTO tasks (task_name, description) VALUES (?, ?)", tasks)


    # Assignments Table (Link Users, Events, Tasks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Assigned', -- 'Assigned', 'In Progress', 'Completed'
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
        FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE,
        UNIQUE(user_id, event_id, task_id) -- Ensure a user isn't assigned the same task twice for the same event
    )
    """)

    # Vendor Management Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        service_type TEXT,
        contact_person TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        status TEXT DEFAULT 'Pending', -- e.g., 'Pending', 'Contacted', 'Booked', 'Rejected'
        notes TEXT,
        FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
    )
    """)

    # Guest List Management Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guests (
        guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        rsvp_status TEXT DEFAULT 'Pending', -- e.g., 'Pending', 'Attending', 'Declined', 'Maybe'
        notes TEXT,
        FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
    )
    """)

    # Logistics Management Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logistics (
        logistics_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        category TEXT, -- e.g., 'AV Equipment', 'Furniture', 'Catering Supplies'
        quantity INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Required', -- e.g., 'Required', 'Sourced', 'Delivered', 'Setup', 'Returned'
        supplier TEXT,
        cost REAL,
        notes TEXT,
        FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
    )
    """)

    # Schedule Coordination Table (Example 4th Task)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            location TEXT,
            responsible_person TEXT,
            status TEXT DEFAULT 'Planned', -- e.g., 'Planned', 'Confirmed', 'Ongoing', 'Completed'
            notes TEXT,
            FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
        )
        """)

    # Chat Messages Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)

    # Tickets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        ticket_code TEXT NOT NULL UNIQUE,
        user_name TEXT NOT NULL,
        user_class TEXT,
        user_roll_number TEXT,
        user_address TEXT,
        booking_timestamp TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
    )
    """)

    # Add Ticket Management to predefined tasks if it doesn't exist
    cursor.execute("INSERT OR IGNORE INTO tasks (task_name, description) VALUES (?, ?)",
                  ('Ticket Management', 'Manage event tickets and attendee information'))

    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized successfully.")

if __name__ == "__main__":
    initialize_database() 