"""
SharePoint Integration Service for Housing Pipeline Pro
Handles Microsoft Graph API integration for automated SharePoint site creation and document management.
"""

import os
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

class SharePointService:
    """Service class for SharePoint integration via Microsoft Graph API"""
    
    def __init__(self):
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.access_token = None
        self.token_expires_at = None
        
    def _get_access_token(self) -> str:
        """Get or refresh access token for Microsoft Graph API"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
            
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
        
        return self.access_token
    
    def _make_graph_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Microsoft Graph API"""
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.graph_base_url}{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()
        return response.json() if response.content else {}
    
    def create_project_group(self, project_name: str, project_description: str, owner_user_id: str) -> Tuple[str, str]:
        """
        Create Microsoft 365 group for project (which automatically creates SharePoint site)
        
        Args:
            project_name: Name of the project
            project_description: Description of the project
            owner_user_id: Azure AD user ID of the project owner
            
        Returns:
            Tuple of (group_id, mail_nickname)
        """
        # Create safe mail nickname (lowercase, no spaces, alphanumeric only)
        mail_nickname = ''.join(c.lower() for c in project_name if c.isalnum())[:64]
        
        group_data = {
            "description": f"{project_description} - Affordable Housing Project",
            "displayName": project_name,
            "groupTypes": ["Unified"],
            "mailEnabled": True,
            "mailNickname": mail_nickname,
            "securityEnabled": False,
            "owners@odata.bind": [
                f"https://graph.microsoft.com/v1.0/users/{owner_user_id}"
            ]
        }
        
        result = self._make_graph_request('POST', '/groups', group_data)
        return result['id'], mail_nickname
    
    def get_sharepoint_site(self, group_id: str) -> Dict:
        """
        Get SharePoint site information for a Microsoft 365 group
        
        Args:
            group_id: Microsoft 365 group ID
            
        Returns:
            SharePoint site information
        """
        return self._make_graph_request('GET', f'/groups/{group_id}/sites/root')
    
    def wait_for_sharepoint_site(self, group_id: str, max_wait_minutes: int = 10) -> Optional[Dict]:
        """
        Wait for SharePoint site to be provisioned after group creation
        
        Args:
            group_id: Microsoft 365 group ID
            max_wait_minutes: Maximum time to wait in minutes
            
        Returns:
            SharePoint site information or None if timeout
        """
        end_time = datetime.now() + timedelta(minutes=max_wait_minutes)
        
        while datetime.now() < end_time:
            try:
                site_info = self.get_sharepoint_site(group_id)
                if site_info:
                    return site_info
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Site not ready yet, wait and retry
                    time.sleep(30)
                    continue
                else:
                    raise
                    
        return None
    
    def create_folder_structure(self, group_id: str, folder_structure: List[str]) -> List[Dict]:
        """
        Create standardized folder structure in SharePoint document library
        
        Args:
            group_id: Microsoft 365 group ID
            folder_structure: List of folder names to create
            
        Returns:
            List of created folder information
        """
        created_folders = []
        
        for folder_name in folder_structure:
            folder_data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            try:
                result = self._make_graph_request(
                    'POST', 
                    f'/groups/{group_id}/drive/root/children',
                    folder_data
                )
                created_folders.append(result)
            except requests.exceptions.HTTPError as e:
                # Log error but continue with other folders
                print(f"Error creating folder '{folder_name}': {e}")
                
        return created_folders
    
    def add_group_member(self, group_id: str, user_id: str) -> bool:
        """
        Add user to Microsoft 365 group (grants SharePoint access)
        
        Args:
            group_id: Microsoft 365 group ID
            user_id: Azure AD user ID to add
            
        Returns:
            True if successful
        """
        member_data = {
            "@odata.id": f"https://graph.microsoft.com/v1.0/users/{user_id}"
        }
        
        try:
            self._make_graph_request('POST', f'/groups/{group_id}/members/$ref', member_data)
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def upload_file(self, group_id: str, file_path: str, file_content: bytes, folder_path: str = "") -> Dict:
        """
        Upload file to SharePoint document library
        
        Args:
            group_id: Microsoft 365 group ID
            file_path: Name of the file
            file_content: Binary content of the file
            folder_path: Optional folder path (e.g., "Project Documents")
            
        Returns:
            Upload result information
        """
        if folder_path:
            endpoint = f'/groups/{group_id}/drive/root:/{folder_path}/{file_path}:/content'
        else:
            endpoint = f'/groups/{group_id}/drive/root:/{file_path}:/content'
            
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/octet-stream'
        }
        
        url = f"{self.graph_base_url}{endpoint}"
        response = requests.put(url, headers=headers, data=file_content)
        response.raise_for_status()
        
        return response.json()
    
    def get_default_folder_structure(self, funding_sources: List[str] = None) -> List[str]:
        """
        Get standardized folder structure for affordable housing projects
        
        Args:
            funding_sources: List of funding sources to create specific folders for
            
        Returns:
            List of folder names
        """
        base_folders = [
            "01 - Project Planning",
            "02 - Financial Documents",
            "03 - Legal & Compliance", 
            "04 - Construction Documents",
            "05 - Marketing & Leasing",
            "06 - Environmental Reports",
            "07 - Permits & Approvals",
            "08 - Team Communications"
        ]
        
        if funding_sources:
            for i, source in enumerate(funding_sources, 9):
                base_folders.append(f"{i:02d} - {source} Application")
                
        return base_folders
    
    def create_complete_project_site(self, project_name: str, project_description: str, 
                                   owner_user_id: str, funding_sources: List[str] = None) -> Dict:
        """
        Complete workflow: Create group, wait for SharePoint site, create folder structure
        
        Args:
            project_name: Name of the project
            project_description: Description of the project  
            owner_user_id: Azure AD user ID of the project owner
            funding_sources: List of funding sources for folder creation
            
        Returns:
            Complete project site information
        """
        # Step 1: Create Microsoft 365 group
        group_id, mail_nickname = self.create_project_group(
            project_name, project_description, owner_user_id
        )
        
        # Step 2: Wait for SharePoint site provisioning
        site_info = self.wait_for_sharepoint_site(group_id)
        if not site_info:
            raise Exception("SharePoint site provisioning timed out")
        
        # Step 3: Create folder structure
        folder_structure = self.get_default_folder_structure(funding_sources)
        created_folders = self.create_folder_structure(group_id, folder_structure)
        
        return {
            'group_id': group_id,
            'mail_nickname': mail_nickname,
            'sharepoint_site_url': site_info.get('webUrl'),
            'sharepoint_email': f"{mail_nickname}@{self.tenant_id.split('.')[0]}.onmicrosoft.com",
            'site_info': site_info,
            'created_folders': created_folders
        }

