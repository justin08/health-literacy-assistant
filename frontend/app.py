"""
Health Literacy Assistant - Frontend Container
Standalone Mock Version - Clean Build
"""

import streamlit as st
from utils import APIClient
from pages.login import show_login
from pages.admin import show_admin_panel

# Page config
st.set_page_config(
    page_title="Health Literacy Assistant",
    page_icon="",
    layout="wide"
)

# ==================== INITIALIZATION ====================
@st.cache_resource
def init_api_client():
    return APIClient()

def init_session_state():
    """Initialize all session variables"""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = init_api_client()
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'patient_id' not in st.session_state:
        st.session_state.patient_id = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    if 'viewing_patient' not in st.session_state:
        st.session_state.viewing_patient = None
    if 'selected_patient_name' not in st.session_state:
        st.session_state.selected_patient_name = None

init_session_state()

# ==================== AUTHENTICATION ====================
if not st.session_state.logged_in:
    show_login()
    st.stop()

# Set token
st.session_state.api_client.set_token(st.session_state.get('token', ''))

# ==================== SIDEBAR ====================
with st.sidebar:
    # User info
    st.markdown(f"""
    <div style='text-align:center; padding:1rem; background:#F0F2F6; border-radius:12px;'>
        <div style='font-size:2rem;'></div>
        <h3>{st.session_state.user_name}</h3>
        <p>{st.session_state.user_role.upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Patient selector
    if st.session_state.user_role == 'patient':
        current_patient = st.session_state.patient_id
        st.info(f"Patient ID: {current_patient}")
    else:
        patients = st.session_state.api_client.get_all_patients()
        if patients:
            patient_names = [p['name'] for p in patients]
            # Use session state to track selected patient
            default_index = 0
            if st.session_state.selected_patient_name in patient_names:
                default_index = patient_names.index(st.session_state.selected_patient_name)
            
            selected_name = st.selectbox(
                "Select Patient", 
                patient_names,
                index=default_index,
                key="patient_selector"
            )
            
            # Update session state when selection changes
            if selected_name != st.session_state.selected_patient_name:
                st.session_state.selected_patient_name = selected_name
                st.session_state.viewing_patient = next(p['id'] for p in patients if p['name'] == selected_name)
                # Force refresh of current page
                st.rerun()
            
            current_patient = st.session_state.viewing_patient
    
    st.markdown("---")
    
    # Navigation buttons
    if st.button("Dashboard", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()
    
    if st.button("Medical Records", use_container_width=True):
        st.session_state.current_page = "records"
        st.rerun()
    
    if st.button("Translation Assistant", use_container_width=True):
        st.session_state.current_page = "assistant"
        st.rerun()
    
    if st.session_state.user_role == 'admin':
        if st.button("Admin Panel", use_container_width=True):
            st.session_state.current_page = "admin"
            st.rerun()
    
    st.markdown("---")
    
    # Status
    st.success("Mock Mode")
    st.caption(f"Logged in: {st.session_state.user_name}")
    
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.patient_id = None
        st.session_state.user_name = None
        st.session_state.selected_patient_name = None
        st.session_state.viewing_patient = None
        st.rerun()

# ==================== MAIN CONTENT ====================

# Admin Panel
if st.session_state.current_page == "admin" and st.session_state.user_role == 'admin':
    show_admin_panel()
    st.stop()

# Get current patient ID
if st.session_state.user_role == 'admin':
    patient_id = st.session_state.viewing_patient
else:
    patient_id = st.session_state.patient_id

# Dashboard
if st.session_state.current_page == "dashboard":
    st.title(f"Welcome, {st.session_state.user_name}!")
    st.markdown("### Your Health Literacy Assistant")
    
    # Get patient data for stats
    obs = st.session_state.api_client.get_patient_observations(patient_id) if patient_id else []
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lab Results", len(obs) if obs else 0)
    with col2:
        st.metric("Conditions", 0)
    with col3:
        st.metric("Medications", 0)
    
    st.markdown("---")
    
    # Quick Demo
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("How It Works")
        st.markdown("""
        1. View your medical records
        2. Select any medical term
        3. Get a plain-language explanation
        """)
    
    with col2:
        st.subheader("Try It Now")
        demo_term = st.selectbox("Select a medical term:", ["Hypertension", "Diabetes", "A1c"])
        if st.button("Explain", type="primary"):
            result = st.session_state.api_client.explain_medical_term(demo_term)
            if result:
                st.success(result['plain_language'])
                st.caption(f"Sources: {', '.join(result['sources'])}")

# Medical Records
elif st.session_state.current_page == "records":
    st.title("Medical Records")
    
    if not patient_id:
        st.error("No patient selected")
    else:
        # Show current patient name
        patients = st.session_state.api_client.get_all_patients()
        current_name = next((p['name'] for p in patients if p['id'] == patient_id), patient_id)
        st.info(f"Viewing: {current_name}")
        
        # Get observations
        obs = st.session_state.api_client.get_patient_observations(patient_id)
        
        if obs and len(obs) > 0:
            st.success(f"Found {len(obs)} measurements for this patient")
            
            # Display all measurements
            st.subheader("All Measurements")
            
            # Group by test name for better organization
            tests = {}
            for o in obs:
                test_name = o['display']
                if test_name not in tests:
                    tests[test_name] = []
                tests[test_name].append(o)
            
            # Show each test group
            for test_name, values in sorted(tests.items()):
                with st.expander(f"{test_name} ({len(values)} records)"):
                    for v in values:
                        flag = " " if v.get('flag') else ""
                        date = v.get('effective_date', 'Unknown')
                        value = v.get('value', 'N/A')
                        unit = v.get('unit', '')
                        st.write(f"  {flag}{value} {unit} - {date}")
        else:
            st.warning("No measurements found for this patient")
            st.info("This patient has no observation data in the JSON file.")

# Translation Assistant
elif st.session_state.current_page == "assistant":
    st.title("Medical Translation Assistant")
    st.markdown("Enter a medical term to get a plain-language explanation.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        term = st.text_input("Medical term:", placeholder="e.g., hypertension, diabetes, a1c")
        context = st.text_area("Context (optional):", placeholder="e.g., This appears in my lab results")
        translate_clicked = st.button("Translate", type="primary", use_container_width=True)
    
    with col2:
        if translate_clicked and term:
            with st.spinner("Generating explanation..."):
                result = st.session_state.api_client.explain_medical_term(term, context)
                if result:
                    st.markdown("### Plain Language")
                    st.success(result['plain_language'])
                    st.markdown(f"**Sources:** {', '.join(result['sources'])}")
                    st.caption(f"**Readability:** Grade {result['readability_score']}")
        elif translate_clicked and not term:
            st.warning("Please enter a medical term")
        else:
            st.info("Enter a term and click Translate")

# Footer
st.markdown("---")
st.caption("Health Literacy Assistant | Mock Mode | Data from cleaned_patient_data.json")
