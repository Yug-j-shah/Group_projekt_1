import streamlit as st
import pandas as pd
from datetime import date
import security as sec
import data_access as da
import backend as be

# --- Constants ---
TASK_STATUS_OPTIONS = ['Assigned', 'In Progress', 'Completed']
VENDOR_STATUS_OPTIONS = ['Pending', 'Contacted', 'Booked', 'Rejected']
GUEST_RSVP_OPTIONS = ['Pending', 'Attending', 'Declined', 'Maybe']
LOGISTICS_STATUS_OPTIONS = ['Required', 'Sourced', 'Delivered', 'Setup', 'Returned']
SCHEDULE_STATUS_OPTIONS = ['Planned', 'Confirmed', 'Ongoing', 'Completed']

# --- UI Components ---

def render_sidebar(user_info):
    """Render the sidebar navigation based on user role."""
    st.sidebar.title("EventEase")
    st.sidebar.write(f"Welcome, {user_info['full_name']} ({user_info['role']})")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state.pop('user_info', None)
        st.session_state.pop('selected_event_id', None)
        st.session_state.pop('page', None)
        st.session_state.pop('booking_ticket_code', None) 
        st.session_state.pop('session_id', None)
        st.session_state.pop('login_time', None)
        st.success("Logged out successfully.")
        st.rerun()
        
    st.sidebar.divider()
    
    if user_info['role'] == 'Head':
        return render_head_sidebar(user_info)
    else:
        return render_member_sidebar(user_info)

def render_head_sidebar(user_info):
    """Render sidebar navigation for Head users."""
    st.sidebar.header("Management")
    
    # Main options including Profile
    main_page_options = ["Dashboard", "Profile", "Create Event", "Create Member", "Assign Tasks", "Events"]
    selected_main_page = st.sidebar.radio("Go to:", main_page_options, key="main_page_select")
    
    if selected_main_page not in ["Events", "Profile"]:
        st.session_state['page'] = selected_main_page
        st.session_state.pop('selected_event_id', None)
        return {"type": "main_page", "page": selected_main_page}
    elif selected_main_page == "Profile":
        st.session_state['page'] = "Profile"
        st.session_state.pop('selected_event_id', None)
        return {"type": "main_page", "page": "Profile"}
    else:  # Events selected
        # Get all events and filter by Head's college
        events = be.get_all_events()
        user_id = user_info['user_id']
        user_college = st.session_state['college_info'].get(user_id)
        
        if user_college:
            filtered_events = [e for e in events if e.get('college') == user_college]
        else:
            filtered_events = []
            
        if not filtered_events:
            st.sidebar.warning("No events available for your college. Please create an event first.")
            st.session_state['page'] = 'Dashboard'
            st.session_state.pop('selected_event_id', None)
            return {"type": "main_page", "page": "Dashboard"}
        else:
            event_dict = {f"{e['event_name']} (ID: {e['event_id']})": e['event_id'] for e in filtered_events}
            selected_event_display = st.sidebar.radio(
                "Select Event:", 
                options=list(event_dict.keys()), 
                index=None, 
                key="head_event_select"
            )

            if selected_event_display:
                event_id = event_dict[selected_event_display]
                st.session_state['selected_event_id'] = event_id
                
                # Get the event data to check ticketing status
                event_data = next((e for e in filtered_events if e['event_id'] == event_id), None)
                
                # Determine which task pages to show
                task_pages = list(be.TASK_PAGE_MAP.keys())
                
                # Remove Ticket Management if event doesn't have ticketing
                if event_data and not event_data.get('has_tickets') and 'Ticket Management' in task_pages:
                    task_pages.remove('Ticket Management')
                
                selected_task_page = st.sidebar.radio(
                    "Select Event Page:", 
                    options=task_pages, 
                    key="event_page_select"
                )
                
                st.session_state['page'] = selected_task_page
                return {"type": "event_page", "page": selected_task_page, "event_id": event_id}
            else:
                # No event selected
                st.session_state['page'] = 'Dashboard'
                st.session_state.pop('selected_event_id', None)
                return {"type": "main_page", "page": "Dashboard"}

def render_member_sidebar(user_info):
    """Render sidebar navigation for Member users."""
    st.sidebar.header("Navigation")
    
    # Standard pages + Tasks based on selected event
    base_pages = ["Dashboard", "Profile"]
    selected_page_group = st.sidebar.radio("Area:", ["General", "Event Tasks"], key="member_area_select")

    if selected_page_group == "General":
        selected_page = st.sidebar.radio("Go to:", base_pages, key="member_general_select")
        st.session_state['page'] = selected_page
        st.session_state.pop('selected_event_id', None)
        return {"type": "main_page", "page": selected_page}
    else:  # Event Tasks selected
        st.sidebar.header("Your Tasks")
        
        # Get member's college
        user_id = user_info['user_id']
        member_college = st.session_state['college_info'].get(user_id)
        
        if not member_college:
            st.sidebar.warning("Your account is not associated with a college. Cannot view event tasks.")
            st.session_state['page'] = 'Dashboard'
            st.session_state.pop('selected_event_id', None)
            return {"type": "main_page", "page": "Dashboard"}
        
        # Get user's assignments
        assignments = be.get_user_assignments(user_id)
        assigned_event_ids = sorted(list(set([a['event_id'] for a in assignments])))
        
        # Get event details and filter by member's college
        member_events = []
        for eid in assigned_event_ids:
            event_details = be.get_event_by_id(eid)
            if event_details and event_details.get('college') == member_college:
                member_events.append(event_details)
                
        event_dict = {f"{e['event_name']} (ID: {e['event_id']})": e['event_id'] for e in member_events}

        if not event_dict:
            st.sidebar.info(f"You have not been assigned to any events for {member_college} yet.")
            st.session_state['page'] = 'Dashboard'
            st.session_state.pop('selected_event_id', None)
            return {"type": "main_page", "page": "Dashboard"}
        
        selected_event_display = st.sidebar.radio(
            "Select Event:",
            options=list(event_dict.keys()),
            index=None,
            key="member_event_select"
        )

        if selected_event_display:
            event_id = event_dict[selected_event_display]
            st.session_state['selected_event_id'] = event_id
            
            # Get user's assignments for this event
            event_assignments = [a for a in assignments if a['event_id'] == event_id]
            task_page_options = [a['task_name'] for a in event_assignments]
            
            # Filter out Head-only pages
            task_page_options = [p for p in task_page_options if p not in ["Task Tracking", "Reports"]]
            
            # Always add Team Chat
            if "Team Chat" not in task_page_options:
                task_page_options.append("Team Chat")
            
            selected_task_page = st.sidebar.radio("Go to Task:", task_page_options, key="nav_radio_member_task")
            st.session_state['page'] = selected_task_page
            
            # Find the specific assignment if one exists
            assignment = next((a for a in event_assignments if a['task_name'] == selected_task_page), None)
            
            return {
                "type": "event_page", 
                "page": selected_task_page, 
                "event_id": event_id,
                "assignment": assignment
            }
        else:
            st.session_state['page'] = 'Dashboard'
            st.session_state.pop('selected_event_id', None)
            return {"type": "main_page", "page": "Dashboard"}

def render_status_update(assignment, success_message=None):
    """Render task status update component for members."""
    if not assignment:
        return
        
    st.subheader("Update Your Task Status")
    current_status_index = TASK_STATUS_OPTIONS.index(assignment['status']) if assignment['status'] in TASK_STATUS_OPTIONS else 0
    new_status = st.selectbox(
        "Mark task as:",
        options=TASK_STATUS_OPTIONS,
        index=current_status_index,
        key=f"status_{assignment['assignment_id']}"
    )
    
    if st.button("Update Status", key=f"update_status_{assignment['assignment_id']}"):
        if be.update_assignment_status(assignment['assignment_id'], new_status):
            task_name = assignment.get('task_name', 'Task')
            st.success(f"Task status updated to '{new_status}'.")
            st.session_state['task_status_success'] = f"Task '{task_name}' status updated to '{new_status}'."
            st.rerun()
        else:
            st.error("Failed to update task status.")
            
    st.divider()

def render_data_editor(data_df, 
                       editor_key, 
                       column_config, 
                       disabled=False, 
                       on_change_function=None, 
                       required_cols=None):
    """
    Render a data editor with validation.
    Returns the edited dataframe if changes were made
    """
    # Initialize an empty DataFrame with correct columns if data is empty
    if data_df.empty and column_config:
        data_df = pd.DataFrame(columns=list(column_config.keys()))
        
    # Render the data editor
    edited_df = st.data_editor(
        data_df,
        key=editor_key,
        num_rows="dynamic",
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        disabled=disabled
    )
    
    # Check for changes and validate
    if not edited_df.equals(data_df) and not disabled:
        # Validate required columns
        if required_cols and any(edited_df[col].isnull().any() for col in required_cols):
            missing_cols = [col for col in required_cols if edited_df[col].isnull().any()]
            st.error(f"The following fields cannot be empty: {', '.join(missing_cols)}")
            return None
            
        # Call the on_change function if provided
        if on_change_function:
            result = on_change_function(data_df, edited_df)
            if result is not None:
                return result
                
        return edited_df
    
    return None

def render_error_trace(error, include_trace=False):
    """Render error messages safely."""
    st.error(f"Error: {str(error)}")
    if include_trace and st.session_state.get('dev_mode'):
        import traceback
        st.warning("Developer Mode: Stack Trace")
        st.code(traceback.format_exc())

def display_success_alert():
    """Display success message from task status update if it exists."""
    if 'task_status_success' in st.session_state:
        st.success(st.session_state['task_status_success'])
        del st.session_state['task_status_success'] 