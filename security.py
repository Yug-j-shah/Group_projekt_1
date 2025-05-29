import streamlit as st
import time
import secrets
import re
import html
from datetime import datetime, timedelta

# Constants
SESSION_TIMEOUT = 60 * 60  # 1 hour in seconds

def init_session_state():
    """Initialize security-related session state variables."""
    if 'login_time' not in st.session_state:
        st.session_state['login_time'] = None
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = None
        
def generate_session_id():
    """Generate a cryptographically secure session ID."""
    return secrets.token_hex(32)

def set_session_cookie():
    """Set a secure session cookie."""
    if 'session_id' in st.session_state and st.session_state['session_id']:
        # In a production environment, you would set a secure HTTP-only cookie
        # Since Streamlit doesn't support direct cookie manipulation, we use session state
        st.session_state['login_time'] = time.time()

def check_session_active():
    """Check if the current session is still active or has timed out."""
    if 'login_time' not in st.session_state or not st.session_state['login_time']:
        return False
        
    current_time = time.time()
    elapsed_time = current_time - st.session_state['login_time']
    
    if elapsed_time > SESSION_TIMEOUT:
        # Session expired
        return False
    
    # Update the login time to extend the session
    st.session_state['login_time'] = current_time
    return True

def sanitize_input(input_str):
    """Sanitize input to prevent XSS attacks."""
    if input_str is None:
        return None
    # First, HTML escape the string
    sanitized = html.escape(str(input_str))
    # Remove potential script injection patterns
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'on\w+=".*?"', '', sanitized, flags=re.IGNORECASE)
    return sanitized

def validate_email(email):
    """Validate email format."""
    if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return False
    return True

def validate_phone(phone):
    """Validate phone number format."""
    if phone and not re.match(r"^\+?[0-9\s\-()]{7,20}$", phone):
        return False
    return True

def validate_date_format(date_str):
    """Validate date string in YYYY-MM-DD format."""
    try:
        if date_str:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
    except ValueError:
        return False
    return True

def validate_datetime_format(datetime_str):
    """Validate datetime string in YYYY-MM-DD HH:MM format."""
    try:
        if datetime_str:
            datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            return True
    except ValueError:
        return False
    return True 