from flask import Blueprint, request, jsonify
import openai
import os
from src.models.database import db, Project, Client, Application, FundingSource

ai_chat_bp = Blueprint('ai_chat', __name__)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_project_context(project_id=None):
    """Get context about projects for AI responses"""
    context = []
    
    if project_id:
        # Get specific project
        project = Project.query.get(project_id)
        if project:
            total_awarded = sum([app.awarded_amount or 0 for app in project.applications])
            funding_gap = (project.total_cost or 0) - total_awarded
            
            context.append(f"Project: {project.name}")
            context.append(f"Location: {project.city}, {project.state}")
            context.append(f"Phase: {project.phase.value if project.phase else 'Unknown'}")
            context.append(f"Total Units: {project.total_units}")
            context.append(f"Total Cost: ${project.total_cost:,.2f}" if project.total_cost else "Total Cost: Not specified")
            context.append(f"Funding Secured: ${total_awarded:,.2f}")
            context.append(f"Funding Gap: ${funding_gap:,.2f}")
            context.append(f"Client: {project.client.name if project.client else 'Unknown'}")
            
            if project.applications:
                context.append("\\nFunding Applications:")
                for app in project.applications:
                    context.append(f"- {app.funding_source.name}: {app.status.value}")
                    if app.requested_amount:
                        context.append(f"  Requested: ${app.requested_amount:,.2f}")
                    if app.awarded_amount:
                        context.append(f"  Awarded: ${app.awarded_amount:,.2f}")
    else:
        # Get general portfolio overview
        total_projects = Project.query.count()
        context.append(f"Total Projects in Portfolio: {total_projects}")
        
        # Get projects by phase
        from src.models.database import ProjectPhase
        for phase in ProjectPhase:
            count = Project.query.filter(Project.phase == phase).count()
            context.append(f"{phase.value}: {count} projects")
    
    return "\\n".join(context)

@ai_chat_bp.route('/chat', methods=['POST'])
def chat_with_ai():
    """Chat with AI about projects and clients"""
    try:
        data = request.get_json()
        
        if not data.get('message'):
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        user_message = data['message']
        project_id = data.get('project_id')
        
        # Get context for the AI
        context = get_project_context(project_id)
        
        # System prompt for affordable housing context
        system_prompt = f"""You are an AI assistant for an affordable housing development firm. You help with project management, funding applications, and client communications.

Current Context:
{context}

You should provide helpful, accurate information about:
- Project status and funding gaps
- Funding source recommendations
- Application deadlines and requirements
- Project development phases
- Client and stakeholder management

Be professional, concise, and focus on actionable insights for affordable housing development."""

        # Make OpenAI API call
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
        except Exception as openai_error:
            # Fallback response if OpenAI is not available
            ai_response = f"I'm here to help with your affordable housing projects. Based on the current context, I can see you have projects in various phases. However, I'm currently unable to access my full AI capabilities. Please check your OpenAI API configuration. Your message was: '{user_message}'"
        
        return jsonify({
            'success': True,
            'data': {
                'response': ai_response,
                'context_used': bool(context)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_chat_bp.route('/project-insights/<int:project_id>', methods=['GET'])
def get_project_insights(project_id):
    """Get AI-generated insights for a specific project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Calculate project metrics
        total_awarded = sum([app.awarded_amount or 0 for app in project.applications])
        total_requested = sum([app.requested_amount or 0 for app in project.applications])
        funding_gap = (project.total_cost or 0) - total_awarded
        
        # Generate insights
        insights = []
        
        # Funding gap analysis
        if funding_gap > 0:
            gap_percentage = (funding_gap / project.total_cost * 100) if project.total_cost else 0
            if gap_percentage > 50:
                insights.append({
                    'type': 'warning',
                    'title': 'Significant Funding Gap',
                    'message': f'Project has a ${funding_gap:,.0f} funding gap ({gap_percentage:.1f}% of total cost). Consider additional funding sources.'
                })
            elif gap_percentage > 20:
                insights.append({
                    'type': 'info',
                    'title': 'Moderate Funding Gap',
                    'message': f'Project has a ${funding_gap:,.0f} funding gap. Monitor for additional funding opportunities.'
                })
        else:
            insights.append({
                'type': 'success',
                'title': 'Fully Funded',
                'message': 'Project funding is complete or oversubscribed.'
            })
        
        # Application status insights
        pending_apps = [app for app in project.applications if app.status.value in ['Draft', 'Submitted', 'Under Review']]
        if pending_apps:
            insights.append({
                'type': 'info',
                'title': 'Pending Applications',
                'message': f'{len(pending_apps)} funding applications are still pending. Total pending amount: ${sum([app.requested_amount or 0 for app in pending_apps]):,.0f}'
            })
        
        # Phase-specific recommendations
        if project.phase:
            if project.phase.value == 'Pre-Development':
                insights.append({
                    'type': 'info',
                    'title': 'Pre-Development Phase',
                    'message': 'Focus on site control, environmental reviews, and preliminary design. Consider PDLP funding for predevelopment costs.'
                })
            elif project.phase.value == 'Application/Financing':
                insights.append({
                    'type': 'info',
                    'title': 'Financing Phase',
                    'message': 'Active funding application period. Monitor deadlines and ensure all documentation is complete.'
                })
        
        return jsonify({
            'success': True,
            'data': {
                'project_name': project.name,
                'insights': insights,
                'metrics': {
                    'total_cost': project.total_cost,
                    'funding_secured': total_awarded,
                    'funding_requested': total_requested,
                    'funding_gap': funding_gap
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_chat_bp.route('/funding-recommendations/<int:project_id>', methods=['GET'])
def get_funding_recommendations(project_id):
    """Get AI-powered funding source recommendations for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get all active funding sources
        all_sources = FundingSource.query.filter(FundingSource.is_active == True).all()
        
        # Get funding sources already applied to
        applied_source_ids = [app.funding_source_id for app in project.applications]
        available_sources = [source for source in all_sources if source.id not in applied_source_ids]
        
        recommendations = []
        
        for source in available_sources:
            # Simple matching logic (can be enhanced with AI)
            match_score = 0
            reasons = []
            
            # Check if project type matches funding source
            if source.type.value == 'LIHTC 9%' and project.total_units and project.total_units >= 20:
                match_score += 30
                reasons.append("Good fit for 9% LIHTC with sufficient unit count")
            
            if source.type.value == 'FHLB AHP' and project.population_type == 'Family':
                match_score += 25
                reasons.append("FHLB AHP supports family housing development")
            
            if source.type.value == 'HOME' and project.project_type in ['New Construction', 'Rehabilitation']:
                match_score += 20
                reasons.append("HOME funds support new construction and rehabilitation")
            
            # Check funding amount compatibility
            if source.award_amount_min and source.award_amount_max:
                funding_gap = (project.total_cost or 0) - sum([app.awarded_amount or 0 for app in project.applications])
                if source.award_amount_min <= funding_gap <= source.award_amount_max:
                    match_score += 25
                    reasons.append(f"Award range (${source.award_amount_min:,.0f}-${source.award_amount_max:,.0f}) matches funding gap")
            
            if match_score > 0:
                recommendations.append({
                    'funding_source': {
                        'id': source.id,
                        'name': source.name,
                        'type': source.type.value,
                        'agency': source.agency,
                        'award_amount_min': source.award_amount_min,
                        'award_amount_max': source.award_amount_max
                    },
                    'match_score': match_score,
                    'reasons': reasons
                })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'project_name': project.name,
                'recommendations': recommendations[:5],  # Top 5 recommendations
                'total_available_sources': len(available_sources)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

