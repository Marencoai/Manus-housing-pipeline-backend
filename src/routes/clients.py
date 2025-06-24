from flask import Blueprint, request, jsonify
from src.models.database import db, Client
from datetime import datetime

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/', methods=['GET'])
def get_clients():
    """Get all clients"""
    try:
        clients = Client.query.all()
        
        result = []
        for client in clients:
            result.append({
                'id': client.id,
                'name': client.name,
                'organization': client.organization,
                'email': client.email,
                'phone': client.phone,
                'address': client.address,
                'city': client.city,
                'state': client.state,
                'zip_code': client.zip_code,
                'contact_person': client.contact_person,
                'projects_count': len(client.projects),
                'created_at': client.created_at.isoformat() if client.created_at else None
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

@clients_bp.route('/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Get a specific client by ID"""
    try:
        client = Client.query.get_or_404(client_id)
        
        # Get client projects
        projects = []
        for project in client.projects:
            total_awarded = sum([app.awarded_amount or 0 for app in project.applications])
            funding_gap = (project.total_cost or 0) - total_awarded
            
            projects.append({
                'id': project.id,
                'name': project.name,
                'phase': project.phase.value if project.phase else None,
                'total_units': project.total_units,
                'total_cost': project.total_cost,
                'funding_secured': total_awarded,
                'funding_gap': funding_gap
            })
        
        result = {
            'id': client.id,
            'name': client.name,
            'organization': client.organization,
            'email': client.email,
            'phone': client.phone,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zip_code': client.zip_code,
            'contact_person': client.contact_person,
            'projects': projects,
            'created_at': client.created_at.isoformat() if client.created_at else None,
            'updated_at': client.updated_at.isoformat() if client.updated_at else None
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

@clients_bp.route('/', methods=['POST'])
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Client name is required'
            }), 400
        
        # Create client
        client = Client(
            name=data['name'],
            organization=data.get('organization'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            contact_person=data.get('contact_person')
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': client.id,
                'name': client.name,
                'message': 'Client created successfully'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@clients_bp.route('/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    """Update an existing client"""
    try:
        client = Client.query.get_or_404(client_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            client.name = data['name']
        if 'organization' in data:
            client.organization = data['organization']
        if 'email' in data:
            client.email = data['email']
        if 'phone' in data:
            client.phone = data['phone']
        if 'address' in data:
            client.address = data['address']
        if 'city' in data:
            client.city = data['city']
        if 'state' in data:
            client.state = data['state']
        if 'zip_code' in data:
            client.zip_code = data['zip_code']
        if 'contact_person' in data:
            client.contact_person = data['contact_person']
            
        client.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': client.id,
                'name': client.name,
                'message': 'Client updated successfully'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

