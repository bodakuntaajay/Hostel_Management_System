import os

class Config:
    """Base configuration settings for the Flask app."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-and-hard-to-guess-key'
SQLALCHEMY_DATABASE_URI = database_url
SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Credentials for the single admin user
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'

