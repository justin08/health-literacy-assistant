"""
Frontend Container - Streamlit Application
Integrates with Backend and Database containers
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from utils.api_client import APIClient

st.set_page_config(
    page_title="Figma Design Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_api_client():
    api_url = os.getenv("API_URL", "http://backend:5000")
    return APIClient(base_url=api_url)

def init_session_state():
    if 'api_client' not in st.session_state:
        st.session_state.api_client = init_api_client()
    if 'design_data' not in st.session_state:
        st.session_state.design_data = None
    if 'file_key' not in st.session_state:
        st.session_state.file_key = ""
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "dashboard"

init_session_state()

# Sidebar
with st.sidebar:
    st.title("🎨 Figma Dashboard")
    st.markdown("---")
    
    # System Status
    st.subheader("🔌 System Status")
    health = st.session_state.api_client.health_check()
    
    col1, col2 = st.columns(2)
    with col1:
        if health.get("backend"):
            st.success("✅ Backend")
        else:
            st.error("❌ Backend")
    with col2:
        if health.get("database"):
            st.success("✅ Database")
        else:
            st.error("❌ Database")
    
    st.markdown("---")
    
    # Navigation
    st.subheader("📱 Navigation")
    view = st.radio(
        "Select View",
        ["🏠 Dashboard", "🎨 Import Design", "💾 Saved Designs"],
        label_visibility="collapsed"
    )
    
    if view == "🏠 Dashboard":
        st.session_state.current_view = "dashboard"
    elif view == "🎨 Import Design":
        st.session_state.current_view = "import"
    elif view == "💾 Saved Designs":
        st.session_state.current_view = "saved"
    
    st.markdown("---")
    
    # Figma Input (only in import view)
    if st.session_state.current_view == "import":
        st.subheader("📁 Figma File")
        file_key = st.text_input(
            "Enter Figma File Key",
            value=st.session_state.file_key,
            placeholder="e.g., fzYhvQpqhZJlYi37E9rC8H"
        )
        
        if file_key != st.session_state.file_key:
            st.session_state.file_key = file_key
            st.session_state.design_data = None
        
        if st.button("🚀 Load Design", type="primary", use_container_width=True):
            if file_key:
                with st.spinner("Fetching from Figma..."):
                    response = st.session_state.api_client.get_figma_file(file_key, save_to_db=True)
                    if response:
                        st.session_state.design_data = response
                        st.success("✅ Design loaded!")
                        st.balloons()
    
    st.markdown("---")
    st.caption("Frontend Container v1.0")

# Main Content
if st.session_state.current_view == "dashboard":
    st.title("🎨 Figma Design Dashboard")
    st.markdown("Welcome to your design dashboard!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**🖥️ Frontend**\nStreamlit App\nPort: 8501")
    with col2:
        st.info("**⚙️ Backend**\nFastAPI Server\nPort: 5000")
    with col3:
        st.info("**🗄️ Database**\nPostgreSQL\nPort: 5432")
    
    st.markdown("---")
    
    # Show recent designs
    st.subheader("📋 Recent Designs")
    saved = st.session_state.api_client.get_saved_designs(limit=5)
    if saved:
        df = pd.DataFrame(saved)
        st.dataframe(df[['id', 'name', 'created_at']], use_container_width=True)
    else:
        st.info("No saved designs yet. Go to 'Import Design' to add some.")

elif st.session_state.current_view == "import":
    st.title("🎨 Import Figma Design")
    
    if st.session_state.design_data:
        design = st.session_state.design_data
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Design Name", design.get('name', 'Unknown'))
        with col2:
            st.metric("Version", design.get('version', 'N/A'))
        with col3:
            stats = design.get('statistics', {})
            st.metric("Components", stats.get('total_components', 0))
        
        st.markdown("---")
        
        if st.button("💾 Save to Database"):
            saved = st.session_state.api_client.save_figma_design(design)
            if saved:
                st.success(f"Saved! Design ID: {saved.get('id')}")

elif st.session_state.current_view == "saved":
    st.title("💾 Saved Designs")
    
    designs = st.session_state.api_client.get_saved_designs(limit=100)
    if designs:
        df = pd.DataFrame(designs)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No saved designs found.")
