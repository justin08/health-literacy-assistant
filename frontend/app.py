"""
Health Literacy Assistant - Frontend Container
Built with assistance from AI (Claude) for:
- Streamlit app structure
- API client integration
- Docker configuration

Human modifications:
- Customized for FHIR resource display (Conditions, Lab Results)
- Added medical terminology translations
- Multi-page navigation structure
- Deployed to cloud platform

Sprint 3 Deliverable: Working frontend container with mock data
Backend integration ready for Sprint 4
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add utils to path
sys.path.append(os.path.dirname(__file__))

from utils.api_client import APIClient

# Page configuration
st.set_page_config(
    page_title="Health Literacy Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API client
@st.cache_resource
def init_api_client():
    """Initialize the API client for backend communication"""
    api_url = os.getenv("API_URL", "http://backend:5000")
    return APIClient(base_url=api_url)

# Initialize session state
def init_session_state():
    if 'api_client' not in st.session_state:
        st.session_state.api_client = init_api_client()
    if 'selected_term' not in st.session_state:
        st.session_state.selected_term = None

init_session_state()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("🏥 Health Literacy Assistant")
    st.markdown("*Making medical language clear*")
    st.markdown("---")
    
    # Navigation
    st.subheader("Navigation")
    page = st.radio(
        "Select View",
        ["📊 Dashboard", "📋 Medical Records", "💬 Translation Assistant"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # System Status
    st.subheader("System Status")
    health = st.session_state.api_client.health_check()
    
    if health.get("backend"):
        st.success("✅ Backend Ready")
    else:
        st.warning("⚠️ Demo Mode (Backend not connected)")
    
    if health.get("database"):
        st.success("✅ Knowledge Base Connected")
    else:
        st.info("📚 Using local knowledge base")
    
    st.markdown("---")
    
    # Patient selector (mock data for now)
    st.subheader("Patient")
    patient = st.selectbox(
        "Select Patient",
        ["Patient #1001 (Synthetic)", "Patient #1002 (Synthetic)", "Patient #1003 (Synthetic)"],
        help="Synthetic data from Synthea"
    )
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")
    st.caption("Powered by RAG Technology")

# ==================== MAIN CONTENT ====================

# DASHBOARD VIEW
if page == "📊 Dashboard":
    st.title("Welcome to Your Health Literacy Assistant")
    st.markdown("### Understanding your health information, made simple")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Medical Terms Translated", "24", delta="+12 this week")
    with col2:
        st.metric("Readability Score", "8.2", delta="-1.5", help="Lower is better (target: ≤8)")
    with col3:
        st.metric("Trusted Sources", "156", delta="+23")
    
    st.markdown("---")
    
    # How it works
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("How It Works")
        st.markdown("""
        1. **View** your medical records in plain language
        2. **Select** any medical term you don't understand
        3. **Get** a clear, plain-language explanation
        4. **Learn** from trusted medical sources
        """)
    
    with col2:
        st.subheader("Quick Demo")
        
        demo_terms = ["Hypertension", "Diabetes", "Hyperlipidemia"]
        selected = st.selectbox("Try a medical term:", demo_terms)
        
        if st.button("Explain This Term", type="primary"):
            if selected == "Hypertension":
                st.success("""
                **Plain Language:**
                
                **Hypertension** means high blood pressure.
                
                Think of it like water flowing through a garden hose. When the water pressure is too high, it puts extra strain on the hose. Similarly, high blood pressure strains your blood vessels and heart over time.
                
                **Sources:** American Heart Association, MedlinePlus
                """)
            elif selected == "Diabetes":
                st.success("""
                **Plain Language:**
                
                **Diabetes** means your body has trouble using sugar for energy.
                
                Normally, your body turns food into sugar and uses insulin to move that sugar into your cells for energy. With diabetes, this process doesn't work properly, causing sugar to build up in your blood.
                
                **Sources:** American Diabetes Association, CDC
                """)
            else:
                st.success("""
                **Plain Language:**
                
                **Hyperlipidemia** means high cholesterol.
                
                Cholesterol is a waxy substance in your blood. Too much of it can build up in your blood vessels, making it harder for blood to flow smoothly.
                
                **Sources:** American Heart Association, Mayo Clinic
                """)
    
    st.markdown("---")
    st.info("💡 **Tip:** Navigate to 'Medical Records' to see your actual health data, or use the 'Translation Assistant' for any medical term.")

# MEDICAL RECORDS VIEW
elif page == "📋 Medical Records":
    st.title("Your Medical Records")
    st.markdown("*Click on any item to get a plain-language explanation*")
    
    # Create tabs for different FHIR resources
    tab1, tab2, tab3 = st.tabs(["🏷️ Conditions", "🧪 Lab Results", "💊 Medications"])
    
    with tab1:
        st.subheader("Active Conditions")
        
        # Mock conditions data (would come from backend/FHIR)
        conditions = [
            {"Condition": "Essential hypertension", "Status": "Active", "Diagnosed": "2024-01-15"},
            {"Condition": "Type 2 diabetes mellitus", "Status": "Active", "Diagnosed": "2023-08-22"},
            {"Condition": "Hyperlipidemia", "Status": "Active", "Diagnosed": "2024-01-15"}
        ]
        
        df_conditions = pd.DataFrame(conditions)
        st.dataframe(df_conditions, use_container_width=True)
        
        st.caption("💡 Click on a condition in the Translation Assistant to get an explanation")
    
    with tab2:
        st.subheader("Recent Lab Results")
        
        # Mock lab results
        labs = [
            {"Test": "Hemoglobin A1c", "Result": "7.2%", "Reference": "<5.7%", "Flag": "⚠️ High"},
            {"Test": "LDL Cholesterol", "Result": "130 mg/dL", "Reference": "<100 mg/dL", "Flag": "⚠️ High"},
            {"Test": "Blood Pressure", "Result": "135/85", "Reference": "<120/80", "Flag": "⚠️ Elevated"}
        ]
        
        df_labs = pd.DataFrame(labs)
        st.dataframe(df_labs, use_container_width=True)
        
        st.caption("⚠️ Results outside normal range may need attention. Ask your doctor for guidance.")
    
    with tab3:
        st.subheader("Current Medications")
        
        # Mock medications
        medications = [
            {"Medication": "Lisinopril 10mg", "Instructions": "Take once daily", "Purpose": "Blood pressure"},
            {"Medication": "Metformin 500mg", "Instructions": "Take with meals", "Purpose": "Blood sugar"},
            {"Medication": "Atorvastatin 20mg", "Instructions": "Take at bedtime", "Purpose": "Cholesterol"}
        ]
        
        for med in medications:
            with st.expander(f"💊 {med['Medication']}"):
                st.write(f"**Instructions:** {med['Instructions']}")
                st.write(f"**Purpose:** {med['Purpose']}")
                if st.button(f"Simplify Instructions", key=med['Medication']):
                    st.session_state.selected_term = med['Medication']
                    st.info(f"Simplifying: {med['Medication']} - This will connect to RAG backend in Sprint 4")
    
    st.markdown("---")
    st.warning("⚠️ **Demo Data Notice:** This is synthetic patient data from Synthea. Real medical records would appear here when backend is connected.")

# TRANSLATION ASSISTANT VIEW
elif page == "💬 Translation Assistant":
    st.title("Medical Translation Assistant")
    st.markdown("*From clinical jargon to plain language*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Medical Term")
        
        # Dropdown for medical terms
        medical_terms = [
            "Hypertension",
            "Type 2 Diabetes Mellitus",
            "Hyperlipidemia", 
            "Myocardial Infarction",
            "Chronic Kidney Disease",
            "Hemoglobin A1c",
            "LDL Cholesterol"
        ]
        
        selected_term = st.selectbox("Select a medical term:", medical_terms)
        
        # Or allow free text input
        custom_term = st.text_input("Or enter your own term:", placeholder="e.g., Atrial fibrillation")
        
        term_to_translate = custom_term if custom_term else selected_term
        
        st.markdown("---")
        st.markdown(f"**Selected Term:** `{term_to_translate}`")
        
        # Context for better translation
        context = st.text_area(
            "Context (optional):",
            placeholder="e.g., This appears in my lab results",
            help="Adding context helps provide a more accurate translation"
        )
    
    with col2:
        st.subheader("💡 Plain Language Translation")
        
        if st.button("Translate", type="primary", use_container_width=True):
            with st.spinner("Generating plain-language explanation..."):
                # Mock translations (would come from backend RAG)
                translations = {
                    "Hypertension": """
                    **What it means:** High blood pressure
                    
                    **Simple explanation:** Your blood pushes against your artery walls with too much force. Think of it like water flowing through a garden hose - when the pressure is too high, it puts extra strain on the hose.
                    
                    **What you can do:**
                    • Take prescribed medications
                    • Reduce salt intake
                    • Exercise regularly
                    • Monitor blood pressure at home
                    
                    **Sources:** American Heart Association, MedlinePlus (NIH)
                    """,
                    
                    "Type 2 Diabetes Mellitus": """
                    **What it means:** High blood sugar
                    
                    **Simple explanation:** Your body has trouble using sugar for energy. Normally, insulin helps sugar move into your cells. With type 2 diabetes, your body doesn't use insulin properly.
                    
                    **What you can do:**
                    • Monitor blood sugar levels
                    • Follow meal plan
                    • Take medications as prescribed
                    • Stay physically active
                    
                    **Sources:** American Diabetes Association, CDC
                    """,
                    
                    "Hyperlipidemia": """
                    **What it means:** High cholesterol
                    
                    **Simple explanation:** Too much fat (cholesterol) in your blood. This can build up in your blood vessels over time.
                    
                    **What you can do:**
                    • Eat heart-healthy foods
                    • Exercise regularly
                    • Take cholesterol medications if prescribed
                    
                    **Sources:** American Heart Association, Mayo Clinic
                    """,
                    
                    "Hemoglobin A1c": """
                    **What it means:** Average blood sugar over 3 months
                    
                    **Simple explanation:** This test shows how well your blood sugar has been controlled. Lower numbers mean better control.
                    
                    **Target:** Below 7% for most adults with diabetes
                    
                    **Sources:** American Diabetes Association
                    """
                }
                
                # Get translation or show placeholder
                translation = translations.get(term_to_translate, """
                **RAG Translation (Coming in Sprint 4)**
                
                This term will be translated using our RAG pipeline with:
                • Vector database of trusted medical sources
                • LLM-powered plain language generation
                • Citation of authoritative references
                
                **For now, this is a demo of the UI.**
                """)
                
                st.markdown(translation)
                
                # Add citation footer
                st.markdown("---")
                st.caption("📚 **Sources:** American Heart Association, American Diabetes Association, MedlinePlus, Mayo Clinic")
        
        else:
            st.info("👈 Select a medical term and click 'Translate' to see a plain-language explanation")
    
    # Additional resources
    st.markdown("---")
    st.subheader("📚 Learn More")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Trusted Health Resources:**")
        st.markdown("""
        • [MedlinePlus](https://medlineplus.gov) - NIH
        • [Mayo Clinic](https://mayoclinic.org) - Patient Education
        • [CDC](https://cdc.gov) - Health Information
        """)
    with col2:
        st.markdown("**Questions to Ask Your Doctor:**")
        st.markdown("""
        • What do my lab results mean?
        • Are my medications working?
        • What lifestyle changes would help?
        • When should I follow up?
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    <p>Health Literacy Assistant v1.0 | Sprint 3 Demo</p>
    <p>⚠️ This is a demo version with mock data. Real backend integration coming in Sprint 4.</p>
    <p>Always consult your healthcare provider for medical advice.</p>
</div>
""", unsafe_allow_html=True)
