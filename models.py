from datetime import datetime
from app import db
from sqlalchemy import Text, JSON

class Program(db.Model):
    """Model for storing ITMO AI program information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(Text)
    duration = db.Column(db.String(50))
    language = db.Column(db.String(50))
    cost = db.Column(db.String(100))
    budget_places = db.Column(db.Integer)
    contract_places = db.Column(db.Integer)
    career_prospects = db.Column(Text)
    admission_requirements = db.Column(Text)
    curriculum_data = db.Column(JSON)
    partners = db.Column(JSON)
    team_members = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Conversation(db.Model):
    """Model for storing user conversations"""
    id = db.Column(db.Integer, primary_key=True)
    telegram_user_id = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100))
    message = db.Column(Text, nullable=False)
    response = db.Column(Text)
    context = db.Column(JSON)  # Store conversation context
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserProfile(db.Model):
    """Model for storing user background information"""
    id = db.Column(db.Integer, primary_key=True)
    telegram_user_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100))
    background = db.Column(db.String(100))  # technical, product, mixed, etc.
    experience_years = db.Column(db.Integer)
    interests = db.Column(JSON)  # List of interests
    preferred_language = db.Column(db.String(10), default='ru')
    survey_step = db.Column(db.Integer, default=0)  # Track survey progress
    education_background = db.Column(db.String(200))  # Educational background
    work_experience = db.Column(db.String(200))  # Work experience
    career_goals = db.Column(db.String(200))  # Career aspirations
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
