"""
SharePoint Routes for Housing Pipeline Pro
Handles SharePoint integration endpoints for project management.
"""

from flask import Blueprint, request, jsonify
from src.models.database import db, Project
from src.services.sharepoint_service import SharePointService
import os

sharepoint_bp = Blueprint('sharepoint', __name__)

@sharepoint_bp.route('/projects/<int:project_id>/create-site', methods=['POST'])
def create_project_sharepoint_site(project_id):
    """Create SharePoint site for an existing project"""
    try:
        # Get project
        project = Project.query.get_or_404(project_id)
        
        # Check if SharePoint site already exists
        if project.sharepoint_site_url:
            return jsonify({
                'success': False,
                'error': 'SharePoint site already exists for this project',
                'existing_url': project.sharepoint_site_url
            }), 400
        
        # Get request data
        data = request.get_json() or {}
        owner_user_id = data.get('owner_user_id')
        
        if not owner_user_id:
            return jsonify({
                'success': False,
                'error': 'owner_user_id is required'
            }), 400
        
        # Check if Azure credentials are configured
        if not all([os.getenv('AZURE_TENANT_ID'), os.getenv('AZURE_CLIENT_ID'), os.getenv('AZURE_CLIENT_SECRET')]):
            return jsonify({
                'success': False,
                'error': 'Azure credentials not configured. Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET environment variables.'
            }), 500
        
        # Initialize SharePoint service
        sharepoint_service = SharePointService()
        
        # Get funding sources for folder structure
        funding_sources = [app.funding_source.name for app in project.applications if app.funding_source]
        
        # Create complete project site
        site_result = sharepoint_service.create_complete_project_site(
            project_name=project.name,
            project_description=f"Affordable housing project in {project.city}, {project.state}",
            owner_user_id=owner_user_id,
            funding_sources=funding_sources
        )
        
        # Update project with SharePoint information
        project.sharepoint_site_url = site_result['sharepoint_site_url']
        project.sharepoint_email = site_result['sharepoint_email']
        project.sharepoint_group_id = site_result['group_id']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'project_id': project.id,
                'project_name': project.name,
                'group_id': site_result['group_id'],
                'sharepoint_site_url': site_result['sharepoint_site_url'],
                'sharepoint_email': site_result['sharepoint_email'],
                'folders_created': len(site_result['created_folders']),
                'message': 'SharePoint site created successfully'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to create SharePoint site: {str(e)}'
        }), 500

@sharepoint_bp.route('/projects/<int:project_id>/add-member', methods=['POST'])
def add_project_team_member(project_id):
    """Add team member to project SharePoint site"""
    try:
        # Get project
        project = Project.query.get_or_404(project_id)
        
        if not project.sharepoint_site_url:
            return jsonify({
                'success': False,
                'error': 'No SharePoint site exists for this project'
            }), 400
        
        # Get request data
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id is required'
            }), 400
        
        # Initialize SharePoint service
        sharepoint_service = SharePointService()
        
        # Use stored group ID
        if not project.sharepoint_group_id:
            return jsonify({
                'success': False,
                'error': 'No SharePoint group ID found for this project'
            }), 400
        
        # Add member to group
        success = sharepoint_service.add_group_member(project.sharepoint_group_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'project_id': project.id,
                    'user_id': user_id,
                    'message': 'Team member added successfully'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add team member'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to add team member: {str(e)}'
        }), 500

@sharepoint_bp.route('/projects/<int:project_id>/upload-document', methods=['POST'])
def upload_project_document(project_id):
    """Upload document to project SharePoint site"""
    try:
        # Get project
        project = Project.query.get_or_404(project_id)
        
        if not project.sharepoint_site_url:
            return jsonify({
                'success': False,
                'error': 'No SharePoint site exists for this project'
            }), 400
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Get optional folder path
        folder_path = request.form.get('folder_path', '')
        
        # Use stored group ID
        if not project.sharepoint_group_id:
            return jsonify({
                'success': False,
                'error': 'No SharePoint group ID found for this project'
            }), 400
        
        # Initialize SharePoint service
        sharepoint_service = SharePointService()
        
        # Upload file
        file_content = file.read()
        upload_result = sharepoint_service.upload_file(
            group_id=project.sharepoint_group_id,
            file_path=file.filename,
            file_content=file_content,
            folder_path=folder_path
        )
        
        return jsonify({
            'success': True,
            'data': {
                'project_id': project.id,
                'file_name': file.filename,
                'folder_path': folder_path,
                'file_id': upload_result.get('id'),
                'web_url': upload_result.get('webUrl'),
                'message': 'Document uploaded successfully'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to upload document: {str(e)}'
        }), 500

@sharepoint_bp.route('/projects/<int:project_id>/sharepoint-info', methods=['GET'])
def get_project_sharepoint_info(project_id):
    """Get SharePoint information for a project"""
    try:
        # Get project
        project = Project.query.get_or_404(project_id)
        
        return jsonify({
            'success': True,
            'data': {
                'project_id': project.id,
                'project_name': project.name,
                'sharepoint_site_url': project.sharepoint_site_url,
                'sharepoint_email': project.sharepoint_email,
                'has_sharepoint_site': bool(project.sharepoint_site_url)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sharepoint_bp.route('/config/check', methods=['GET'])
def check_sharepoint_config():
    """Check if SharePoint integration is properly configured"""
    try:
        required_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            return jsonify({
                'success': False,
                'configured': False,
                'missing_variables': missing_vars,
                'message': f'Missing required environment variables: {", ".join(missing_vars)}'
            })
        
        # Test authentication
        try:
            sharepoint_service = SharePointService()
            token = sharepoint_service._get_access_token()
            
            return jsonify({
                'success': True,
                'configured': True,
                'message': 'SharePoint integration is properly configured',
                'has_valid_token': bool(token)
            })
            
        except Exception as auth_error:
            return jsonify({
                'success': False,
                'configured': False,
                'error': f'Authentication failed: {str(auth_error)}',
                'message': 'Environment variables are set but authentication failed'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sharepoint_bp.route('/folder-structure/default', methods=['GET'])
def get_default_folder_structure():
    """Get the default folder structure for projects"""
    try:
        sharepoint_service = SharePointService()
        
        # Get funding sources from query params
        funding_sources = request.args.getlist('funding_sources')
        
        folder_structure = sharepoint_service.get_default_folder_structure(funding_sources)
        
        return jsonify({
            'success': True,
            'data': {
                'folder_structure': folder_structure,
                'total_folders': len(folder_structure)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

