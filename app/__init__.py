from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from os import path

# Initialize SQLAlchemy
db = SQLAlchemy()
DB_NAME = "database.db"

# Factory function to create the Flask app
def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = '#$&^&^WYYDUHS&YWE' 
    db_path = os.path.abspath(os.path.dirname(__file__))  # Get the directory of the main script
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(os.path.join(db_path, DB_NAME))
   
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Define paths for file uploads
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/img/profile')
    EXCEL_FOLDER = os.path.join(APP_ROOT, 'static/excel')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['EXCEL_FOLDER'] = EXCEL_FOLDER
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    
    # Import and register blueprints
    from .auth import auth
    from .views import views
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    create_database(app)
    
    # Import models and create database tables
    from .models import Login_admin, Employee, Attendance, Shift_time, Backup
    with app.app_context():
        db.create_all()
    
    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # User loader callback for LoginManager
    @login_manager.user_loader
    def load_user(id):
        return Login_admin.query.get(int(id))
    
    return app

# Function to create the database if it doesn't exist
def create_database(app):
    if not path.exists('app/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')


