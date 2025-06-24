from flask import Blueprint, request, jsonify
from src.models.database import db, FundingSource, FundingSourceType
from datetime import datetime

funding_sources_bp = Blueprint('funding_sources', __name__)

@funding_sources_bp.route('/', methods=['GET'])
def get_funding_sources():
    """Get all funding sources with optional filtering"""
    try:
        source_type = request.args.get('type')
        is_active = request.args.get('is_active')
        
        query = FundingSource.query
        
        if source_type:
            query = query.filter(FundingSource.type == FundingSourceType(source_type))
        if is_active is not None:
            query = query.filter(FundingSource.is_active == (is_active.lower() == 'true'))
            
        funding_sources = query.all()
        
        result = []
        for source in funding_sources:
            result.append({
                'id': source.id,
                'name': source.name,
                'type': source.type.value,
                'agency': source.agency,
                'description': source.description,
                'application_deadline': source.application_deadline.isoformat() if source.application_deadline else None,
                'award_amount_min': source.award_amount_min,
                'award_amount_max': source.award_amount_max,
                'requirements': source.requirements,
                'contact_info': source.contact_info,
                'website_url': source.website_url,
                'is_active': source.is_active,
                'applications_count': len(source.applications),
                'created_at': source.created_at.isoformat() if source.created_at else None
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

@funding_sources_bp.route('/<int:source_id>', methods=['GET'])
def get_funding_source(source_id):
    """Get a specific funding source by ID"""
    try:
        source = FundingSource.query.get_or_404(source_id)
        
        # Get applications for this funding source
        applications = []
        for app in source.applications:
            applications.append({
                'id': app.id,
                'project': {
                    'id': app.project.id,
                    'name': app.project.name,
                    'city': app.project.city,
                    'state': app.project.state
                },
                'status': app.status.value,
                'application_round': app.application_round,
                'requested_amount': app.requested_amount,
                'awarded_amount': app.awarded_amount,
                'submission_date': app.submission_date.isoformat() if app.submission_date else None
            })
        
        result = {
            'id': source.id,
            'name': source.name,
            'type': source.type.value,
            'agency': source.agency,
            'description': source.description,
            'application_deadline': source.application_deadline.isoformat() if source.application_deadline else None,
            'award_amount_min': source.award_amount_min,
            'award_amount_max': source.award_amount_max,
            'requirements': source.requirements,
            'contact_info': source.contact_info,
            'website_url': source.website_url,
            'is_active': source.is_active,
            'applications': applications,
            'created_at': source.created_at.isoformat() if source.created_at else None
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

@funding_sources_bp.route('/', methods=['POST'])
def create_funding_source():
    """Create a new funding source"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Funding source name is required'
            }), 400
            
        if not data.get('type'):
            return jsonify({
                'success': False,
                'error': 'Funding source type is required'
            }), 400
        
        # Parse deadline if provided
        application_deadline = None
        if data.get('application_deadline'):
            application_deadline = datetime.strptime(data['application_deadline'], '%Y-%m-%d').date()
        
        # Create funding source
        funding_source = FundingSource(
            name=data['name'],
            type=FundingSourceType(data['type']),
            agency=data.get('agency'),
            description=data.get('description'),
            application_deadline=application_deadline,
            award_amount_min=data.get('award_amount_min'),
            award_amount_max=data.get('award_amount_max'),
            requirements=data.get('requirements'),
            contact_info=data.get('contact_info'),
            website_url=data.get('website_url'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(funding_source)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': funding_source.id,
                'name': funding_source.name,
                'message': 'Funding source created successfully'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@funding_sources_bp.route('/<int:source_id>', methods=['PUT'])
def update_funding_source(source_id):
    """Update an existing funding source"""
    try:
        funding_source = FundingSource.query.get_or_404(source_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            funding_source.name = data['name']
        if 'type' in data:
            funding_source.type = FundingSourceType(data['type'])
        if 'agency' in data:
            funding_source.agency = data['agency']
        if 'description' in data:
            funding_source.description = data['description']
        if 'application_deadline' in data:
            if data['application_deadline']:
                funding_source.application_deadline = datetime.strptime(data['application_deadline'], '%Y-%m-%d').date()
            else:
                funding_source.application_deadline = None
        if 'award_amount_min' in data:
            funding_source.award_amount_min = data['award_amount_min']
        if 'award_amount_max' in data:
            funding_source.award_amount_max = data['award_amount_max']
        if 'requirements' in data:
            funding_source.requirements = data['requirements']
        if 'contact_info' in data:
            funding_source.contact_info = data['contact_info']
        if 'website_url' in data:
            funding_source.website_url = data['website_url']
        if 'is_active' in data:
            funding_source.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': funding_source.id,
                'name': funding_source.name,
                'message': 'Funding source updated successfully'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@funding_sources_bp.route('/types', methods=['GET'])
def get_funding_source_types():
    """Get all available funding source types"""
    try:
        types = [{'value': source_type.value, 'label': source_type.value} for source_type in FundingSourceType]
        
        return jsonify({
            'success': True,
            'data': types
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

