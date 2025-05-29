import streamlit as st
import pandas as pd
import backend as be
import security as sec

def check_user_college_access(user_id, event_id):
    """
    Verify that a user has access to an event based on college association.
    Returns True if the user's college matches the event's college.
    """
    # Get user's college
    user = be.get_user_by_id(user_id)
    if not user or 'college' not in user or not user['college']:
        return False
    
    # Get event's college
    event = be.get_event_by_id(event_id)
    if not event or 'college' not in event or not event['college']:
        return False
    
    # Check if they match
    return user['college'] == event['college']

def check_assignment_access(user_id, assignment_id):
    """
    Verify that a user has access to an assignment.
    Returns True if the user is assigned to the task or is a Head with correct college.
    """
    # Get assignment details
    conn = be.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.user_id, a.event_id, e.event_name
            FROM assignments a
            JOIN events e ON a.event_id = e.event_id
            WHERE a.assignment_id = ?
        """, (assignment_id,))
        
        assignment = cursor.fetchone()
        conn.close()
        
        if not assignment:
            return False
        
        # If user is directly assigned
        if assignment['user_id'] == user_id:
            return True
            
        # If user is a Head, check if they have access to this event's college
        user = be.get_user_by_id(user_id)
        if user and user.get('role') == 'Head':
            # Verify college match
            return check_user_college_access(user_id, assignment['event_id'])
            
        return False
        
    except Exception as e:
        print(f"Error checking assignment access: {e}")
        if conn:
            conn.close()
        return False

def filter_events_by_college(events, user_id):
    """
    Filter events to only include those matching the user's college.
    """
    user = be.get_user_by_id(user_id)
    if not user or 'college' not in user or not user['college']:
        return []
    
    user_college = user['college']
    return [e for e in events if e.get('college') == user_college]

def filter_members_by_college(members, user_college):
    """
    Filter members to only include those matching a specific college.
    """
    if not user_college:
        return []
    
    # Get college info for each member
    return [m for m in members 
            if be.get_user_by_id(m['user_id']).get('college') == user_college]

def validate_form_input(form_data, required_fields=None, email_fields=None, phone_fields=None, 
                        date_fields=None, datetime_fields=None):
    """
    Validate form inputs. Returns (is_valid, error_message)
    """
    if required_fields:
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                return False, f"Field '{field}' is required"
    
    if email_fields:
        for field in email_fields:
            if field in form_data and form_data[field] and not sec.validate_email(form_data[field]):
                return False, f"Invalid email format for '{field}'"
    
    if phone_fields:
        for field in phone_fields:
            if field in form_data and form_data[field] and not sec.validate_phone(form_data[field]):
                return False, f"Invalid phone format for '{field}'"
    
    if date_fields:
        for field in date_fields:
            if field in form_data and form_data[field] and not sec.validate_date_format(str(form_data[field])):
                return False, f"Invalid date format for '{field}' (use YYYY-MM-DD)"
    
    if datetime_fields:
        for field in datetime_fields:
            if field in form_data and form_data[field] and not sec.validate_datetime_format(form_data[field]):
                return False, f"Invalid datetime format for '{field}' (use YYYY-MM-DD HH:MM)"
    
    return True, "Validation successful"

def sanitize_form_data(form_data):
    """
    Sanitize all form inputs to prevent XSS attacks.
    """
    sanitized_data = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            sanitized_data[key] = sec.sanitize_input(value)
        else:
            sanitized_data[key] = value
    return sanitized_data 