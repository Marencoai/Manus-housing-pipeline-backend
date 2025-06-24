from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class ProjectPhase(Enum):
    PRE_DEVELOPMENT = "Pre-Development"
    APPLICATION_FINANCING = "Application/Financing"
    CONSTRUCTION = "Construction"
    LEASE_UP_COMPLIANCE = "Lease-Up/Compliance"

class FundingSourceType(Enum):
    LIHTC_9_PERCENT = "LIHTC 9%"
    LIHTC_4_PERCENT = "LIHTC 4%"
    FHLB_AHP = "FHLB AHP"
    ORCA = "ORCA"
    HOME = "HOME"
    PDLP = "PDLP"
    CONGRESSIONAL_CIP = "Congressional/CIP"

class ApplicationStatus(Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    DENIED = "Denied"
    WITHDRAWN = "Withdrawn"

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    phase = db.Column(db.Enum(ProjectPhase), default=ProjectPhase.PRE_DEVELOPMENT)
    project_type = db.Column(db.String(100))  # New Construction, Rehabilitation, etc.
    population_type = db.Column(db.String(100))  # Family, Senior, etc.
    housing_type = db.Column(db.String(100))  # Multifamily, Single-family
    total_units = db.Column(db.Integer)
    total_cost = db.Column(db.Float)
    funding_gap = db.Column(db.Float, default=0.0)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    sharepoint_site_url = db.Column(db.String(500))
    sharepoint_email = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', backref='projects')
    applications = db.relationship('Application', backref='project', cascade='all, delete-orphan')
    time_entries = db.relationship('TimeEntry', backref='project', cascade='all, delete-orphan')

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    organization = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    contact_person = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FundingSource(db.Model):
    __tablename__ = 'funding_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(FundingSourceType), nullable=False)
    agency = db.Column(db.String(200))
    description = db.Column(db.Text)
    application_deadline = db.Column(db.Date)
    award_amount_min = db.Column(db.Float)
    award_amount_max = db.Column(db.Float)
    requirements = db.Column(db.Text)
    contact_info = db.Column(db.Text)
    website_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    funding_source_id = db.Column(db.Integer, db.ForeignKey('funding_sources.id'), nullable=False)
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    application_round = db.Column(db.String(100))  # e.g., "2023-5"
    requested_amount = db.Column(db.Float)
    awarded_amount = db.Column(db.Float)
    submission_date = db.Column(db.Date)
    decision_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    documents_folder = db.Column(db.String(500))  # SharePoint folder path
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    funding_source = db.relationship('FundingSource', backref='applications')

class TimeEntry(db.Model):
    __tablename__ = 'time_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    user_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    hourly_rate = db.Column(db.Float, default=125.0)
    date = db.Column(db.Date, nullable=False)
    is_billable = db.Column(db.Boolean, default=True)
    is_invoiced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Email(db.Model):
    __tablename__ = 'emails'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    subject = db.Column(db.String(500), nullable=False)
    sender = db.Column(db.String(200), nullable=False)
    recipients = db.Column(db.Text)  # JSON string of recipients
    body = db.Column(db.Text)
    received_date = db.Column(db.DateTime, nullable=False)
    outlook_message_id = db.Column(db.String(500), unique=True)
    funding_source_type = db.Column(db.Enum(FundingSourceType))
    is_urgent = db.Column(db.Boolean, default=False)
    is_processed = db.Column(db.Boolean, default=False)
    ai_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='emails')

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    name = db.Column(db.String(300), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    sharepoint_url = db.Column(db.String(500))
    document_type = db.Column(db.String(100))  # Application, Contract, Report, etc.
    version = db.Column(db.String(50))
    status = db.Column(db.String(50))  # Draft, Final, Approved, etc.
    uploaded_by = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='documents')
    application = db.relationship('Application', backref='documents')

