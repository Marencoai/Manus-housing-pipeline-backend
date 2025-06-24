from flask import Blueprint, request, jsonify
from src.models.database import db, Application, Project, FundingSource, ApplicationStatus
from datetime import datetime, date

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/', methods=['GET'])
def get_applications():
    """Get all applications with optional filtering"""
    try:
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        funding_source_id = request.args.get('funding_source_id')
        
        query = Application.query
        
        if project_id:
            query = query.filter(Application.project_id == project_id)
        if status:
            query = query.filter(Application.status == ApplicationStatus(status))
        if funding_source_id:
            query = query.filter(Application.funding_source_id == funding_source_id)
            
        applications = query.all()
        
        result = []
        for app in applications:
            result.append({
                'id': app.id,
                'project': {
                    'id': app.project.id,
                    'name': app.project.name,
                    'city': app.project.city,
                    'state': app.project.state
                },
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
                'notes': app.notes,
                'documents_folder': app.documents_folder,
                'created_at': app.created_at.isoformat() if app.created_at else None,
                'updated_at': app.updated_at.isoformat() if app.updated_at else None
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

@applications_bp.route('/<int:application_id>', methods=['GET'])
def get_application(application_id):
    """Get a specific application by ID"""
    try:
        app = Application.query.get_or_404(application_id)
        
        result = {
            'id': app.id,
            'project': {
                'id': app.project.id,
                'name': app.project.name,
                'address': app.project.address,
                'city': app.project.city,
                'state': app.project.state,
                'total_units': app.project.total_units,
                'total_cost': app.project.total_cost
            },
            'funding_source': {
                'id': app.funding_source.id,
                'name': app.funding_source.name,
                'type': app.funding_source.type.value,
                'agency': app.funding_source.agency,
                'description': app.funding_source.description,
                'requirements': app.funding_source.requirements,
                'website_url': app.funding_source.website_url
            },
            'status': app.status.value,
            'application_round': app.application_round,
            'requested_amount': app.requested_amount,
            'awarded_amount': app.awarded_amount,
            'submission_date': app.submission_date.isoformat() if app.submission_date else None,
            'decision_date': app.decision_date.isoformat() if app.decision_date else None,
            'notes': app.notes,
            'documents_folder': app.documents_folder,
            'created_at': app.created_at.isoformat() if app.created_at else None,
            'updated_at': app.updated_at.isoformat() if app.updated_at else None
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

@applications_bp.route('/', methods=['POST'])
def create_application():
    """Create a new application"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('project_id'):
            return jsonify({
                'success': False,
                'error': 'Project ID is required'
            }), 400
            
        if not data.get('funding_source_id'):
            return jsonify({
                'success': False,
                'error': 'Funding source ID is required'
            }), 400
        
        # Verify project and funding source exist
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({
                'success': False,
                'error': 'Project not found'
            }), 404
            
        funding_source = FundingSource.query.get(data['funding_source_id'])
        if not funding_source:
            return jsonify({
                'success': False,
                'error': 'Funding source not found'
            }), 404
        
        # Parse dates if provided
        submission_date = None
        decision_date = None
        
        if data.get('submission_date'):
            submission_date = datetime.strptime(data['submission_date'], '%Y-%m-%d').date()
        if data.get('decision_date'):
            decision_date = datetime.strptime(data['decision_date'], '%Y-%m-%d').date()
        
        # Create application
        application = Application(
            project_id=data['project_id'],
            funding_source_id=data['funding_source_id'],
            status=ApplicationStatus(data['status']) if data.get('status') else ApplicationStatus.DRAFT,
            application_round=data.get('application_round'),
            requested_amount=data.get('requested_amount'),
            awarded_amount=data.get('awarded_amount'),
            submission_date=submission_date,
            decision_date=decision_date,
            notes=data.get('notes'),
            documents_folder=data.get('documents_folder')
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': application.id,
                'message': 'Application created successfully'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@applications_bp.route('/<int:application_id>', methods=['PUT'])
def update_application(application_id):
    """Update an existing application"""
    try:
        application = Application.query.get_or_404(application_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'status' in data:
            application.status = ApplicationStatus(data['status'])
        if 'application_round' in data:
            application.application_round = data['application_round']
        if 'requested_amount' in data:
            application.requested_amount = data['requested_amount']
        if 'awarded_amount' in data:
            application.awarded_amount = data['awarded_amount']
        if 'submission_date' in data:
            if data['submission_date']:
                application.submission_date = datetime.strptime(data['submission_date'], '%Y-%m-%d').date()
            else:
                application.submission_date = None
        if 'decision_date' in data:
            if data['decision_date']:
                application.decision_date = datetime.strptime(data['decision_date'], '%Y-%m-%d').date()
            else:
                application.decision_date = None
        if 'notes' in data:
            application.notes = data['notes']
        if 'documents_folder' in data:
            application.documents_folder = data['documents_folder']
            
        application.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': application.id,
                'message': 'Application updated successfully'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@applications_bp.route('/dashboard-stats', methods=['GET'])
def get_application_stats():
    """Get application dashboard statistics"""
    try:
        # Applications by status
        status_stats = {}
        for status in ApplicationStatus:
            count = Application.query.filter(Application.status == status).count()
            status_stats[status.value] = count
        
        # Recent applications (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_applications = Application.query.filter(
            Application.created_at >= thirty_days_ago
        ).count()
        
        # Funding metrics
        total_requested = db.session.query(db.func.sum(Application.requested_amount)).scalar() or 0
        total_awarded = db.session.query(db.func.sum(Application.awarded_amount)).scalar() or 0
        
        # Success rate
        total_applications = Application.query.count()
        approved_applications = Application.query.filter(
            Application.status == ApplicationStatus.APPROVED
        ).count()
        
        success_rate = (approved_applications / total_applications * 100) if total_applications > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'status_distribution': status_stats,
                'recent_applications': recent_applications,
                'total_requested': total_requested,
                'total_awarded': total_awarded,
                'success_rate': round(success_rate, 1),
                'total_applications': total_applications
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

