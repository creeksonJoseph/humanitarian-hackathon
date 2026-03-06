"""Production configuration management."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/okoaroute.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Africa's Talking
    AT_USERNAME = os.getenv('AFRICAS_TALKING_USERNAME', 'sandbox')
    AT_API_KEY = os.getenv('AFRICAS_TALKING_API_KEY', '')
    
    # API Security
    API_KEY = os.getenv('API_KEY', 'dev-api-key')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
