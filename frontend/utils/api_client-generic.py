"""
API Client for communicating with backend container
"""

import requests
import streamlit as st
from typing import Dict, Any, Optional, List

class APIClient:
    """Client for backend API communication"""
    
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
            st.error(f"Cannot connect to backend at {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            st.error("Request timeout - backend is slow")
            return None
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return None
    
    def get_figma_file(self, file_key: str, save_to_db: bool = True) -> Optional[Dict[str, Any]]:
        """Fetch Figma file data from backend"""
        endpoint = f"/api/figma/{file_key}"
        params = {"save_to_db": save_to_db}
        return self._make_request("GET", endpoint, params=params)
    
    def get_saved_designs(self, limit: int = 50, offset: int = 0) -> Optional[List[Dict]]:
        """Get saved designs from database container"""
        endpoint = "/api/database/designs"
        params = {"limit": limit, "offset": offset}
        return self._make_request("GET", endpoint, params=params)
    
    def save_figma_design(self, design_data: Dict) -> Optional[Dict]:
        """Save Figma design to database container"""
        endpoint = "/api/database/designs"
        return self._make_request("POST", endpoint, json=design_data)
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all services"""
        result = self._make_request("GET", "/api/health")
        if result:
            return {
                "backend": result.get("status") == "healthy",
                "database": result.get("database", {}).get("connected", False)
            }
        return {"backend": False, "database": False}
