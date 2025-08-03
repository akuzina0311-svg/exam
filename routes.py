from flask import render_template, jsonify, request
from app import app, db
from models import Conversation, UserProfile, Program
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def dashboard():
    """Main dashboard for bot management"""
    try:
        # Get statistics
        total_conversations = Conversation.query.count()
        total_users = UserProfile.query.count()
        total_programs = Program.query.count()
        
        # Recent conversations
        recent_conversations = Conversation.query.order_by(
            Conversation.created_at.desc()
        ).limit(10).all()
        
        # Popular questions (simplified)
        today = datetime.utcnow().date()
        today_conversations = Conversation.query.filter(
            Conversation.created_at >= today
        ).count()
        
        stats = {
            'total_conversations': total_conversations,
            'total_users': total_users,
            'total_programs': total_programs,
            'today_conversations': today_conversations
        }
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_conversations=recent_conversations)
                             
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('dashboard.html', 
                             stats={'error': 'Ошибка загрузки данных'},
                             recent_conversations=[])

@app.route('/api/stats')
def api_stats():
    """API endpoint for getting bot statistics"""
    try:
        # Get conversation stats for the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        daily_stats = []
        
        for i in range(7):
            day = week_ago + timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = Conversation.query.filter(
                Conversation.created_at >= day_start,
                Conversation.created_at < day_end
            ).count()
            
            daily_stats.append({
                'date': day.strftime('%Y-%m-%d'),
                'conversations': count
            })
        
        # Get user backgrounds distribution
        backgrounds = db.session.query(
            UserProfile.background, 
            db.func.count(UserProfile.id)
        ).group_by(UserProfile.background).all()
        
        background_stats = [
            {'background': bg[0] or 'unknown', 'count': bg[1]} 
            for bg in backgrounds
        ]
        
        return jsonify({
            'daily_conversations': daily_stats,
            'user_backgrounds': background_stats,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/programs')
def api_programs():
    """API endpoint for getting program information"""
    try:
        programs = Program.query.all()
        programs_data = []
        
        for program in programs:
            programs_data.append({
                'id': program.id,
                'name': program.name,
                'url': program.url,
                'description': program.description[:200] + '...' if program.description and len(program.description) > 200 else program.description,
                'duration': program.duration,
                'language': program.language,
                'cost': program.cost,
                'budget_places': program.budget_places,
                'contract_places': program.contract_places,
                'updated_at': program.updated_at.isoformat() if program.updated_at else None
            })
        
        return jsonify({
            'programs': programs_data,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error getting programs: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/conversations')
def api_conversations():
    """API endpoint for getting recent conversations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        conversations = Conversation.query.order_by(
            Conversation.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        conversations_data = []
        for conv in conversations.items:
            conversations_data.append({
                'id': conv.id,
                'username': conv.username,
                'message': conv.message[:100] + '...' if len(conv.message) > 100 else conv.message,
                'response': conv.response[:100] + '...' if conv.response and len(conv.response) > 100 else conv.response,
                'created_at': conv.created_at.isoformat()
            })
        
        return jsonify({
            'conversations': conversations_data,
            'total': conversations.total,
            'pages': conversations.pages,
            'current_page': page,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/refresh-data', methods=['POST'])
def refresh_data():
    """Manually refresh program data"""
    try:
        from web_scraper import scrape_and_store_program_data
        scrape_and_store_program_data()
        return jsonify({'status': 'success', 'message': 'Данные обновлены'})
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
