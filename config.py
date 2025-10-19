import os

class Config:
    """Base configuration settings for the Flask app."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-and-hard-to-guess-key'
    SQLALCHEMY_DATABASE_URI ='postgresql://ajaydb_mooe_user:2uCzgTOxUey4IJH1YrvFOxkq6fetkPBY@dpg-d3qc8i2li9vc73c7mg70-a/ajaydb_mooe'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Credentials for the single admin user
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'



