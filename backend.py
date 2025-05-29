import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import datetime
import uuid
import random
import string

DATABASE_NAME = 'event_management.db'

def get_db_connection(timeout=10.0):
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME, timeout=timeout)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return conn

# --- User Management --- 

def create_user(username, password, role, full_name, college=None):
    """Creates a new user (Head or Member) with optional college association."""
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Insert the basic user info
        cursor.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                       (username, password_hash, role, full_name))
        user_id = cursor.lastrowid
        
        # If college information is provided, store it in user_metadata table
        if college:
            try:
                cursor.execute("INSERT INTO user_metadata (user_id, key, value) VALUES (?, ?, ?)",
                           (user_id, 'college', college))
            except sqlite3.OperationalError:
                # If user_metadata table doesn't exist, create it first
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_metadata (
                        metadata_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        UNIQUE (user_id, key)
                    )
                """)
                # Now try inserting again
                cursor.execute("INSERT INTO user_metadata (user_id, key, value) VALUES (?, ?, ?)",
                           (user_id, 'college', college))
        
        # Commit the transaction
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return None # Username already exists

def verify_user(username, password):
    """Verifies user credentials and returns user info if valid."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if user_metadata table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_metadata'")
        metadata_exists = cursor.fetchone() is not None
        
        # Get basic user info
        cursor.execute("SELECT user_id, username, password_hash, role, full_name FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password_hash'], password):
            conn.close()
            return None
            
        user_dict = dict(user)
        
        # Get college info if metadata table exists
        if metadata_exists:
            cursor.execute("SELECT value FROM user_metadata WHERE user_id = ? AND key = 'college'", (user_dict['user_id'],))
            college_row = cursor.fetchone()
            user_dict['college'] = college_row['value'] if college_row else None
        
        conn.close()
        return user_dict
    
    except sqlite3.Error as e:
        print(f"Error verifying user: {e}")
        conn.close()
        return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user_metadata table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_metadata'")
        metadata_exists = cursor.fetchone() is not None
        
        # Get basic user info
        cursor.execute("SELECT user_id, username, role, full_name FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return None
            
        user_dict = dict(user)
        
        # Get college info if metadata table exists
        if metadata_exists:
            cursor.execute("SELECT value FROM user_metadata WHERE user_id = ? AND key = 'college'", (user_id,))
            college_row = cursor.fetchone()
            user_dict['college'] = college_row['value'] if college_row else None
        
        conn.close()
        return user_dict
    
    except sqlite3.Error as e:
        print(f"Error fetching user: {e}")
        conn.close()
        return None

def get_users_with_colleges():
    """Retrieves all users with their associated college information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user_metadata table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_metadata'")
        if not cursor.fetchone():
            # If table doesn't exist, return users without college info
            cursor.execute("SELECT user_id, username, role, full_name FROM users")
            users = cursor.fetchall()
            users_with_colleges = [dict(user) for user in users]
            for user in users_with_colleges:
                user['college'] = None
            return users_with_colleges
        
        # If table exists, join users with metadata to get college info
        cursor.execute("""
            SELECT u.user_id, u.username, u.role, u.full_name,
                   m.value as college
            FROM users u
            LEFT JOIN user_metadata m ON u.user_id = m.user_id AND m.key = 'college'
        """)
        
        users = cursor.fetchall()
        conn.close()
        return [dict(user) for user in users]
    
    except sqlite3.Error as e:
        print(f"Error fetching users with colleges: {e}")
        conn.close()
        return []

def get_all_members():
    """Retrieves all users with the 'Member' role, including college info."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user_metadata table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_metadata'")
        metadata_exists = cursor.fetchone() is not None
        
        if metadata_exists:
            # Join with metadata to get college info
            cursor.execute("""
                SELECT u.user_id, u.username, u.full_name, m.value as college
                FROM users u
                LEFT JOIN user_metadata m ON u.user_id = m.user_id AND m.key = 'college'
                WHERE u.role = 'Member'
            """)
        else:
            # Get basic member info without college
            cursor.execute("SELECT user_id, username, full_name FROM users WHERE role = 'Member'")
            
        members = cursor.fetchall()
        members_list = [dict(member) for member in members]
        
        # Ensure college field exists in all records
        if not metadata_exists:
            for member in members_list:
                member['college'] = None
                
        conn.close()
        return members_list
        
    except sqlite3.Error as e:
        print(f"Error fetching members: {e}")
        conn.close()
        return []

# --- Event Management --- 

def create_event(name, date, location, has_tickets=False, college=None):
    """Creates a new event with optional college association."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First, add the event to the events table
        cursor.execute("INSERT INTO events (event_name, event_date, event_location, has_tickets) VALUES (?, ?, ?, ?)",
                       (name, date, location, 1 if has_tickets else 0))
        event_id = cursor.lastrowid
        
        # If college information is provided, store it in the event_metadata table
        if college:
            try:
                cursor.execute("INSERT INTO event_metadata (event_id, key, value) VALUES (?, ?, ?)",
                           (event_id, 'college', college))
            except sqlite3.OperationalError:
                # If event_metadata table doesn't exist, create it first
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS event_metadata (
                        metadata_id INTEGER PRIMARY KEY,
                        event_id INTEGER NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT,
                        FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE,
                        UNIQUE (event_id, key)
                    )
                """)
                # Now try inserting again
                cursor.execute("INSERT INTO event_metadata (event_id, key, value) VALUES (?, ?, ?)",
                           (event_id, 'college', college))
                
        conn.commit()
        conn.close()
        return event_id
    except sqlite3.IntegrityError as e:
        print(f"Error creating event: {e}")
        conn.close()
        return None # Event name might be unique

def get_events_with_colleges():
    """Retrieves all events with their associated college information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if event_metadata table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_metadata'")
        if not cursor.fetchone():
            # If table doesn't exist, return events without college info
            cursor.execute("SELECT event_id, event_name, event_date, event_location, has_tickets FROM events")
            events = cursor.fetchall()
            events_with_colleges = [dict(event) for event in events]
            for event in events_with_colleges:
                event['college'] = None
            return events_with_colleges
        
        # If table exists, join events with metadata to get college info
        cursor.execute("""
            SELECT e.event_id, e.event_name, e.event_date, e.event_location, e.has_tickets,
                   m.value as college
            FROM events e
            LEFT JOIN event_metadata m ON e.event_id = m.event_id AND m.key = 'college'
            ORDER BY e.event_date DESC
        """)
        
        events = cursor.fetchall()
        conn.close()
        return [dict(event) for event in events]
    
    except sqlite3.Error as e:
        print(f"Error fetching events with colleges: {e}")
        conn.close()
        return []

def get_event_by_id(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if event_metadata table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_metadata'")
        metadata_exists = cursor.fetchone() is not None
        
        # Get basic event info
        cursor.execute("SELECT event_id, event_name, event_date, event_location, has_tickets FROM events WHERE event_id = ?", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            conn.close()
            return None
            
        event_dict = dict(event)
        
        # Get college info if metadata table exists
        if metadata_exists:
            cursor.execute("SELECT value FROM event_metadata WHERE event_id = ? AND key = 'college'", (event_id,))
            college_row = cursor.fetchone()
            event_dict['college'] = college_row['value'] if college_row else None
        
        conn.close()
        return event_dict
    
    except sqlite3.Error as e:
        print(f"Error fetching event: {e}")
        conn.close()
        return None

def get_all_events():
    """Retrieves all events with their college information if available."""
    return get_events_with_colleges()

def delete_event(event_id):
    """Deletes an event from the database based on its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Delete from event_metadata first if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_metadata'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM event_metadata WHERE event_id = ?", (event_id,))
        
        # Now delete the event
        cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
        deleted = cursor.rowcount > 0 # Check if any row was affected
        
        # Commit the transaction
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error during event deletion: {e}")
        conn.rollback()
        deleted = False
    finally:
        conn.close()
    return deleted

# --- Task & Assignment Management ---

def get_all_tasks():
    """Retrieves all predefined tasks."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT task_id, task_name FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return [dict(task) for task in tasks]

def get_task_by_id(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT task_id, task_name FROM tasks WHERE task_id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    return dict(task) if task else None

def assign_custom_task(user_id, event_id, task_name, task_description=None):
    """Creates a custom task and assigns it to a user for a specific event.
    
    Args:
        user_id (int): The ID of the user to assign the task to
        event_id (int): The ID of the event for which the task is being assigned
        task_name (str): The name of the custom task
        task_description (str, optional): Description of the custom task
        
    Returns:
        int or None: The assignment ID if successful, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Check if a task with this name already exists
        cursor.execute("SELECT task_id FROM tasks WHERE task_name = ?", (task_name,))
        existing_task = cursor.fetchone()
        
        if existing_task:
            # Use existing task
            task_id = existing_task['task_id']
        else:
            # Create new task, including the description
            cursor.execute("INSERT INTO tasks (task_name, description) VALUES (?, ?)", (task_name, task_description))
            task_id = cursor.lastrowid
        
        # Now assign the task
        cursor.execute("INSERT INTO assignments (user_id, event_id, task_id, status) VALUES (?, ?, ?, 'Assigned')",
                   (user_id, event_id, task_id))
        assignment_id = cursor.lastrowid
        
        # Commit the transaction
        conn.commit()
        return assignment_id
        
    except sqlite3.IntegrityError as e:
        # This could happen if the user is already assigned this task for this event
        # or if there's another constraint violation
        print(f"Database integrity error: {e}")
        conn.rollback()
        return None
    except Exception as e:
        print(f"Error in assign_custom_task: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def assign_task(user_id, event_id, task_id):
    """Assigns a task to a user for a specific event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO assignments (user_id, event_id, task_id, status) VALUES (?, ?, ?, 'Assigned')",
                       (user_id, event_id, task_id))
        conn.commit()
        assignment_id = cursor.lastrowid
        conn.close()
        return assignment_id
    except sqlite3.IntegrityError:
        # Handle cases where the assignment already exists or foreign key constraints fail
        conn.close()
        return None

def get_user_assignments(user_id, event_id=None):
    """Retrieves tasks assigned to a specific user, optionally filtered by event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT a.assignment_id, a.event_id, e.event_name, 
               a.task_id, t.task_name, t.description,
               a.status
        FROM assignments a
        JOIN events e ON a.event_id = e.event_id
        JOIN tasks t ON a.task_id = t.task_id
        WHERE a.user_id = ?
    """
    params = [user_id]
    if event_id:
        query += " AND a.event_id = ?"
        params.append(event_id)
    query += " ORDER BY e.event_date DESC, t.task_name"
    cursor.execute(query, params)
    assignments = cursor.fetchall()
    conn.close()
    return [dict(assignment) for assignment in assignments]

def get_event_assignments(event_id):
     """Retrieves all assignments for a specific event, including user and task details."""
     conn = get_db_connection()
     cursor = conn.cursor()
     query = """
         SELECT
             a.assignment_id,
             a.user_id, u.username, u.full_name,
             a.task_id, t.task_name,
             a.status,
             t.description
         FROM assignments a
         JOIN users u ON a.user_id = u.user_id
         JOIN tasks t ON a.task_id = t.task_id
         WHERE a.event_id = ?
         ORDER BY u.full_name, t.task_name
     """
     cursor.execute(query, (event_id,))
     assignments = cursor.fetchall()
     conn.close()
     return [dict(assignment) for assignment in assignments]

def update_assignment_status(assignment_id, new_status):
    """Updates the status of a specific task assignment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE assignments SET status = ? WHERE assignment_id = ?", (new_status, assignment_id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    return updated_rows > 0

# --- Task-Specific Data Management --- 

# Vendor Management
def add_vendor(event_id, name, service_type, contact_person, contact_email, contact_phone, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vendors (event_id, name, service_type, contact_person, contact_email, contact_phone, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (event_id, name, service_type, contact_person, contact_email, contact_phone, notes))
    conn.commit()
    vendor_id = cursor.lastrowid
    conn.close()
    return vendor_id

def get_vendors_for_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendors WHERE event_id = ? ORDER BY name", (event_id,))
    vendors = cursor.fetchall()
    conn.close()
    return [dict(v) for v in vendors]

def update_vendor(vendor_id, name, service_type, contact_person, contact_email, contact_phone, status, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE vendors SET name=?, service_type=?, contact_person=?, contact_email=?, contact_phone=?, status=?, notes=?
        WHERE vendor_id=?
        """, (name, service_type, contact_person, contact_email, contact_phone, status, notes, vendor_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_vendor(vendor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendors WHERE vendor_id=?", (vendor_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# Guest List Management
def add_guest(event_id, name, email, phone, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guests (event_id, name, email, phone, notes, rsvp_status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
    """, (event_id, name, email, phone, notes))
    conn.commit()
    guest_id = cursor.lastrowid
    conn.close()
    return guest_id

def get_guests_for_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guests WHERE event_id = ? ORDER BY name", (event_id,))
    guests = cursor.fetchall()
    conn.close()
    return [dict(g) for g in guests]

def update_guest(guest_id, name, email, phone, rsvp_status, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE guests SET name=?, email=?, phone=?, rsvp_status=?, notes=?
        WHERE guest_id=?
        """, (name, email, phone, rsvp_status, notes, guest_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_guest(guest_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guests WHERE guest_id=?", (guest_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# Logistics Management
def add_logistics_item(event_id, item_name, category, quantity, supplier, cost, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logistics (event_id, item_name, category, quantity, status, supplier, cost, notes)
        VALUES (?, ?, ?, ?, 'Required', ?, ?, ?)
    """, (event_id, item_name, category, quantity, supplier, cost, notes))
    conn.commit()
    logistics_id = cursor.lastrowid
    conn.close()
    return logistics_id

def get_logistics_for_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logistics WHERE event_id = ? ORDER BY category, item_name", (event_id,))
    logistics = cursor.fetchall()
    conn.close()
    return [dict(l) for l in logistics]

def update_logistics_item(logistics_id, item_name, category, quantity, status, supplier, cost, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE logistics SET item_name=?, category=?, quantity=?, status=?, supplier=?, cost=?, notes=?
        WHERE logistics_id=?
        """, (item_name, category, quantity, status, supplier, cost, notes, logistics_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_logistics_item(logistics_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logistics WHERE logistics_id=?", (logistics_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# Schedule Coordination
def add_schedule_item(event_id, item_name, start_time, end_time, location, responsible_person, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO schedule_items (event_id, item_name, start_time, end_time, location, responsible_person, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, 'Planned', ?)
    """, (event_id, item_name, start_time, end_time, location, responsible_person, notes))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id

def get_schedule_for_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Assuming start_time is stored in a sortable format (e.g., 'YYYY-MM-DD HH:MM')
    cursor.execute("SELECT * FROM schedule_items WHERE event_id = ? ORDER BY start_time, item_name", (event_id,))
    schedule = cursor.fetchall()
    conn.close()
    return [dict(s) for s in schedule]

def update_schedule_item(item_id, item_name, start_time, end_time, location, responsible_person, status, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE schedule_items SET item_name=?, start_time=?, end_time=?, location=?, responsible_person=?, status=?, notes=?
        WHERE item_id=?
        """, (item_name, start_time, end_time, location, responsible_person, status, notes, item_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_schedule_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedule_items WHERE item_id=?", (item_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# --- Reporting --- 

def get_guest_report(event_id):
    """Generates a report on guest RSVP status for an event."""
    guests = get_guests_for_event(event_id)
    if not guests:
        return pd.DataFrame(columns=['RSVP Status', 'Count'])
    df = pd.DataFrame(guests)
    report = df['rsvp_status'].value_counts().reset_index()
    report.columns = ['RSVP Status', 'Count']
    return report

def get_logistics_report(event_id):
    """Generates a report on logistics status and cost for an event."""
    logistics = get_logistics_for_event(event_id)
    if not logistics:
        return pd.DataFrame(columns=['Status', 'Count', 'Total Cost'])
    df = pd.DataFrame(logistics)
    # Ensure 'cost' is numeric, coercing errors to NaN and filling with 0
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce').fillna(0)

    report = df.groupby('status').agg(
        Count=('logistics_id', 'size'),
        Total_Cost=('cost', 'sum')
    ).reset_index()
    report.columns = ['Status', 'Count', 'Total Cost']
    return report

# --- Chat Functions ---

def add_chat_message(event_id, user_id, message_text):
    """
    Adds a message to the team chat for an event.
    
    Args:
        event_id (int): The ID of the event
        user_id (int): The sender's user ID
        message_text (str): The message content
        
    Returns:
        int: The message ID if successful, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    
    try:
        cursor.execute(
            "INSERT INTO chat_messages (event_id, user_id, message_text, timestamp) VALUES (?, ?, ?, ?)",
            (event_id, user_id, message_text, timestamp)
        )
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        return message_id
    except sqlite3.Error as e:
        print(f"Error adding chat message: {e}")
        conn.close()
        return None

def get_chat_messages(event_id, limit=50):
    """
    Retrieves chat messages for an event.
    
    Args:
        event_id (int): The ID of the event
        limit (int): Maximum number of messages to return (most recent first)
        
    Returns:
        list: List of message dictionaries with sender details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            m.message_id,
            m.user_id,
            u.full_name,
            u.role,
            m.message_text,
            m.timestamp
        FROM chat_messages m
        JOIN users u ON m.user_id = u.user_id
        WHERE m.event_id = ?
        ORDER BY m.timestamp DESC
        LIMIT ?
    """
    
    try:
        cursor.execute(query, (event_id, limit))
        messages = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts and reverse to show oldest first
        result = [dict(m) for m in messages]
        result.reverse()  # Show in chronological order
        
        return result
    except sqlite3.Error as e:
        print(f"Error retrieving chat messages: {e}")
        conn.close()
        return [] 

# --- Ticket Management Functions ---

def get_ticketed_events():
    """Retrieves all events that have ticketing enabled."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT event_id, event_name, event_date, event_location FROM events WHERE has_tickets = 1 AND event_date >= date('now') ORDER BY event_date")
    events = cursor.fetchall()
    conn.close()
    return [dict(event) for event in events]

def generate_ticket_code():
    """Generates a unique ticket code with format EVT-XXXX-XXXX."""
    # Generate a random 8-character alphanumeric code
    chars = string.ascii_uppercase + string.digits
    code_part = ''.join(random.choice(chars) for _ in range(8))
    return f"EVT-{code_part[:4]}-{code_part[4:]}"

def book_ticket(event_id, user_name, user_class, user_roll_number, user_address):
    """Books a ticket for an event and returns the ticket code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if event exists and has ticketing enabled
    cursor.execute("SELECT has_tickets FROM events WHERE event_id = ?", (event_id,))
    event = cursor.fetchone()
    
    if not event or not event['has_tickets']:
        conn.close()
        return None
    
    # Generate a unique ticket code
    ticket_code = generate_ticket_code()
    
    # Set booking timestamp to current date/time
    booking_timestamp = datetime.datetime.now().isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO tickets 
            (event_id, ticket_code, user_name, user_class, user_roll_number, user_address, booking_timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, 
            (event_id, ticket_code, user_name, user_class, user_roll_number, user_address, booking_timestamp)
        )
        conn.commit()
        conn.close()
        return ticket_code
    except sqlite3.Error as e:
        print(f"Error booking ticket: {e}")
        conn.rollback()
        conn.close()
        # If there was a unique constraint error with the ticket code, try again with a new code
        if "UNIQUE constraint failed: tickets.ticket_code" in str(e):
            return book_ticket(event_id, user_name, user_class, user_roll_number, user_address)
        return None

def get_tickets_for_event(event_id):
    """Retrieves all tickets for a specific event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ticket_id, ticket_code, user_name, user_class, user_roll_number, user_address, booking_timestamp 
        FROM tickets 
        WHERE event_id = ? 
        ORDER BY booking_timestamp DESC
        """, 
        (event_id,)
    )
    tickets = cursor.fetchall()
    conn.close()
    return [dict(ticket) for ticket in tickets]

def validate_ticket(ticket_code):
    """Validates if a ticket code exists and returns the ticket details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.ticket_id, t.ticket_code, t.user_name, t.user_class, t.user_roll_number, 
               t.booking_timestamp, e.event_name, e.event_date 
        FROM tickets t
        JOIN events e ON t.event_id = e.event_id
        WHERE t.ticket_code = ?
        """, 
        (ticket_code,)
    )
    ticket = cursor.fetchone()
    conn.close()
    return dict(ticket) if ticket else None 

def update_user_profile(user_id, update_data):
    """Updates a user's profile information.
    
    Args:
        user_id (int): The ID of the user to update
        update_data (dict): A dictionary with the fields to update, can include:
                           'full_name', 'password', 'college'
                           
    Returns:
        bool: True if the update was successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Update user table fields if needed
        user_table_fields = []
        user_table_values = []
        
        if 'full_name' in update_data:
            user_table_fields.append('full_name = ?')
            user_table_values.append(update_data['full_name'])
            
        if 'password' in update_data:
            password_hash = generate_password_hash(update_data['password'])
            user_table_fields.append('password_hash = ?')
            user_table_values.append(password_hash)
        
        # Only update the users table if there are changes
        if user_table_fields:
            user_table_values.append(user_id)
            update_user_query = f"UPDATE users SET {', '.join(user_table_fields)} WHERE user_id = ?"
            cursor.execute(update_user_query, user_table_values)
        
        # Update college in metadata table if needed
        if 'college' in update_data:
            # Check if user_metadata table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_metadata'")
            metadata_exists = cursor.fetchone() is not None
            
            if not metadata_exists:
                # Create the table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_metadata (
                        metadata_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        UNIQUE (user_id, key)
                    )
                """)
            
            # Check if the user already has a college entry
            cursor.execute("SELECT value FROM user_metadata WHERE user_id = ? AND key = 'college'", (user_id,))
            existing_college = cursor.fetchone()
            
            if existing_college:
                # Update existing college
                cursor.execute("UPDATE user_metadata SET value = ? WHERE user_id = ? AND key = 'college'", 
                               (update_data['college'], user_id))
            else:
                # Insert new college
                cursor.execute("INSERT INTO user_metadata (user_id, key, value) VALUES (?, 'college', ?)",
                               (user_id, update_data['college']))
        
        # Commit all changes
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Error updating user profile: {e}")
        conn.rollback()
        return False
    finally:
        conn.close() 

def get_all_college_options():
    """Retrieves a list of all unique college names from user_metadata."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user_metadata table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_metadata'")
        if cursor.fetchone():
            # Get unique college names
            cursor.execute("SELECT DISTINCT value FROM user_metadata WHERE key = 'college'")
            colleges = [row['value'] for row in cursor.fetchall()]
            conn.close()
            return colleges
        else:
            conn.close()
            return []
    except sqlite3.Error as e:
        print(f"Error fetching college options: {e}")
        conn.close()
        return [] 

def verify_password(user_id, password):
    """Verifies if the provided password matches the user's stored password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False
            
        # Use werkzeug's check_password_hash to verify
        return check_password_hash(user['password_hash'], password)
    except sqlite3.Error as e:
        print(f"Error verifying password: {e}")
        conn.close()
        return False 