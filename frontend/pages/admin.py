"""
Admin Panel - View all patients (admin only)
"""

import streamlit as st

def show_admin_panel():
    """Display admin panel with all patients"""
    
    st.title("Admin Panel")
    
    # Check if user is admin
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    # Get all patients
    patients = st.session_state.api_client.get_all_patients()
    
    if patients:
        st.subheader(f"All Patients ({len(patients)})")
        
        # Simple list display
        for patient in patients:
            st.write(f"{patient['name']} ({patient['id']})")
    else:
        st.info("No patients found")
