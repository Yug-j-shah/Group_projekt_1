import streamlit as st
import pandas as pd
from datetime import date, datetime
import time as time_module  # Import time module with a different name
from datetime import time  # Import time class from datetime
import re
import html

# Import backend functions
import backend as be
from database import initialize_database

# Import our new security modules
import security as sec
import data_access as da
import ui_components as ui

# --- Database Initialization ---
# Ensure the database and tables are created when the app starts
initialize_database()

# --- Page Configuration ---
st.set_page_config(page_icon="📅",page_title="EventEase", layout="wide")

# --- Custom CSS ---
# Add Content-Security-Policy to prevent XSS attacks
custom_css = """
<style>
    /* Apply purple-navy-blue gradient to the app */
    .stApp {
        background-image: linear-gradient(111.6deg, rgba(207,25,233,1) 0.3%, rgba(52,66,101,1) 51.8%, rgba(28,123,241,1) 100.2%) !important;
        background-attachment: fixed !important;
        background-size: cover !important;
        background-position: center center !important;
        min-height: 100vh !important;
    }
    
    /* Animation Keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    /* New animations for glow effects */
    @keyframes textGlow {
        0% { text-shadow: 0 0 5px rgba(255, 255, 255, 0.3), 0 0 10px rgba(255, 255, 255, 0.2); }
        50% { text-shadow: 0 0 15px rgba(102, 204, 255, 0.8), 0 0 20px rgba(102, 204, 255, 0.5); }
        100% { text-shadow: 0 0 5px rgba(255, 255, 255, 0.3), 0 0 10px rgba(255, 255, 255, 0.2); }
    }
    
    @keyframes buttonLight {
        0% { background-position: -100% 0; }
        100% { background-position: 200% 0; }
    }
    
    @keyframes neonPulse {
        0% { box-shadow: 0 0 5px rgba(255, 255, 255, 0.5), 0 0 10px rgba(161, 103, 221, 0.5); }
        50% { box-shadow: 0 0 15px rgba(161, 103, 221, 0.8), 0 0 20px rgba(161, 103, 221, 0.8); }
        100% { box-shadow: 0 0 5px rgba(255, 255, 255, 0.5), 0 0 10px rgba(161, 103, 221, 0.5); }
    }
    
    /* Apply animations to main content blocks */
    .main .block-container {
        animation: fadeIn 0.6s ease-out forwards;
    }
    
    /* Title text animation with glow */
    h1 {
        animation: slideInLeft 0.5s ease-out forwards, textGlow 3s ease-in-out infinite;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5), 0 0 15px rgba(102, 204, 255, 0.5);
    }
    
    h2, h3 {
        animation: slideInLeft 0.5s ease-out forwards;
        text-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
    }
    
    /* Add glow effect to header text */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5), 0 0 15px rgba(102, 204, 255, 0.5);
    }
    
    /* Make sidebar items appear with delay */
    [data-testid="stSidebar"] .block-container {
        animation: fadeIn 0.4s ease-out forwards;
    }
    
    /* Card animations with glow */
    div[data-testid="stExpander"], div.stForm {
        transition: all 0.3s ease;
        animation: fadeIn 0.6s ease-out forwards;
        box-shadow: 0 0 5px rgba(255, 255, 255, 0.2);
    }
    
    div[data-testid="stExpander"]:hover, div.stForm:hover {
        animation: neonPulse 2s infinite;
    }
    
    /* Button animations with light effect */
    .stButton > button, div[data-testid="stForm"] button[kind="primary"], button {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        transition: all 0.3s ease !important;
        position: relative;
        overflow: hidden;
        z-index: 1;
    }
    
    /* Light animation behind buttons */
    .stButton > button::before, 
    div[data-testid="stForm"] button[kind="primary"]::before, 
    button::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 200%;
        height: 100%;
        background: linear-gradient(to right, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 0.3) 50%, 
            rgba(255, 255, 255, 0) 100%);
        z-index: -1;
        animation: buttonLight 3s infinite linear;
        transform: translateX(-100%);
    }
    
    /* Button hover effects */
    .stButton > button:hover, div[data-testid="stForm"] button[kind="primary"]:hover, button:hover {
        background-color: rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3), 0 0 15px rgba(161, 103, 221, 0.8);
        text-shadow: 0 0 5px rgba(255, 255, 255, 0.7);
    }
    
    /* Button active effect */
    .stButton > button:active, .stButton > button:focus,
    div[data-testid="stForm"] button[kind="primary"]:active, div[data-testid="stForm"] button[kind="primary"]:focus,
    button:active, button:focus {
        background-color: rgba(255, 255, 255, 0.35) !important;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5), 0 0 10px rgba(161, 103, 221, 0.8) !important;
        transform: translateY(1px);
    }
    
    /* Success message animation */
    div[data-baseweb="notification"] {
        animation: slideInLeft 0.4s ease-out forwards, pulse 2s ease-in-out 1;
        box-shadow: 0 0 15px rgba(102, 204, 255, 0.7);
    }
    
    /* Form field focus animation */
    input:focus, select:focus, textarea:focus, 
    div.stTextInput>div>div>input:focus, 
    div.stNumberInput>div>div>input:focus,
    div.stTextArea>div>div>textarea:focus {
        transform: translateY(-2px);
        transition: transform 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1), 0 0 10px rgba(161, 103, 221, 0.6) !important;
    }
    
    /* Dataframe hover effect */
    div[data-testid="stDataFrame"] tr:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        transition: background-color 0.3s ease;
    }
    
    /* Chat message animation */
    div[data-testid="stChatMessage"] {
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    /* Loading animation */
    div[data-testid="stSpinner"] {
        animation: pulse 1.5s infinite ease-in-out;
        filter: drop-shadow(0 0 10px rgba(161, 103, 221, 0.8));
    }
    
    /* Event card hover effects */
    .main .block-container > div:has(div[data-testid="column"]) {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .main .block-container > div:has(div[data-testid="column"]):hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1), 0 0 15px rgba(161, 103, 221, 0.6);
    }
    
    /* Ensure the sidebar blends with the gradient */
    section[data-testid="stSidebar"] {
        background: transparent !important;
    }
    
    /* Make all containers transparent to show the gradient */
    .main .block-container, 
    div[data-testid="stVerticalBlock"], 
    div.stForm,
    div[data-testid="stExpander"] {
        background: transparent !important;
    }
    
    /* Ensure inputs and selectors are semi-transparent to show gradient but remain readable */
    input, select, textarea, div.stTextInput>div>div>input, div.stNumberInput>div>div>input,
    div.stTextArea>div>div>textarea, div.stSelectbox>div[data-baseweb="select"]>div,
    div.stMultiselect>div[data-baseweb="select"]>div, div.stDateInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transition: all 0.3s ease; /* Added transition for smooth effects */
    }
    
    /* Style dataframes and metrics to be semi-transparent */
    div[data-testid="stDataFrame"], div[data-testid="stMetric"] {
        background-color: rgba(0, 0, 0, 0.2) !important;
        border-radius: 5px !important;
        transition: all 0.3s ease; /* Added transition */
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Ensure text is visible on the gradient background with glow effect */
    .stMarkdown, h1, h2, h3, label, p, div, span {
        color: white !important;
        text-shadow: 0px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Add glow to key elements */
    .stMarkdown strong, .stMetric label, .stMetric .css-16r8m64 {
        text-shadow: 0 0 10px rgba(161, 103, 221, 0.8);
        animation: textGlow 3s ease-in-out infinite;
    }
    
    /* Add a pulsing effect to important notifications */
    div.element-container:has(div[data-baseweb="notification"]) {
        animation: pulse 2s infinite;
    }
    
    /* Add shimmer effect to metrics */
    div[data-testid="stMetric"] {
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 10px rgba(161, 103, 221, 0.4);
    }
    
    div[data-testid="stMetric"]::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to right, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 0.2) 50%, 
            rgba(255, 255, 255, 0) 100%);
        background-size: 200% 100%;
        animation: shimmer 3s infinite;
    }
    
    /* Radio button animations */
    .stRadio > div > label:hover {
        transform: translateX(3px);
        transition: transform 0.2s ease;
        text-shadow: 0 0 10px rgba(161, 103, 221, 0.8);
    }
    
    /* Checkbox animations */
    .stCheckbox > div > label:hover {
        transform: translateX(3px);
        transition: transform 0.2s ease;
        text-shadow: 0 0 10px rgba(161, 103, 221, 0.8);
    }
    
    /* Selectbox animations */
    div[data-baseweb="select"] div {
        transition: all 0.3s ease;
    }
    
    div[data-baseweb="select"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1), 0 0 10px rgba(161, 103, 221, 0.6);
    }
    
    /* Divider animation */
    hr {
        position: relative;
        overflow: hidden;
        border-color: rgba(255, 255, 255, 0.3);
        box-shadow: 0 0 10px rgba(161, 103, 221, 0.4);
    }
    
    hr::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to right, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 0.5) 50%, 
            rgba(255, 255, 255, 0) 100%);
        background-size: 200% 100%;
        animation: shimmer 3s infinite;
    }
</style>
"""

# --- Constants ---
TASK_STATUS_OPTIONS = ui.TASK_STATUS_OPTIONS
VENDOR_STATUS_OPTIONS = ui.VENDOR_STATUS_OPTIONS
GUEST_RSVP_OPTIONS = ui.GUEST_RSVP_OPTIONS
LOGISTICS_STATUS_OPTIONS = ui.LOGISTICS_STATUS_OPTIONS
SCHEDULE_STATUS_OPTIONS = ui.SCHEDULE_STATUS_OPTIONS

TASK_PAGE_MAP = {
    "Vendor Management": "render_vendor_page",
    "Guest List Management": "render_guest_page",
    "Logistics Management": "render_logistics_page",
    "Schedule Coordination": "render_schedule_page",
    "Ticket Management": "render_ticket_management_page",
    "Task Tracking": "render_task_tracking_page",
    "Reports": "render_reports_page",
    "Team Chat": "render_team_chat_page"
}

# Store TASK_PAGE_MAP in backend for reference
be.TASK_PAGE_MAP = TASK_PAGE_MAP.copy()

# --- User Sessions ---
# Initialize security session state
sec.init_session_state()

# Initialize college info dictionaries
if 'college_info' not in st.session_state:
    st.session_state['college_info'] = {}
if 'event_colleges' not in st.session_state:
    st.session_state['event_colleges'] = {}

# Enable dev mode for debugging (should be disabled in production)
if 'dev_mode' not in st.session_state:
    st.session_state['dev_mode'] = False

# --- Function to determine if a task is custom ---
def is_custom_task(task_name):
    """Returns True if the task is not one of the standard predefined tasks."""
    # Also check if it's not one of the special Head-only pages
    return task_name not in TASK_PAGE_MAP and task_name not in ["Task Tracking", "Reports"]

# --- Custom Task Page Rendering ---
def render_custom_task_page(event_id, user_role, assignment=None):
    """Renders a page for custom tasks."""
    # Verify access permissions
    if not da.check_user_college_access(st.session_state['user_info']['user_id'], event_id):
        st.error("Access denied: You don't have permission to view this event.")
        return
        
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    
    task_name = assignment['task_name'] if assignment else "Custom Task"
    
    st.title(f"Custom Task: {task_name}")
    st.subheader(f"Event: {event_info['event_name']}")
    
    # Display task description
    if assignment and assignment.get('description'):
        st.markdown("**Task Description:**")
        st.markdown(sec.sanitize_input(assignment['description']))
    else:
        st.info("No description provided for this task.")
    
    if user_role == 'Member' and assignment:
        st.divider()
        ui.render_status_update(assignment)

# --- Function to get the appropriate render function for a task ---
def get_render_function_for_task(task_name):
    """Returns the appropriate rendering function for a task name."""
    if is_custom_task(task_name):
        return render_custom_task_page
    else:
        function_name = TASK_PAGE_MAP.get(task_name)
        return globals().get(function_name) if function_name else None

# --- Authentication State ---
def init_auth_state():
    """Initialize authentication state with security measures."""
    if 'auth_view' not in st.session_state:
        st.session_state['auth_view'] = 'login'  # Default to login view
        
    # Add booking view state
    if 'booking_ticket_code' not in st.session_state:
        st.session_state['booking_ticket_code'] = None
    if 'selected_college' not in st.session_state:
        st.session_state['selected_college'] = None
        
    # Ensure college_info and event_colleges are initialized
    if 'college_info' not in st.session_state:
        st.session_state['college_info'] = {}
    if 'event_colleges' not in st.session_state:
        st.session_state['event_colleges'] = {}
    
    # If user is logged in, validate session timeout
    if st.session_state.get('logged_in'):
        if not sec.check_session_active():
            # Session expired, log the user out
            logout(expired=True)
            return
            
    # Load event-college associations from database
    try:
        # Get all events and their college associations
        events_with_colleges = be.get_events_with_colleges()
        if events_with_colleges:
            for event in events_with_colleges:
                event_id = event.get('event_id')
                college = event.get('college')
                if event_id and college:
                    st.session_state['event_colleges'][event_id] = college
    except Exception as e:
        if st.session_state.get('dev_mode'):
            print(f"Error loading event-college associations: {e}")
            
    # Load user-college associations from database
    try:
        # Get all users and their college associations
        users_with_colleges = be.get_users_with_colleges()
        if users_with_colleges:
            for user in users_with_colleges:
                user_id = user.get('user_id')
                college = user.get('college')
                if user_id and college:
                    st.session_state['college_info'][user_id] = college
    except Exception as e:
        if st.session_state.get('dev_mode'):
            print(f"Error loading user-college associations: {e}")

# --- Helper Functions ---
def render_auth_page():
    """Displays the login or sign-up form with enhanced security."""
    init_auth_state()  # Ensure state is initialized

    if st.session_state['auth_view'] == 'login':
        st.header("Welcome to EventEase")
        st.subheader("Please Login to continue!")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                # Validate and sanitize inputs
                username = sec.sanitize_input(username)
                # Password is not sanitized as it goes directly to hash verification
                
                if not username or not password:
                    st.error("Username and password are required")
                elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                    st.error("Username can only contain letters, numbers, and underscores")
                else:
                    user = be.verify_user(username, password)
                    if user:
                        # Create and store session information
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = user
                        st.session_state['page'] = 'Dashboard'  # Default page after login
                        st.session_state['auth_view'] = 'login'  # Reset view for next time
                        
                        # Set up session security
                        st.session_state['session_id'] = sec.generate_session_id()
                        sec.set_session_cookie()
                        
                        # Store college from user data
                        user_id = user.get('user_id')
                        college_from_db = user.get('college')
                        if user_id and college_from_db:
                            st.session_state['college_info'][user_id] = college_from_db
                            
                        # Load all event-college associations
                        try:
                            events_with_colleges = be.get_events_with_colleges()
                            if events_with_colleges:
                                for event in events_with_colleges:
                                    event_id = event.get('event_id')
                                    college = event.get('college')
                                    if event_id and college:
                                        st.session_state['event_colleges'][event_id] = college
                        except Exception as e:
                            st.warning(f"Could not load event-college associations: {e}")

                        st.rerun()  # Rerun to reflect login state
                    else:
                        st.error("Invalid username or password")
        
        col_signup, col_book = st.columns(2)
        with col_signup:
            if st.button("Switch to Sign Up"):
                st.session_state['auth_view'] = 'signup'
                st.session_state['booking_ticket_code'] = None  # Clear ticket code when switching view
                st.rerun()
        with col_book:
            if st.button("Book Event Tickets"):
                st.session_state['auth_view'] = 'book_tickets'
                st.session_state['booking_ticket_code'] = None  # Clear ticket code when switching view
                st.rerun()

    elif st.session_state['auth_view'] == 'signup':
        st.header("Welcome to EventEase")
        st.subheader("Please Sign-up as Event Head!")
        
        with st.form("signup_form"):
            signup_fullname = st.text_input("Full Name", key="signup_fullname")
            signup_username = st.text_input("Username", key="signup_username", 
                                          help="Username must contain only letters, numbers, and underscores")
            signup_password = st.text_input("Password", type="password", key="signup_password",
                                          help="Password must be at least 8 characters long with letters and numbers")
            signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
            signup_college = st.text_input("College Name", key="signup_college")
            signup_submitted = st.form_submit_button("Sign Up as Head")

            if signup_submitted:
                # Validate and sanitize all inputs
                form_data = {
                    "fullname": sec.sanitize_input(signup_fullname),
                    "username": sec.sanitize_input(signup_username),
                    "college": sec.sanitize_input(signup_college),
                }
                
                # Custom validation
                if not all([form_data["fullname"], signup_username, signup_password, signup_confirm_password, form_data["college"]]):
                    st.warning("Please fill in all fields.")
                elif not re.match(r'^[a-zA-Z0-9_]+$', signup_username):
                    st.error("Username can only contain letters, numbers, and underscores")
                elif len(signup_password) < 8:
                    st.error("Password must be at least 8 characters long")
                elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$', signup_password):
                    st.error("Password must contain at least one letter and one number")
                elif signup_password != signup_confirm_password:
                    st.error("Passwords do not match")
                else:
                    # Create user with college in database
                    user_id = be.create_user(signup_username, signup_password, 'Head', form_data["fullname"], college=form_data["college"])
                    if user_id:
                        # Store in session state too for immediate use
                        st.session_state['college_info'][user_id] = form_data["college"]
                        st.success(f"Head user '{signup_username}' created successfully! Please switch back to Login.")
                    else:
                        st.error(f"Username '{signup_username}' already exists. Please choose a different one.")
        
        if st.button("Back to Login"):
            st.session_state['auth_view'] = 'login'
            st.rerun()

    elif st.session_state['auth_view'] == 'book_tickets':
        render_book_tickets_page()  # Call the booking page function

def logout(expired=False):
    """Logs the user out by clearing session state with security measures."""
    st.session_state['logged_in'] = False
    st.session_state.pop('user_info', None)
    st.session_state.pop('selected_event_id', None)
    st.session_state.pop('page', None)
    st.session_state.pop('booking_ticket_code', None) # Clear ticket code on logout
    st.success("Logged out successfully.")
    st.rerun() # Rerun to show login page


# --- Placeholder Page Rendering Functions (Will be implemented later) ---
def render_dashboard():
    st.title(f"Welcome, {st.session_state['user_info']['full_name']}!")

    st.header("Event Overview")

    # --- Get Event Data ---
    all_events = be.get_all_events()  # This now returns events with college info
    user_id = st.session_state['user_info']['user_id']
    user_role = st.session_state['user_info']['role']
    user_college = st.session_state['college_info'].get(user_id)
    
    # Filter events based on user role and college association
    if user_role == 'Head':
        # user_college fetched above
        if user_college:
            # Filter events by college using college field from all_events
            events = [
                e for e in all_events
                if e.get('college') == user_college
            ]
            st.subheader(f"College: {user_college}")
        else:
            st.warning("Your account is not associated with a college. You won't see any events. Please update your profile.")
            events = []
    elif user_role == 'Member':
        # user_college fetched above
        if user_college:
            # Filter events to show only those from the member's college
            events = [
                e for e in all_events
                if e.get('college') == user_college
            ]
            st.subheader(f"College: {user_college}") # Show college context
        else:
            st.warning("Your account is not associated with a college. You won't see any events. Please update your profile.")
            events = []
    else: # Should not happen, but default to no events
        events = []

    if not events:
        if user_college: # Check if user_college was determined
             st.info(f"No events found for {user_college}. Please check back later or contact your Event Head.")
        # else: # Warning for no college association already shown
        return

    events_df = pd.DataFrame(events)

    # Convert 'event_date' to datetime objects for comparison
    # Assuming event_date is stored as 'YYYY-MM-DD' string
    try:
        events_df['event_date'] = pd.to_datetime(events_df['event_date']).dt.date
    except Exception as e:
        st.error(f"Error processing event dates: {e}. Please ensure dates are in YYYY-MM-DD format.")
        return

    # --- Calculate Event Status ---    
    today = date.today()
    upcoming_events = events_df[events_df['event_date'] >= today]
    completed_events = events_df[events_df['event_date'] < today]

    # --- Display Metrics --- Metrics should reflect the filtered events
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Events", len(events_df))
    with col2:
        st.metric("Upcoming Events", len(upcoming_events))
    with col3:
        st.metric("Completed Events", len(completed_events))

    st.divider()

    # --- Display Event Lists --- Lists show filtered events
    col_up, col_comp = st.columns(2)

    with col_up:
        st.subheader("📅 Upcoming Events")
        if not upcoming_events.empty:
            display_cols = ['event_name', 'event_date', 'event_location']
            st.dataframe(
                upcoming_events[display_cols].sort_values(by='event_date'),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No upcoming events.")

    with col_comp:
        st.subheader("✅ Completed Events")
        if not completed_events.empty:
            display_cols = ['event_name', 'event_date', 'event_location']
            st.dataframe(
                completed_events[display_cols].sort_values(by='event_date', ascending=False),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No completed events yet.")

def render_create_event_page():
    st.title("Create New Event")
    with st.form("create_event_form"):
        event_name = st.text_input("Event Name")
        # Use date_input for better UI
        event_date = st.date_input("Event Date", value=date.today())
        event_location = st.text_input("Event Location")
        # Add college field - defaults to head's college
        head_user_id = st.session_state['user_info']['user_id']
        event_college = st.text_input("College Name", value=st.session_state['college_info'].get(head_user_id, ''))
        # Add Ticketing Checkbox
        has_tickets = st.checkbox("Enable Ticketing for this Event?", key="event_ticketing_checkbox")
        submitted = st.form_submit_button("Create Event")
        if submitted:
            if not event_name:
                st.warning("Event Name is required.")
            elif not event_college:
                st.warning("College Name is required.")
            else:
                # Pass has_tickets flag and college name to backend
                event_date_str = event_date.isoformat()
                # Store event college in event metadata
                event_id = be.create_event(event_name, event_date_str, event_location, has_tickets, college=event_college)
                if event_id:
                    # Store college info in session state as well for immediate use
                    if 'event_colleges' not in st.session_state:
                        st.session_state['event_colleges'] = {}
                    st.session_state['event_colleges'][event_id] = event_college
                    st.success(f"Event '{event_name}' created successfully with ID: {event_id}")
                    st.balloons() # Add celebratory balloons!
                else:
                    st.error("Event name might already exist or another error occurred.")
    st.divider()
    st.subheader("Existing Events")
    
    # Get current Head's info
    current_head_user_id = st.session_state['user_info']['user_id']
    current_head_college = st.session_state['college_info'].get(current_head_user_id)

    if not current_head_college:
        st.warning("Cannot display existing events as your account has no college association.")
        return
        
    all_events = be.get_all_events()  # Now includes college info
    
    # Filter events to show only those from the head's college
    college_events = [
        e for e in all_events 
        if e.get('college') == current_head_college
    ]

    if college_events:
        events_df = pd.DataFrame(college_events)
        # Sort by date for consistent display
        try:
            events_df['event_date'] = pd.to_datetime(events_df['event_date']).dt.date
            events_df = events_df.sort_values(by='event_date', ascending=False)
        except Exception as e:
             st.warning(f"Could not sort events by date due to format issue: {e}")

        # Display events with delete buttons
        for index, event in events_df.iterrows():
            event_id = event['event_id']
            event_name = event['event_name']
            event_date_display = str(event.get('event_date', 'N/A')) 
            event_location = event.get('event_location', 'N/A')
            # Get college from event data directly
            event_college = event.get('college', 'N/A')
            ticketing_status = "🎟️ Ticketing Enabled" if event.get('has_tickets') else ""
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{event_name}**")
                st.caption(f"📅 {event_date_display} | 📍 {event_location} | 🏫 {event_college} | ID: {event_id} {ticketing_status}")
            with col2:
                # Unique key for the initial delete button
                delete_key = f"delete_{event_id}"
                if st.button("🗑️ Delete", key=delete_key):
                    # Store the event ID intended for deletion in session state
                    st.session_state[f'confirm_delete_{event_id}'] = True 

            # Confirmation section appears if the specific delete button was clicked
            if st.session_state.get(f'confirm_delete_{event_id}'):
                 st.warning(f"❓ Are you sure you want to delete the event: **{event_name}** (ID: {event_id})? This action cannot be undone.")
                 confirm_col1, confirm_col2, _ = st.columns([1,1,3]) # Layout for confirm/cancel buttons
                 with confirm_col1:
                     confirm_key = f"confirm_button_{event_id}"
                     if st.button("✔️ Yes, Delete", key=confirm_key):
                         deleted = be.delete_event(event_id)
                         if deleted:
                             st.success(f"Event '{event_name}' deleted successfully.")
                             # Clean up session state flag
                             del st.session_state[f'confirm_delete_{event_id}']
                             # Also remove from event colleges if needed
                             if 'event_colleges' in st.session_state and event_id in st.session_state['event_colleges']:
                                 del st.session_state['event_colleges'][event_id]
                             st.rerun()
                         else:
                             st.error(f"Failed to delete event '{event_name}'.")
                             # Clean up session state flag even on failure
                             del st.session_state[f'confirm_delete_{event_id}']
                             st.rerun() # Rerun to clear confirmation state
                 with confirm_col2:
                     cancel_key = f"cancel_delete_{event_id}"
                     if st.button("❌ Cancel", key=cancel_key):
                          # Just clean up the flag and rerun to hide confirmation
                          del st.session_state[f'confirm_delete_{event_id}']
                          st.rerun()
            st.divider()
    else:
        st.info("No events created yet.")

def render_create_member_page():
    st.title("Create New Member")
    with st.form("create_member_form"):
        member_fullname = st.text_input("Member Full Name")
        member_username = st.text_input("Username (for login)")
        member_password = st.text_input("Password", type="password")
        
        # Get the head's college to associate with this member
        head_user_id = st.session_state['user_info']['user_id']
        head_college = st.session_state['college_info'].get(head_user_id, '')
        if head_college:
            st.info(f"This member will be associated with: {head_college}")
        else:
            st.warning("Your account doesn't have a college association. Please update your profile.")
            
        submitted = st.form_submit_button("Create Member")
        if submitted:
            if not member_fullname or not member_username or not member_password:
                st.warning("Please fill in all fields.")
            elif not head_college:
                st.error("Cannot create member: You don't have a college association. Contact an administrator.")
            else:
                # Pass the college to the backend
                user_id = be.create_user(member_username, member_password, 'Member', member_fullname, college=head_college)
                if user_id:
                    # Store in session state as well for immediate use
                    st.session_state['college_info'][user_id] = head_college
                    st.success(f"Member '{member_fullname}' ({member_username}) created successfully with ID: {user_id}")
                else:
                    st.error(f"Username '{member_username}' already exists. Please choose a different one.")
    st.divider()
    st.subheader("Existing Members")
    all_members = be.get_all_members() # Fetch list of all members
    
    # Get the current head's college
    current_head_user_id = st.session_state['user_info']['user_id']
    current_head_college = st.session_state['college_info'].get(current_head_user_id)

    if current_head_college:
        # Filter members to show only those from the head's college
        filtered_members = [
            m for m in all_members 
            if st.session_state['college_info'].get(m['user_id']) == current_head_college
        ]
    else:
        # If head has no college, show no members (consistent with dashboard)
        filtered_members = []
        st.warning("Cannot display members as your account has no college association.")

    if filtered_members:
        members_df = pd.DataFrame(filtered_members)
        # Add college info (already filtered, but good for consistency)
        members_df['college_name'] = members_df['user_id'].apply(
            lambda uid: st.session_state['college_info'].get(uid, 'N/A')
        )
        # Select and order columns for display
        display_columns = ['user_id', 'full_name', 'username', 'college_name']
        # Ensure columns exist before trying to access them
        members_df = members_df[[col for col in display_columns if col in members_df.columns]]
        st.dataframe(members_df, use_container_width=True)
    elif current_head_college: # Only show 'no members' if the head *has* a college
        st.info(f"No members found for {current_head_college} yet.")

def render_assign_task_page():
    st.title("Assign Tasks to Members")

    all_events = be.get_all_events()  # Now includes college info
    all_members = be.get_all_members()
    tasks = be.get_all_tasks()
    
    # Get current Head's info
    head_user_id = st.session_state['user_info']['user_id']
    head_college = st.session_state['college_info'].get(head_user_id)

    if not head_college:
        st.error("Your account is not associated with a college. Cannot assign tasks.")
        return
        
    # Filter events for this Head's college
    college_events = [
        e for e in all_events 
        if e.get('college') == head_college
    ]
    
    # Filter members for this Head's college
    college_members = [
        m for m in all_members
        if st.session_state['college_info'].get(m['user_id']) == head_college
    ]

    if not college_events:
        st.warning(f"Please create an event for {head_college} first.")
        return
    if not college_members:
        st.warning(f"Please create at least one member for {head_college} first.")
        return
    if not tasks:
        st.error("No tasks found in the database. Initialize tasks first.")
        return

    # Use filtered lists for selections
    event_dict = {e['event_name']: e['event_id'] for e in college_events}
    event_data = {e['event_id']: e for e in college_events} # Store full event data by ID
    member_dict = {m['full_name']: m['user_id'] for m in college_members}
    task_dict = {t['task_name']: t['task_id'] for t in tasks}

    CUSTOM_TASK_OPTION = "(Create Custom Task...)"
    # Initial task options (we'll filter based on selected event)
    all_task_options = list(task_dict.keys())
    
    # Remove Team Chat from assignable tasks since it's automatically available to all members
    if 'Team Chat' in all_task_options:
        all_task_options.remove('Team Chat')
        
    task_options = all_task_options + [CUSTOM_TASK_OPTION]

    # Event selection (filtered to head's college)
    selected_event_name = st.selectbox("Select Event", options=list(event_dict.keys()))
    selected_event_id = event_dict[selected_event_name]
    selected_event = event_data[selected_event_id]
    
    # Filter out Ticket Management if event doesn't have ticketing enabled
    # (Task options filtering logic remains the same)
    if not selected_event.get('has_tickets') and 'Ticket Management' in task_options:
        task_options.remove('Ticket Management')
    elif selected_event.get('has_tickets') and 'Ticket Management' not in all_task_options:
        if 'Ticket Management' in task_dict:
            task_options.insert(-1, 'Ticket Management')
    
    # Task selection dropdown on the main page
    selected_task_name = st.selectbox("Select Task or Create Custom", task_options)

    with st.form("assign_task_form"):
        # Member selection (filtered to head's college)
        selected_member_name = st.selectbox("Select Member", options=list(member_dict.keys()))

        # Custom task fields only appear inside the form if the custom option is selected
        if selected_task_name == CUSTOM_TASK_OPTION:
            custom_task_name_input = st.text_input("Custom Task Name")
            custom_task_description_input = st.text_area("Custom Task Description")

        submitted = st.form_submit_button("Assign Task")

        if submitted:
            event_id = selected_event_id
            user_id = member_dict[selected_member_name]

            if selected_task_name == CUSTOM_TASK_OPTION:
                if custom_task_name_input:
                    assignment_id = be.assign_custom_task(user_id, event_id, custom_task_name_input, custom_task_description_input)
                    if assignment_id:
                        st.success(f"Custom task '{custom_task_name_input}' assigned to '{selected_member_name}' for event '{selected_event_name}'.")
                        st.rerun()
                    else:
                        st.error(f"Failed to assign custom task. This might be because '{selected_member_name}' is already assigned this task for this event.")
                else:
                    st.warning("Please enter a name for the custom task.")
            else:
                task_id = task_dict[selected_task_name]
                assignment_id = be.assign_task(user_id, event_id, task_id)
                if assignment_id:
                    st.success(f"Task '{selected_task_name}' assigned to '{selected_member_name}' for event '{selected_event_name}'.")
                    st.rerun()
                else:
                    st.error(f"Failed to assign task. This might be because '{selected_member_name}' is already assigned this task for this event.")

    # Display current assignments (filtered to head's college)
    st.divider()
    st.subheader("Current Task Assignments")
    all_assignments = []
    # Iterate ONLY through events of the current head's college
    for event in college_events: 
        assignments_for_event = be.get_event_assignments(event['event_id'])
        if assignments_for_event:
            all_assignments.extend([{**a, 'event_name': event['event_name']} for a in assignments_for_event])

    if all_assignments:
        assign_df = pd.DataFrame(all_assignments)
        # Filter assignments further just to be safe (though should be redundant now)
        # Ensure assigned members belong to the current head's college
        assign_df = assign_df[assign_df['user_id'].isin(member_dict.values())]
        
        if not assign_df.empty:
            display_columns = ['event_name', 'full_name', 'task_name', 'status', 'assignment_id', 'user_id', 'task_id']
            # Make sure display columns exist
            assign_df = assign_df[[col for col in display_columns if col in assign_df.columns]]
            st.dataframe(assign_df, use_container_width=True)
        else:
            st.info(f"No tasks assigned yet for events at {head_college}.")
            
    else:
        st.info(f"No tasks assigned yet for events at {head_college}.")

def render_task_tracking_page(event_id):
    st.title(f"Task Progress Tracking")
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    st.header(f"Event: {event_info['event_name']}")

    assignments = be.get_event_assignments(event_id)

    if not assignments:
        st.info("No tasks have been assigned for this event yet.")
        return

    assignments_df = pd.DataFrame(assignments)
    # Display the tracking table
    st.subheader("Current Assignment Status")
    st.dataframe(assignments_df[['full_name', 'task_name', 'status']], use_container_width=True)

    # Optionally add charts or summaries
    status_counts = assignments_df['status'].value_counts()
    st.subheader("Status Summary")
    st.bar_chart(status_counts)

def render_reports_page(event_id):
    st.title("Event Reports")
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    st.header(f"Event: {event_info['event_name']}")

    st.subheader("Guest RSVP Report")
    guest_report_df = be.get_guest_report(event_id)
    if not guest_report_df.empty:
        st.dataframe(guest_report_df, use_container_width=True)
        # Change bar_chart to line_chart
        # Ensure the DataFrame has the correct index set for the chart
        try:
            # Assuming guest_report_df has columns like 'RSVP Status' and 'Count'
            chart_data = guest_report_df.set_index('RSVP Status')['Count'] # Adjust column names if needed
            st.line_chart(chart_data)
        except KeyError as e:
            st.error(f"Error preparing guest report chart data: Missing column - {e}. Check backend function get_guest_report.")
        except Exception as e:
             st.error(f"An unexpected error occurred while generating the guest report chart: {e}")
    else:
        st.info("No guest data available for this report.")

    st.divider()

    # --- Logistics Report ---
    st.subheader("Logistics Cost Report") # Renamed subheader
    logistics_items = be.get_logistics_for_event(event_id)

    if logistics_items:
        logistics_df = pd.DataFrame(logistics_items)

        # Convert cost and quantity columns to numeric, handling potential errors
        logistics_df['cost'] = pd.to_numeric(logistics_df['cost'], errors='coerce').fillna(0)
        logistics_df['quantity'] = pd.to_numeric(logistics_df['quantity'], errors='coerce').fillna(0)

        # Calculate total cost per item
        logistics_df['total_cost'] = logistics_df['cost'] * logistics_df['quantity']
        
        # Calculate overall total cost
        overall_total_logistics_cost = logistics_df['total_cost'].sum()
        st.metric(label="Total Logistics Cost", value=f"${overall_total_logistics_cost:,.2f}")

        # Prepare data for the line chart (using item name as index)
        # Ensure item names are unique or aggregate if necessary (simple approach assumes unique for now)
        chart_data = logistics_df.set_index('item_name')['total_cost']
        
        if not chart_data.empty:
            st.line_chart(chart_data)
        else:
            st.info("No cost data to display in the chart.")

        # Optional: Display summary table (can be removed if not needed)
        st.write("Logistics Item Details:")
        st.dataframe(logistics_df[['item_name', 'quantity', 'cost', 'total_cost', 'status']], use_container_width=True)

        # Remove the status bar chart
        # status_counts = logistics_df['status'].value_counts()
        # st.bar_chart(status_counts)

    else:
        st.info("No logistics items found for this event to generate a cost report.")

    st.divider()
    # --- End Logistics Report ---

    # --- Schedule Report (remains unchanged) ---
    st.subheader("Schedule Report")
    schedule = be.get_schedule_for_event(event_id)
    
    if schedule:
        schedule_df = pd.DataFrame(schedule)
        st.dataframe(schedule_df, use_container_width=True)
    else:
        st.info("No schedule items found for this event.")

def render_vendor_page(event_id, user_role, assignment=None):
    """Renders the Vendor Management page with enhanced security and validation."""
    # Verify access permissions
    if not da.check_user_college_access(st.session_state['user_info']['user_id'], event_id):
        st.error("Access denied: You don't have permission to view this event.")
        return
        
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
        
    st.title(f"Vendor Management: {event_info['event_name']}")

    # --- Member-Specific Section: Update Task Status ---
    if user_role == 'Member' and assignment:
        ui.render_status_update(assignment)

    # --- Display Vendors (Editable for Member, View-only for Head) ---
    st.subheader("Vendor List")
    
    try:
        vendors = be.get_vendors_for_event(event_id)
        
        # Define display columns for consistency
        display_columns = ['vendor_id', 'name', 'service_type', 'contact_person', 
                          'contact_email', 'contact_phone', 'status', 'notes']
        
        # Initialize DataFrame
        if not vendors:
            vendors_df = pd.DataFrame(columns=display_columns)
        else:
            vendors_df = pd.DataFrame(vendors)
            # Ensure all columns exist
            for col in display_columns:
                if col not in vendors_df.columns:
                    vendors_df[col] = None
            vendors_df = vendors_df[display_columns]

        # Define column configuration
        column_config = {
            "vendor_id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Name", required=True),
            "service_type": st.column_config.TextColumn("Service"),
            "contact_person": st.column_config.TextColumn("Contact Person"),
            "contact_email": st.column_config.TextColumn("Email"),
            "contact_phone": st.column_config.TextColumn("Phone"),
            "status": st.column_config.SelectboxColumn("Status", options=VENDOR_STATUS_OPTIONS, required=True),
            "notes": st.column_config.TextColumn("Notes", width="large")
        }
        
        # Process vendor updates function for Member role
        def process_vendor_updates(original_df, edited_df):
            if user_role != 'Member':
                return None
                
            original_ids = set(original_df['vendor_id'].dropna().tolist())
            current_ids = set(edited_df['vendor_id'].dropna().tolist())
            
            # Check for deletion attempts (Members can't delete)
            deleted_in_ui = original_ids - current_ids
            if deleted_in_ui:
                st.warning("Members cannot delete vendors. Deletion action ignored.")
                return original_df  # Return original to reject changes
            
            # Process each row for adds/updates
            for _, row in edited_df.iterrows():
                vid = row['vendor_id']
                
                # Sanitize all string inputs
                data = {}
                for col in display_columns:
                    if col == 'vendor_id':
                        continue
                    if pd.isna(row[col]):
                        data[col] = None
                    elif isinstance(row[col], str):
                        data[col] = sec.sanitize_input(row[col])
                    else:
                        data[col] = row[col]
                
                # Validate email if present
                if data['contact_email'] and not sec.validate_email(data['contact_email']):
                    st.error(f"Invalid email format: {data['contact_email']}")
                    return original_df
                
                # Validate phone if present
                if data['contact_phone'] and not sec.validate_phone(data['contact_phone']):
                    st.error(f"Invalid phone format: {data['contact_phone']}")
                    return original_df
                
                try:
                    if pd.isna(vid):  # Add new vendor
                        be.add_vendor(
                            event_id=event_id,
                            name=data['name'],
                            service_type=data['service_type'],
                            contact_person=data['contact_person'],
                            contact_email=data['contact_email'],
                            contact_phone=data['contact_phone'],
                            notes=data['notes']
                        )
                    else:  # Update existing vendor
                        original_row = original_df[original_df['vendor_id'] == vid].iloc[0]
                        edited_row_series = pd.Series(data)
                        original_data = {col: original_row[col] for col in data.keys()}
                        original_row_series = pd.Series(original_data)
                        
                        # Only update if data actually changed
                        if not edited_row_series.equals(original_row_series):
                            be.update_vendor(
                                vendor_id=vid,
                                name=data['name'],
                                service_type=data['service_type'],
                                contact_person=data['contact_person'],
                                contact_email=data['contact_email'],
                                contact_phone=data['contact_phone'],
                                status=data['status'],
                                notes=data['notes']
                            )
                except Exception as e:
                    ui.render_error_trace(f"Error updating vendor: {e}")
                    return original_df
            
            st.success("Vendor details updated successfully.")
            return None  # Signal success
        
        # Use the generic data editor component 
        edited_df = ui.render_data_editor(
            data_df=vendors_df,
            editor_key=f"vendor_editor_{event_id}_{user_role}",
            column_config=column_config,
            disabled=(user_role == 'Head'),  # Heads can only view
            on_change_function=process_vendor_updates,
            required_cols=['name']
        )
        
        # If changes were processed successfully, refresh the page
        if edited_df is None:  # None means successful processing
            st.rerun()
            
    except Exception as e:
        ui.render_error_trace(f"Error loading vendor data: {e}")

def render_guest_page(event_id, user_role, assignment=None):
    """Renders the Guest List Management page for Heads and Members."""
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    st.title(f"Guest List Management: {event_info['event_name']}")

    # --- Member-Specific Section: Update Task Status ---
    if user_role == 'Member' and assignment:
        st.subheader("Update Your Task Status")
        current_status_index = TASK_STATUS_OPTIONS.index(assignment['status']) if assignment['status'] in TASK_STATUS_OPTIONS else 0
        new_status = st.selectbox(
            "Mark task as:",
            options=TASK_STATUS_OPTIONS,
            index=current_status_index,
            key=f"guest_status_{assignment['assignment_id']}"
        )
        if st.button("Update Status", key=f"update_guest_status_{assignment['assignment_id']}"):
            if be.update_assignment_status(assignment['assignment_id'], new_status):
                st.success(f"Task status updated to '{new_status}'.")
                st.rerun()
            else:
                st.error("Failed to update task status.")
        st.divider()

    # --- Display Guests (Editable for Member, View-only for Head) ---
    st.subheader("Guest List")
    guests = be.get_guests_for_event(event_id)
    
    # Define display columns first so it's always available
    guest_display_columns = ['guest_id', 'name', 'email', 'phone', 'rsvp_status', 'notes']
    
    # Initialize empty DataFrame if no guests yet
    if not guests:
         # Use the predefined columns for the empty DataFrame
         guests_df = pd.DataFrame(columns=guest_display_columns)
    else:
        guests_df = pd.DataFrame(guests)
        # Ensure correct order and selection of columns using the predefined list
        for col in guest_display_columns:
             if col not in guests_df.columns:
                  guests_df[col] = None
        guests_df = guests_df[guest_display_columns]

    guest_column_config = {
        "guest_id": st.column_config.NumberColumn("ID", disabled=True),
        "name": st.column_config.TextColumn("Name", required=True),
        "email": st.column_config.TextColumn("Email"),
        "phone": st.column_config.TextColumn("Phone"),
        "rsvp_status": st.column_config.SelectboxColumn("RSVP Status", options=GUEST_RSVP_OPTIONS, required=True),
        "notes": st.column_config.TextColumn("Notes", width="large")
    }

    # Disable editing for Head
    edited_guest_df = st.data_editor(
        guests_df,
        key=f"guest_editor_{event_id}_{user_role}",
        num_rows="dynamic", # Members can add/delete in UI
        column_config=guest_column_config,
        hide_index=True,
        use_container_width=True,
        disabled=(user_role == 'Head')
    )

    # --- Process Guest Edits/Updates (Only Members) ---
    if user_role == 'Member' and not edited_guest_df.equals(guests_df):
        original_guest_ids = set(guests_df['guest_id'].tolist())
        current_guest_ids = set(edited_guest_df['guest_id'].dropna().tolist())

        try:
            if edited_guest_df['name'].isnull().any():
                st.error("Guest Name cannot be empty.")
                return

            # Member Logic: Add/Update guests
            for _, row in edited_guest_df.iterrows():
                gid = row['guest_id']
                data = {col: (None if pd.isna(row[col]) else row[col]) for col in guest_display_columns if col != 'guest_id'}

                if pd.isna(gid): # Add new row
                    print(f"Member Adding guest {data['name']}") # Debug
                    be.add_guest(event_id, data['name'], data['email'], data['phone'], data['notes'])
                    # Assume 'Pending' RSVP on add is sufficient
                elif gid in original_guest_ids: # Update existing row
                    original_row = guests_df[guests_df['guest_id'] == gid].iloc[0]
                    edited_row_series = row.drop('guest_id')
                    original_row_series = original_row.drop('guest_id')
                    if not edited_row_series.equals(original_row_series):
                        print(f"Member Updating guest {gid}") # Debug
                        be.update_guest(gid, data['name'], data['email'], data['phone'], data['rsvp_status'], data['notes'])
            
            # Prevent Member Deletes
            deleted_in_ui = original_guest_ids - current_guest_ids
            if deleted_in_ui:
                st.warning("Members cannot delete guests. Deletion action ignored.")
                st.rerun()
            else:
                st.success("Guest list updated by Member.")
                st.rerun()

        except Exception as e:
            st.error(f"Error updating guest list: {e}")
            import traceback
            st.error(traceback.format_exc())

def render_logistics_page(event_id, user_role, assignment=None):
    """Renders the Logistics Management page for Heads and Members."""
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    st.title(f"Logistics Management: {event_info['event_name']}")

    # --- Member-Specific Section: Update Task Status ---
    if user_role == 'Member' and assignment:
        st.subheader("Update Your Task Status")
        current_status_index = TASK_STATUS_OPTIONS.index(assignment['status']) if assignment['status'] in TASK_STATUS_OPTIONS else 0
        new_status = st.selectbox(
            "Mark task as:",
            options=TASK_STATUS_OPTIONS,
            index=current_status_index,
            key=f"logistics_status_{assignment['assignment_id']}"
        )
        if st.button("Update Status", key=f"update_logistics_status_{assignment['assignment_id']}"):
            if be.update_assignment_status(assignment['assignment_id'], new_status):
                st.success(f"Task status updated to '{new_status}'.")
                st.rerun()
            else:
                st.error("Failed to update task status.")
        st.divider()

    # --- Display Logistics Items (Editable for Member, View-only for Head) ---
    st.subheader("Logistics List")
    logistics = be.get_logistics_for_event(event_id)
    
    # Initialize empty DataFrame if no logistics items yet
    logistics_display_columns = ['logistics_id', 'item_name', 'category', 'quantity', 'status', 'supplier', 'cost', 'notes']
    if not logistics:
        logistics_df = pd.DataFrame(columns=logistics_display_columns)
    else:
        logistics_df = pd.DataFrame(logistics)
        # Ensure correct order and selection of columns
        for col in logistics_display_columns:
             if col not in logistics_df.columns:
                  logistics_df[col] = None
        logistics_df = logistics_df[logistics_display_columns]

    logistics_column_config = {
        "logistics_id": st.column_config.NumberColumn("ID", disabled=True),
        "item_name": st.column_config.TextColumn("Item Name", required=True),
        "category": st.column_config.TextColumn("Category"),
        "quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
        "status": st.column_config.SelectboxColumn("Status", options=LOGISTICS_STATUS_OPTIONS, required=True),
        "supplier": st.column_config.TextColumn("Supplier/Source"),
        "cost": st.column_config.NumberColumn("Cost (Per Item)", format="$%.2f"), # Store/edit per item cost
        "notes": st.column_config.TextColumn("Notes", width="large")
    }

    # Disable editing for Head
    edited_logistics_df = st.data_editor(
        logistics_df,
        key=f"logistics_editor_{event_id}_{user_role}",
        num_rows="dynamic", # Members can add/delete in UI
        column_config=logistics_column_config,
        hide_index=True,
        use_container_width=True,
        disabled=(user_role == 'Head')
    )

    # --- Process Logistics Edits/Updates (Only Members) ---
    # Compare with original dataframe (which has per-item cost)
    if user_role == 'Member' and not edited_logistics_df.equals(logistics_df):
        original_logistics_ids = set(logistics_df['logistics_id'].tolist())
        current_logistics_ids = set(edited_logistics_df['logistics_id'].dropna().tolist())

        try:
            if edited_logistics_df['item_name'].isnull().any():
                st.error("Item Name cannot be empty.")
                return

            # Member Logic: Add/Update logistics items
            for _, row in edited_logistics_df.iterrows():
                lid = row['logistics_id']
                # Extract data (cost is now per-item cost)
                data = {col: (None if pd.isna(row[col]) else row[col]) for col in logistics_display_columns if col != 'logistics_id'}

                if pd.isna(lid): # Add new row
                    print(f"Member Adding logistics item {data['item_name']}") # Debug
                    be.add_logistics_item(event_id, data['item_name'], data['category'], data['quantity'], data['supplier'], data['cost'], data['notes'])
                elif lid in original_logistics_ids: # Update existing row
                    original_row = logistics_df[logistics_df['logistics_id'] == lid].iloc[0]
                    edited_row_series = row.drop('logistics_id')
                    original_row_series = original_row.drop('logistics_id')
                    if not edited_row_series.equals(original_row_series):
                        print(f"Member Updating logistics item {lid}") # Debug
                        be.update_logistics_item(lid, data['item_name'], data['category'], data['quantity'], data['status'], data['supplier'], data['cost'], data['notes'])

            # Prevent Member Deletes
            deleted_in_ui = original_logistics_ids - current_logistics_ids
            if deleted_in_ui:
                st.warning("Members cannot delete logistics items. Deletion action ignored.")
                st.rerun()
            else:
                st.success("Logistics list updated by Member.")
                st.rerun()

        except Exception as e:
            st.error(f"Error updating logistics list: {e}")
            import traceback
            st.error(traceback.format_exc())

def render_schedule_page(event_id, user_role, assignment=None):
    """Renders the Schedule Coordination page for Heads and Members."""
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    st.title(f"Schedule Coordination: {event_info['event_name']}")

    # --- Member-Specific Section: Update Task Status ---
    if user_role == 'Member' and assignment:
        st.subheader("Update Your Task Status")
        current_status_index = TASK_STATUS_OPTIONS.index(assignment['status']) if assignment['status'] in TASK_STATUS_OPTIONS else 0
        new_status = st.selectbox(
            "Mark task as:",
            options=TASK_STATUS_OPTIONS,
            index=current_status_index,
            key=f"schedule_status_{assignment['assignment_id']}"
        )
        if st.button("Update Status", key=f"update_schedule_status_{assignment['assignment_id']}"):
            if be.update_assignment_status(assignment['assignment_id'], new_status):
                st.success(f"Task status updated to '{new_status}'.")
                st.rerun()
            else:
                st.error("Failed to update task status.")
        st.divider()

    # --- Display Schedule Items (Editable for Member, View-only for Head) ---
    st.subheader("Event Schedule")
    schedule = be.get_schedule_for_event(event_id)
    
    # Initialize empty DataFrame if no schedule items yet
    schedule_display_columns = ['item_id', 'item_name', 'start_time', 'end_time', 'location', 'responsible_person', 'status', 'notes']
    if not schedule:
        schedule_df = pd.DataFrame(columns=schedule_display_columns)
    else:
        schedule_df = pd.DataFrame(schedule)
        # Ensure DataFrame has all columns, even if some are empty in DB
        for col in schedule_display_columns:
            if col not in schedule_df.columns:
                schedule_df[col] = None
        schedule_df = schedule_df[schedule_display_columns]

    schedule_column_config = {
        "item_id": st.column_config.NumberColumn("ID", disabled=True),
        "item_name": st.column_config.TextColumn("Item/Activity", required=True),
        "start_time": st.column_config.TextColumn("Start (YYYY-MM-DD HH:MM)"), # Text for simplicity in editor
        "end_time": st.column_config.TextColumn("End (YYYY-MM-DD HH:MM)"), # Text for simplicity in editor
        "location": st.column_config.TextColumn("Location"),
        "responsible_person": st.column_config.TextColumn("Responsible"),
        "status": st.column_config.SelectboxColumn("Status", options=SCHEDULE_STATUS_OPTIONS, required=True),
        "notes": st.column_config.TextColumn("Notes", width="large")
    }

    # Disable editing for Head
    edited_schedule_df = st.data_editor(
        schedule_df,
        key=f"schedule_editor_{event_id}_{user_role}",
        num_rows="dynamic", # Members can add/delete in UI
        column_config=schedule_column_config,
        hide_index=True,
        use_container_width=True,
        disabled=(user_role == 'Head')
    )

    # --- Process Schedule Edits/Updates (Only Members) ---
    if user_role == 'Member' and not edited_schedule_df.equals(schedule_df):
        original_schedule_ids = set(schedule_df['item_id'].tolist())
        current_schedule_ids = set(edited_schedule_df['item_id'].dropna().tolist())

        try:
            if edited_schedule_df['item_name'].isnull().any():
                st.error("Item/Activity Name cannot be empty.")
                return

            # Member Logic: Add/Update schedule items
            for _, row in edited_schedule_df.iterrows():
                itemid = row['item_id']
                # Extract data, handling potential NaNs
                data = {col: (None if pd.isna(row[col]) else row[col]) for col in schedule_display_columns if col != 'item_id'}
                # Ensure time strings are handled correctly (e.g., empty strings vs None)
                data['start_time'] = data['start_time'] if data['start_time'] else None
                data['end_time'] = data['end_time'] if data['end_time'] else None

                if pd.isna(itemid): # Add new row
                    print(f"Member Adding schedule item {data['item_name']}") # Debug
                    be.add_schedule_item(event_id, data['item_name'], data['start_time'], data['end_time'], data['location'], data['responsible_person'], data['notes'])
                    # Assume 'Planned' status on add is sufficient
                elif itemid in original_schedule_ids: # Update existing row
                    original_row = schedule_df[schedule_df['item_id'] == itemid].iloc[0]
                    edited_row_series = pd.Series(data)
                    original_row_series = original_row.drop('item_id')
                    if not edited_row_series.equals(original_row_series):
                        print(f"Member Updating schedule item {itemid}") # Debug
                        be.update_schedule_item(itemid, data['item_name'], data['start_time'], data['end_time'], data['location'], data['responsible_person'], data['status'], data['notes'])

            # Prevent Member Deletes
            deleted_in_ui = original_schedule_ids - current_schedule_ids
            if deleted_in_ui:
                st.warning("Members cannot delete schedule items. Deletion action ignored.")
                st.rerun()
            else:
                st.success("Schedule updated by Member.")
                st.rerun()

        except Exception as e:
            st.error(f"Error updating schedule: {e}")
            import traceback
            st.error(traceback.format_exc())

def render_team_chat_page(event_id, user_role, assignment=None):
    """Renders a team chat interface with enhanced security."""
    # Verify access permissions
    if not da.check_user_college_access(st.session_state['user_info']['user_id'], event_id):
        st.error("Access denied: You don't have permission to view this event.")
        return
        
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    
    st.title(f"Team Chat: {event_info['event_name']}")
    
    # Update Task Status (for Members with specific assignment)
    if user_role == 'Member' and assignment:
        with st.expander("Update Task Status", expanded=False):
            ui.render_status_update(assignment)
        st.divider()
    
    # Set up auto-refresh using safe meta refresh
    # This is safer than injecting JavaScript and still provides 
    # a way to auto-refresh the chat
    st.markdown("""
    <div style="text-align: right; margin-bottom: 10px;">
        <small>Chat refreshes every 30 seconds. 
        <a href="#" id="refresh-link" onclick="window.location.reload();">
            Refresh Now
        </a>
        </small>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a manual refresh button as well
    if st.button("Refresh Chat", key="manual_refresh_chat"):
        st.rerun()
    
    # Chat Interface
    chat_container = st.container()
    
    # Message input area at the bottom
    st.divider()
    with st.form("chat_message_form", clear_on_submit=True):
        message_input = st.text_area("Type your message:", height=70, placeholder="Enter your message here...")
        send_button = st.form_submit_button("Send")
    
    if send_button:
        if not message_input or not message_input.strip():
            st.warning("Please enter a message before sending.")
        else:
            # Sanitize input
            message_input = sec.sanitize_input(message_input.strip())
            
            # Validate against spam patterns
            if len(message_input) > 1000:
                st.error("Message is too long. Please limit to 1000 characters.")
            elif re.search(r'(https?://\S+)', message_input) and not st.session_state.get('dev_mode'):
                st.warning("URLs are not allowed in messages for security reasons.")
            else:
                user_id = st.session_state['user_info']['user_id']
                try:
                    message_sent = be.add_chat_message(event_id, user_id, message_input)
                    if message_sent:
                        st.rerun()
                    else:
                        st.error("Failed to send message. Please try again.")
                except Exception as e:
                    ui.render_error_trace(f"Error sending message: {e}")
    
    # Display messages
    with chat_container:
        try:
            messages = be.get_chat_messages(event_id, limit=100)
            
            if len(messages) == 0:
                st.info("No messages yet. Be the first to say hello!")
            else:
                for msg in messages:
                    is_current_user = msg['user_id'] == st.session_state['user_info']['user_id']
                    
                    try:
                        # Format timestamp safely
                        msg_time = datetime.fromisoformat(msg['timestamp']).strftime("%m/%d %I:%M %p")
                    except:
                        msg_time = msg.get('timestamp', 'Unknown time')
                    
                    # Create appropriate columns for message layout
                    cols = st.columns([0.8, 0.2]) if is_current_user else st.columns([0.2, 0.8])
                    
                    with cols[1] if is_current_user else cols[0]:
                        container = st.container(border=True)
                        with container:
                            # Safely display user info
                            sender_name = sec.sanitize_input(msg.get('full_name', 'Unknown'))
                            role_badge = "👑 " if msg.get('role') == 'Head' else ""
                            st.caption(f"{role_badge}{sender_name} - {msg_time}")
                            
                            # Display the message text (already sanitized by the backend)
                            st.write(sec.sanitize_input(msg.get('message_text', '')))
        except Exception as e:
            ui.render_error_trace(f"Error displaying chat messages: {e}")
    
    # Using st.empty and automatically rerun the app after a delay
    # This is a more secure alternative to injecting JavaScript
    if st.session_state.get('chat_last_refresh_time') is None:
        st.session_state['chat_last_refresh_time'] = time_module.time()
        
    # Check if 30 seconds have passed since last refresh
    current_time = time_module.time()
    if current_time - st.session_state.get('chat_last_refresh_time', 0) >= 30:
        st.session_state['chat_last_refresh_time'] = current_time
        time_module.sleep(0.1)  # Small delay to allow UI to render
        st.rerun()  # Trigger a page refresh

# --- Ticket Booking Page ---
def render_book_tickets_page():
    """Displays the ticket booking interface with enhanced security and validation."""
    st.header("Book Event Tickets")
    
    # Display ticket code if booking was successful
    if st.session_state.get('booking_ticket_code'):
        st.success(f"🎉 Ticket booked successfully! Your unique ticket code is: **{st.session_state['booking_ticket_code']}**")
        st.info("Please save this code for entry.")
        st.session_state['booking_ticket_code'] = None  # Clear after displaying once
    
    # Get list of colleges (securely filter from database)
    try:
        colleges_data = be.get_all_college_options()
        colleges = [college for college in colleges_data if college]  # Filter out None/empty values
    except Exception as e:
        ui.render_error_trace(f"Error fetching colleges: {e}")
        colleges = []
    
    # College selection
    if colleges:
        selected_college = st.selectbox(
            "Select Your College", 
            options=["---"] + colleges,
            key="college_selector"
        )
        
        if selected_college != "---":
            # Set selected college in session state with sanitization
            st.session_state['selected_college'] = sec.sanitize_input(selected_college)
            
            try:
                # Fetch events for the selected college that have ticketing enabled
                events = be.get_all_events()
                # Filter events by college and ticketing enabled
                if events:
                    ticketed_events = [
                        e for e in events 
                        if e.get('has_tickets') and e.get('college') == selected_college
                    ]
                else:
                    ticketed_events = []
                    
                if not ticketed_events:
                    st.info(f"There are currently no events available for booking tickets at {selected_college}.")
                else:
                    event_dict = {f"{e['event_name']} ({e['event_date']})": e['event_id'] for e in ticketed_events}
                    selected_event_display = st.selectbox("Select Event", options=["---"] + list(event_dict.keys()))
        
                    if selected_event_display != "---":
                        selected_event_id = event_dict[selected_event_display]
                        st.subheader(f"Booking for: {selected_event_display}")
        
                        with st.form("ticket_booking_form", clear_on_submit=True):
                            st.write("Please provide your details:")
                            user_name = st.text_input("Full Name", key="ticket_user_name")
                            user_class = st.text_input("Class (e.g. F.E, S.E., etc)", key="ticket_user_class")
                            user_roll_no = st.text_input("Roll Number / ID", key="ticket_user_roll")
                            user_address = st.text_area("Address (Optional)", key="ticket_user_address")
        
                            submitted = st.form_submit_button("Confirm Booking")
        
                            if submitted:
                                # Validate inputs
                                form_data = {
                                    "name": sec.sanitize_input(user_name),
                                    "class": sec.sanitize_input(user_class),
                                    "roll_no": sec.sanitize_input(user_roll_no),
                                    "address": sec.sanitize_input(user_address)
                                }
                                
                                # Check required fields
                                is_valid, error_msg = da.validate_form_input(
                                    form_data, 
                                    required_fields=["name", "class", "roll_no"]
                                )
                                
                                if not is_valid:
                                    st.warning(error_msg)
                                else:
                                    try:
                                        # Extra validation for roll number
                                        if not re.match(r'^[a-zA-Z0-9_\-/]+$', form_data["roll_no"]):
                                            st.error("Roll Number contains invalid characters.")
                                        else:
                                            # Call backend function to book ticket
                                            ticket_code = be.book_ticket(
                                                selected_event_id,
                                                form_data["name"],
                                                form_data["class"],
                                                form_data["roll_no"],
                                                form_data["address"]
                                            )
                                            
                                            if ticket_code:
                                                st.session_state['booking_ticket_code'] = ticket_code
                                                st.rerun()  # Rerun to display the success message and code
                                            else:
                                                st.error("Failed to book ticket. Please try again later.")
                                    except Exception as e:
                                        ui.render_error_trace(f"Error booking ticket: {e}")
            except Exception as e:
                ui.render_error_trace(f"Error loading events: {e}")
        else:
            st.info("Please select your college to view available events.")
    else:
        st.info("No colleges with events available for booking currently.")
                            
    if st.button("Back to Login"):
        st.session_state['auth_view'] = 'login'
        st.session_state['booking_ticket_code'] = None  # Clear ticket code
        st.session_state['selected_college'] = None  # Clear selected college
        st.rerun()
        
# --- Ticket Management Page (for Assigned Members) ---
def render_ticket_management_page(event_id, user_role, assignment=None):
    """Displays booked tickets for the event - for assigned members."""
    event_info = be.get_event_by_id(event_id)
    if not event_info:
        st.error("Selected event not found.")
        return
    st.title(f"Ticket Management: {event_info['event_name']}")

    # Add member task status update section if needed
    if user_role == 'Member' and assignment:
        st.subheader("Update Your Task Status")
        current_status_index = TASK_STATUS_OPTIONS.index(assignment['status']) if assignment['status'] in TASK_STATUS_OPTIONS else 0
        new_status = st.selectbox(
            "Mark task as:",
            options=TASK_STATUS_OPTIONS,
            index=current_status_index,
            key=f"ticket_status_{assignment['assignment_id']}"
        )
        if st.button("Update Status", key=f"update_ticket_status_{assignment['assignment_id']}"):
            if be.update_assignment_status(assignment['assignment_id'], new_status):
                st.success(f"Task status updated to '{new_status}'.")
                st.rerun()
            else:
                st.error("Failed to update task status.")
        st.divider()

    st.subheader("Booked Tickets")
    tickets = be.get_tickets_for_event(event_id)

    if tickets:
        tickets_df = pd.DataFrame(tickets)
        st.dataframe(tickets_df[['ticket_id', 'ticket_code', 'user_name', 'user_class', 'user_roll_number', 'booking_timestamp']], use_container_width=True)
    else:
        st.info("No tickets have been booked for this event yet.")

# --- Profile Page --- 
def render_profile_page():
    """Renders the user profile page with secure validation."""
    st.title("👤 Your Profile")
    
    user_info = st.session_state.get('user_info', {})
    user_id = user_info.get('user_id')
    current_college = st.session_state.get('college_info', {}).get(user_id, "Not Set")
    
    if not user_id:
        st.error("Could not load user information.")
        return
        
    st.subheader("Current Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Full Name:** {user_info.get('full_name', 'N/A')}")
        st.write(f"**Username:** {user_info.get('username', 'N/A')}")
    with col2:
        st.write(f"**Role:** {user_info.get('role', 'N/A')}")
        st.write(f"**College:** {current_college}")
        
    st.divider()
    st.subheader("Update Information")
    
    with st.form("profile_update_form"):
        new_fullname = st.text_input("Full Name", value=user_info.get('full_name', ''))
        new_college = st.text_input("College Name", value=current_college if current_college != "Not Set" else "")
        
        # Password Update Section
        st.markdown("**Update Password (Optional)**")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password",
                                     help="Password must be at least 8 characters long with letters and numbers")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Update Profile")
        
        if submitted:
            # Sanitize inputs
            form_data = {
                "full_name": sec.sanitize_input(new_fullname),
                "college": sec.sanitize_input(new_college),
            }
            
            update_data = {}
            password_update = False
            
            # Basic Info Update
            if form_data["full_name"] and form_data["full_name"] != user_info.get('full_name'):
                update_data['full_name'] = form_data["full_name"]
                
            if form_data["college"] and form_data["college"] != current_college:
                update_data['college'] = form_data["college"]
                
            # Password Update Logic
            if current_password or new_password or confirm_password:
                if not current_password:
                    st.warning("Please enter your current password to change it.")
                elif not new_password:
                    st.warning("Please enter a new password.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long.")
                elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$', new_password):
                    st.error("Password must contain at least one letter and one number.")
                elif new_password != confirm_password:
                    st.warning("New passwords do not match.")
                else:
                    # Verify current password with backend
                    password_verified = be.verify_password(user_id, current_password)
                    
                    if password_verified:
                        update_data['password'] = new_password
                        password_update = True
                    else:
                        st.error("Incorrect current password.")
                        
            # Proceed with update if there's data to update
            if update_data:
                try:
                    success = be.update_user_profile(user_id, update_data)
                    if success:
                        st.success("Profile updated successfully!")
                        
                        # Update local session state
                        if 'full_name' in update_data:
                            st.session_state['user_info']['full_name'] = update_data['full_name']
                        if 'college' in update_data:
                            st.session_state['college_info'][user_id] = update_data['college']
                            
                        # Force relogin if password was changed
                        if password_update:
                            st.warning("Your password has been changed. Please log in again with your new password.")
                            if st.button("Log out and Log in again"):
                                logout()
                        else:
                            st.rerun()
                    else:
                        st.error("Failed to update profile. Please try again.")
                except Exception as e:
                    ui.render_error_trace(f"Error updating profile: {e}")
            elif not update_data and not (current_password or new_password or confirm_password):
                st.info("No changes detected.")

# --- Main Application ---
def main():
    """Main function to run the Streamlit app with enhanced security and organization."""
    # Inject Custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    # Initialize security and session state
    sec.init_session_state()
    init_auth_state()

    # Check for session timeout if logged in
    if st.session_state.get('logged_in'):
        if not sec.check_session_active():
            logout(expired=True)
            return

    # Login/Logout Handling
    if not st.session_state.get('logged_in', False):
        render_auth_page()
        return

    # Display any task status success messages
    ui.display_success_alert()

    # User is logged in - get navigation from sidebar
    user_info = st.session_state['user_info']
    nav_result = ui.render_sidebar(user_info)

    # If logout was triggered, stop execution
    if not st.session_state.get('logged_in', False):
        return

    # Process navigation result
    if nav_result['type'] == 'main_page':
        page = nav_result['page']
        
        # Render the appropriate main page
        if page == "Dashboard":
            render_dashboard()
        elif page == "Profile":
            render_profile_page()
        elif user_info['role'] == 'Head':
            if page == "Create Event":
                render_create_event_page()
            elif page == "Create Member":
                render_create_member_page()
            elif page == "Assign Tasks":
                render_assign_task_page()
            else:
                st.error(f"Unknown page: {page}")
                render_dashboard()
    
    elif nav_result['type'] == 'event_page':
        page = nav_result['page']
        event_id = nav_result['event_id']
        
        # Verify user has access to this event based on college
        if not da.check_user_college_access(user_info['user_id'], event_id):
            st.error("Access denied: You don't have permission to view this event.")
            render_dashboard()
            return
            
        # Handle different page types based on user role
        if user_info['role'] == 'Head':
            # Heads see all task pages
            if page in TASK_PAGE_MAP:
                page_render_function_name = TASK_PAGE_MAP[page]
                render_function = globals().get(page_render_function_name)
                
                if render_function:
                    if page in ["Task Tracking", "Reports"]:
                        render_function(event_id)
                    else:
                        render_function(event_id, user_info['role'])
                else:
                    st.error(f"Error: Page function {page_render_function_name} not found.")
            else:
                st.error(f"Unknown page: {page}")
        
        elif user_info['role'] == 'Member':
            # Members only see their assigned tasks
            if page == "Team Chat":
                # Team Chat is always available
                render_team_chat_page(event_id, user_info['role'], None)
            else:
                # Get assignment details from nav_result
                assignment = nav_result.get('assignment')
                
                # Use helper function to get the appropriate render function
                render_function = get_render_function_for_task(page)
                
                if render_function and assignment:
                    # Verify assignment access
                    if da.check_assignment_access(user_info['user_id'], assignment['assignment_id']):
                        render_function(event_id, user_info['role'], assignment)
                    else:
                        st.error("Access denied: You don't have permission to view this task.")
                        render_dashboard()
                elif not render_function:
                    st.error(f"No page found for task '{page}'")
                    render_dashboard()
                else:
                    st.error("Assignment details not found")
                    render_dashboard()

if __name__ == "__main__":
    main() 