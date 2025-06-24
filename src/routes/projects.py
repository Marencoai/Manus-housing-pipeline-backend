from flask import Blueprint, request, jsonify
from src.models.database import db, Project, Client, ProjectPhase
from datetime import datetime

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """Get all projects with optional filtering"""
    try:
        phase = request.args.get('phase')
        client_id = request.args.get('client_id')
        
        query = Project.query
        
        if phase:
            query = query.filter(Project.phase == ProjectPhase(phase))
        if client_id:
            query = query.filter(Project.client_id == client_id)
            
        projects = query.all()
        
        result = []
        for project in projects:
            # Calculate funding secured and gap
            total_awarded = sum([app.awarded_amount or 0 for app in project.applications])
            funding_gap = (project.total_cost or 0) - total_awarded
            
            result.append({
                'id': project.id,
                'name': project.name,
                'address': project.address,
                'city': project.city,
                'state': project.state,
                'zip_code': project.zip_code,
                'phase': project.phase.value if project.phase else None,
                'project_type': project.project_type,
                'population_type': project.population_type,
                'housing_type': project.housing_type,
                'total_units': project.total_units,
                'total_cost': project.total_cost,
                'funding_secured': total_awarded,
                'funding_gap': funding_gap,
                'client': {
                    'id': project.client.id,
                    'name': project.client.name,
                    'organization': project.client.organization
                } if project.client else None,
                'sharepoint_site_url': project.sharepoint_site_url,
                'sharepoint_email': project.sharepoint_email,
                'applications_count': len(project.applications),
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None
            })
            
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project by ID"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Calculate funding metrics
        total_awarded = sum([app.awarded_amount or 0 for app in project.applications])
        total_requested = sum([app.requested_amount or 0 for app in project.applications])
        funding_gap = (project.total_cost or 0) - total_awarded
        
        # Get applications with funding source details
        applications = []
        for app in project.applications:
            applications.append({
                'id': app.id,
                'funding_source': {
                    'id': app.funding_source.id,
                    'name': app.funding_source.name,
                    'type': app.funding_source.type.value,
                    'agency': app.funding_source.agency
                },
                'status': app.status.value,
                'application_round': app.application_round,
                'requested_amount': app.requested_amount,
                'awarded_amount': app.awarded_amount,
                'submission_date': app.submission_date.isoformat() if app.submission_date else None,
                'decision_date': app.decision_date.isoformat() if app.decision_date else None,
                'notes': app.notes
            })
        
        result = {
            'id': project.id,
            'name': project.name,
            'address': project.address,
            'city': project.city,
            'state': project.state,
            'zip_code': project.zip_code,
            'phase': project.phase.value if project.phase else None,
            'project_type': project.project_type,
            'population_type': project.population_type,
            'housing_type': project.housing_type,
            'total_units': project.total_units,
            'total_cost': project.total_cost,
            'funding_secured': total_awarded,
            'funding_requested': total_requested,
            'funding_gap': funding_gap,
            'client': {
                'id': project.client.id,
                'name': project.client.name,
                'organization': project.client.organization,
                'email': project.client.email,
                'phone': project.client.phone
            } if project.client else None,
            'sharepoint_site_url': project.sharepoint_site_url,
            'sharepoint_email': project.sharepoint_email,
            'applications': applications,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@projects_bp.route('/', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Project name is required'
            }), 400
            
        if not data.get('client_id'):
            return jsonify({
                'success': False,
                'error': 'Client ID is required'
            }), 400
        
        # Verify client exists
        client = Client.query.get(data['client_id'])
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Create project
        project = Project(
            name=data['name'],
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            phase=ProjectPhase(data['phase']) if data.get('phase') else ProjectPhase.PRE_DEVELOPMENT,
            project_type=data.get('project_type'),
            population_type=data.get('population_type'),
            housing_type=data.get('housing_type'),
            total_units=data.get('total_units'),
            total_cost=data.get('total_cost'),
            client_id=data['client_id'],
            sharepoint_site_url=data.get('sharepoint_site_url'),
            sharepoint_email=data.get('sharepoint_email')
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': project.id,
                'name': project.name,
                'message': 'Project created successfully'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            project.name = data['name']
        if 'address' in data:
            project.address = data['address']
        if 'city' in data:
            project.city = data['city']
        if 'state' in data:
            project.state = data['state']
        if 'zip_code' in data:
            project.zip_code = data['zip_code']
        if 'phase' in data:
            project.phase = ProjectPhase(data['phase'])
        if 'project_type' in data:
            project.project_type = data['project_type']
        if 'population_type' in data:
            project.population_type = data['population_type']
        if 'housing_type' in data:
            project.housing_type = data['housing_type']
        if 'total_units' in data:
            project.total_units = data['total_units']
        if 'total_cost' in data:
            project.total_cost = data['total_cost']
        if 'sharepoint_site_url' in data:
            project.sharepoint_site_url = data['sharepoint_site_url']
        if 'sharepoint_email' in data:
            project.sharepoint_email = data['sharepoint_email']
            
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': project.id,
                'name': project.name,
                'message': 'Project updated successfully'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@projects_bp.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_projects = Project.query.count()
        
        # Projects by phase
        phase_stats = {}
        for phase in ProjectPhase:
            count = Project.query.filter(Project.phase == phase).count()
            phase_stats[phase.value] = count
        
        # Calculate total funding metrics
        all_projects = Project.query.all()
        total_cost = sum([p.total_cost or 0 for p in all_projects])
        total_secured = 0
        total_requested = 0
        
        for project in all_projects:
            total_secured += sum([app.awarded_amount or 0 for app in project.applications])
            total_requested += sum([app.requested_amount or 0 for app in project.applications])
        
        total_gap = total_cost - total_secured
        
        return jsonify({
            'success': True,
            'data': {
                'total_projects': total_projects,
                'phase_distribution': phase_stats,
                'financial_summary': {
                    'total_project_cost': total_cost,
                    'total_funding_secured': total_secured,
                    'total_funding_requested': total_requested,
                    'total_funding_gap': total_gap
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

