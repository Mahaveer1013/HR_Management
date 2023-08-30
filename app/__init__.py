from flask import Flask
from flask_sqlalchemy import  SQLAlchemy
from flask_login import LoginManager
import os
from os import path
import datetime
import sched
import time
from datetime import datetime, timedelta

db= SQLAlchemy()
DB_NAME="database.db"

def create_app():
    app= Flask(__name__)
    app.config['SECRET_KEY'] = '#$&^&^WYYDUHS&YWE'
    #
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(DB_NAME)
    db_path = os.path.abspath(os.path.dirname(__file__))  # Get the directory of the main script
    #app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{o s.path.join(db_path, DB_NAME)}'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(os.path.join(db_path, DB_NAME))
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/img/profile')
    Excel_FOLDER = os.path.join(APP_ROOT, 'static/excel')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['Excel_FOLDER'] = Excel_FOLDER
    
    db.init_app(app)
    
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    
    from .auth import auth
    from .views import views
    app.register_blueprint(views,url_prefix='/')
    app.register_blueprint(auth,url_prefix='/')
    from.models import Login_admin,Employee,Attendance,Shift_time,Backup
    with app.app_context():
        db.create_all()
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(id):
        return Login_admin.query.get(int(id))
    return app

def create_database(app):
    if not path.exists('app/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
    else:
        print('Database already exists.')
