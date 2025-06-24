from flask import Blueprint, request, jsonify
from src.models.database import db, TimeEntry, Project
from datetime import datetime, date

time_tracking_bp = Blueprint('time_tracking', __name__)

@time_tracking_bp.route('/', methods=['GET'])
def get_time_entries():
    """Get time entries with optional filtering"""
    try:
        project_id = request.args.get('project_id')
        user_name = request.args.get('user_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        is_billable = request.args.get('is_billable')
        is_invoiced = request.args.get('is_invoiced')
        
        query = TimeEntry.query
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        if user_name:
            query = query.filter(TimeEntry.user_name.ilike(f'%{user_name}%'))
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(TimeEntry.date >= start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(TimeEntry.date <= end)
        if is_billable is not None:
            query = query.filter(TimeEntry.is_billable == (is_billable.lower() == 'true'))
        if is_invoiced is not None:
            query = query.filter(TimeEntry.is_invoiced == (is_invoiced.lower() == 'true'))
            
        time_entries = query.order_by(TimeEntry.date.desc()).all()
        
        result = []
        for entry in time_entries:
            total_amount = entry.hours * entry.hourly_rate
            
            result.append({
                'id': entry.id,
                'project': {
                    'id': entry.project.id,
                    'name': entry.project.name
                } if entry.project else None,
                'user_name': entry.user_name,
                'description': entry.description,
                'hours': entry.hours,
                'hourly_rate': entry.hourly_rate,
                'total_amount': total_amount,
                'date': entry.date.isoformat(),
                'is_billable': entry.is_billable,
                'is_invoiced': entry.is_invoiced,
                'created_at': entry.created_at.isoformat() if entry.created_at else None
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

@time_tracking_bp.route('/', methods=['POST'])
def create_time_entry():
    """Create a new time entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('user_name'):
            return jsonify({
                'success': False,
                'error': 'User name is required'
            }), 400
            
        if not data.get('description'):
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
            
        if not data.get('hours'):
            return jsonify({
                'success': False,
                'error': 'Hours is required'
            }), 400
            
        if not data.get('date'):
            return jsonify({
                'success': False,
                'error': 'Date is required'
            }), 400
        
        # Verify project exists if provided
        if data.get('project_id'):
            project = Project.query.get(data['project_id'])
            if not project:
                return jsonify({
                    'success': False,
                    'error': 'Project not found'
                }), 404
        
        # Parse date
        entry_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Create time entry
        time_entry = TimeEntry(
            project_id=data.get('project_id'),
            user_name=data['user_name'],
            description=data['description'],
            hours=float(data['hours']),
            hourly_rate=float(data.get('hourly_rate', 125.0)),
            date=entry_date,
            is_billable=data.get('is_billable', True),
            is_invoiced=data.get('is_invoiced', False)
        )
        
        db.session.add(time_entry)
        db.session.commit()
        
        total_amount = time_entry.hours * time_entry.hourly_rate
        
        return jsonify({
            'success': True,
            'data': {
                'id': time_entry.id,
                'total_amount': total_amount,
                'message': 'Time entry created successfully'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@time_tracking_bp.route('/<int:entry_id>', methods=['PUT'])
def update_time_entry(entry_id):
    """Update an existing time entry"""
    try:
        time_entry = TimeEntry.query.get_or_404(entry_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'project_id' in data:
            if data['project_id']:
                project = Project.query.get(data['project_id'])
                if not project:
                    return jsonify({
                        'success': False,
                        'error': 'Project not found'
                    }), 404
                time_entry.project_id = data['project_id']
            else:
                time_entry.project_id = None
                
        if 'user_name' in data:
            time_entry.user_name = data['user_name']
        if 'description' in data:
            time_entry.description = data['description']
        if 'hours' in data:
            time_entry.hours = float(data['hours'])
        if 'hourly_rate' in data:
            time_entry.hourly_rate = float(data['hourly_rate'])
        if 'date' in data:
            time_entry.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'is_billable' in data:
            time_entry.is_billable = data['is_billable']
        if 'is_invoiced' in data:
            time_entry.is_invoiced = data['is_invoiced']
        
        db.session.commit()
        
        total_amount = time_entry.hours * time_entry.hourly_rate
        
        return jsonify({
            'success': True,
            'data': {
                'id': time_entry.id,
                'total_amount': total_amount,
                'message': 'Time entry updated successfully'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@time_tracking_bp.route('/<int:entry_id>', methods=['DELETE'])
def delete_time_entry(entry_id):
    """Delete a time entry"""
    try:
        time_entry = TimeEntry.query.get_or_404(entry_id)
        
        db.session.delete(time_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Time entry deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@time_tracking_bp.route('/summary', methods=['GET'])
def get_time_summary():
    """Get time tracking summary and billing information"""
    try:
        user_name = request.args.get('user_name')
        project_id = request.args.get('project_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = TimeEntry.query
        
        if user_name:
            query = query.filter(TimeEntry.user_name.ilike(f'%{user_name}%'))
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(TimeEntry.date >= start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(TimeEntry.date <= end)
            
        time_entries = query.all()
        
        # Calculate totals
        total_hours = sum([entry.hours for entry in time_entries])
        total_billable_hours = sum([entry.hours for entry in time_entries if entry.is_billable])
        total_amount = sum([entry.hours * entry.hourly_rate for entry in time_entries if entry.is_billable])
        total_invoiced_amount = sum([entry.hours * entry.hourly_rate for entry in time_entries if entry.is_invoiced])
        total_unbilled_amount = sum([entry.hours * entry.hourly_rate for entry in time_entries if entry.is_billable and not entry.is_invoiced])
        
        # Group by project
        project_summary = {}
        for entry in time_entries:
            project_name = entry.project.name if entry.project else 'No Project'
            if project_name not in project_summary:
                project_summary[project_name] = {
                    'hours': 0,
                    'billable_hours': 0,
                    'amount': 0
                }
            
            project_summary[project_name]['hours'] += entry.hours
            if entry.is_billable:
                project_summary[project_name]['billable_hours'] += entry.hours
                project_summary[project_name]['amount'] += entry.hours * entry.hourly_rate
        
        # Group by user
        user_summary = {}
        for entry in time_entries:
            if entry.user_name not in user_summary:
                user_summary[entry.user_name] = {
                    'hours': 0,
                    'billable_hours': 0,
                    'amount': 0
                }
            
            user_summary[entry.user_name]['hours'] += entry.hours
            if entry.is_billable:
                user_summary[entry.user_name]['billable_hours'] += entry.hours
                user_summary[entry.user_name]['amount'] += entry.hours * entry.hourly_rate
        
        return jsonify({
            'success': True,
            'data': {
                'totals': {
                    'total_hours': total_hours,
                    'total_billable_hours': total_billable_hours,
                    'total_amount': total_amount,
                    'total_invoiced_amount': total_invoiced_amount,
                    'total_unbilled_amount': total_unbilled_amount
                },
                'project_summary': project_summary,
                'user_summary': user_summary,
                'entries_count': len(time_entries)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@time_tracking_bp.route('/invoice-data', methods=['GET'])
def get_invoice_data():
    """Get unbilled time entries for invoice generation"""
    try:
        project_id = request.args.get('project_id')
        user_name = request.args.get('user_name')
        
        query = TimeEntry.query.filter(
            TimeEntry.is_billable == True,
            TimeEntry.is_invoiced == False
        )
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        if user_name:
            query = query.filter(TimeEntry.user_name.ilike(f'%{user_name}%'))
            
        unbilled_entries = query.order_by(TimeEntry.date.desc()).all()
        
        invoice_items = []
        total_amount = 0
        
        for entry in unbilled_entries:
            line_total = entry.hours * entry.hourly_rate
            total_amount += line_total
            
            invoice_items.append({
                'id': entry.id,
                'date': entry.date.isoformat(),
                'project_name': entry.project.name if entry.project else 'General',
                'description': entry.description,
                'hours': entry.hours,
                'hourly_rate': entry.hourly_rate,
                'line_total': line_total,
                'user_name': entry.user_name
            })
        
        return jsonify({
            'success': True,
            'data': {
                'invoice_items': invoice_items,
                'total_amount': total_amount,
                'total_hours': sum([item['hours'] for item in invoice_items]),
                'items_count': len(invoice_items)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@time_tracking_bp.route('/mark-invoiced', methods=['POST'])
def mark_entries_invoiced():
    """Mark time entries as invoiced"""
    try:
        data = request.get_json()
        entry_ids = data.get('entry_ids', [])
        
        if not entry_ids:
            return jsonify({
                'success': False,
                'error': 'Entry IDs are required'
            }), 400
        
        # Update entries
        updated_count = TimeEntry.query.filter(
            TimeEntry.id.in_(entry_ids)
        ).update({
            TimeEntry.is_invoiced: True
        }, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'updated_count': updated_count,
                'message': f'{updated_count} time entries marked as invoiced'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

