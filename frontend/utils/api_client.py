"""
API Client for RAG-Powered Health Literacy Assistant
Communicates with backend containing RAG pipeline
"""

import requests
import streamlit as st
from typing import Dict, Any, Optional, List

class APIClient:
    """Client for RAG backend API"""
    
    def __init__(self, base_url: str = "http://backend:5000"):
        self.base_url = base_url
        self.timeout = 30
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request to backend"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to RAG engine at {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            st.error("⏰ Request timeout - RAG engine is processing")
            return None
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Error: {e}")
            return None
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            return None
    
    # ========== RAG Pipeline Endpoints ==========
    
    def explain_medical_term(self, term: str, context: str = None) -> Optional[Dict]:
        """
        Get plain-language explanation for a medical term using RAG
        
        Args:
            term: Medical term to explain
            context: Optional patient context (e.g., "patient has diabetes")
            
        Returns:
            Explanation with sources
        """
        endpoint = "/api/rag/explain"
        payload = {"term": term, "context": context}
        return self._make_request("POST", endpoint, json=payload)
    
    def translate_fhir_resource(self, resource_type: str, resource_data: Dict) -> Optional[Dict]:
        """
        Translate a FHIR resource to plain language
        
        Args:
            resource_type: Type of FHIR resource (Observation, Condition, etc.)
            resource_data: The FHIR resource data
            
        Returns:
            Plain language translation
        """
        endpoint = "/api/rag/translate"
        payload = {"resource_type": resource_type, "resource_data": resource_data}
        return self._make_request("POST", endpoint, json=payload)
    
    def get_patient_data(self, patient_id: str) -> Optional[Dict]:
        """
        Get patient data from database
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Patient data including FHIR resources
        """
        endpoint = f"/api/patient/{patient_id}"
        return self._make_request("GET", endpoint)
    
    def ask_question(self, question: str, patient_context: Dict = None) -> Optional[Dict]:
        """
        Ask a follow-up question to the RAG assistant
        
        Args:
            question: User's question
            patient_context: Optional patient context
            
        Returns:
            Answer with sources
        """
        endpoint = "/api/rag/ask"
        payload = {"question": question, "context": patient_context}
        return self._make_request("POST", endpoint, json=payload)
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of RAG engine and knowledge base"""
        result = self._make_request("GET", "/api/health")
        if result:
            return {
                "backend": result.get("status") == "healthy",
                "database": result.get("knowledge_base", {}).get("connected", False)
            }
        return {"backend": False, "database": False}
