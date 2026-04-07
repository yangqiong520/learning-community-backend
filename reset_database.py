import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import flask
from flask import Flask
from flask_cors import CORS
import yaml
from libs.db import db, DATABASE_URI
from app.routers.auth import auth_bp
from app.routers.users import users_bp
from app.routers.files import files_bp
from app.routers.regulations import regulations_bp
from app.routers.training_programs import training_bp
from app.routers.teaching_plans import teaching_bp
from app.routers.textbooks import textbook_bp
from app.routers.coursewares import courseware_bp
from app.routers.courses import courses_bp
from app.routers.homeworks import homework_bp

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app_config = config['app']

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 600
    }
})

db.init_app(app)

with app.app_context():
    print("Manually dropping problematic tables...")
    try:
        db.session.execute(db.text("DROP TABLE IF EXISTS homework_submissions"))
        db.session.commit()
        print("  - Dropped homework_submissions")
    except Exception as e:
        print(f"  - Error dropping homework_submissions: {e}")
        db.session.rollback()
    
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Done!")
