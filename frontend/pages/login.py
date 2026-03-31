"""
Login Page for Health Literacy Assistant
"""

import streamlit as st

def show_login():
    """Display login form"""
    
    st.title("🏥 Health Literacy Assistant")
    st.markdown("### Please log in to continue")
    
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    if st.button("Login", type="primary"):
        if username and password:
            response = st.session_state.api_client.login(username, password)
            
            if response:
                st.session_state.logged_in = True
                st.session_state.token = response.get('access_token')
                st.session_state.user_role = response.get('role')
                st.session_state.patient_id = response.get('patient_id')
                st.session_state.username = response.get('username')
                st.session_state.user_name = response.get('name')
                
                st.success(f"Welcome, {response.get('name')}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        else:
            st.warning("Please enter both username and password")
    
    # Demo credentials
    st.info("Demo credentials: john/password123, jane/password123, admin/admin123")
