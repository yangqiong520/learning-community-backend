from flask import Flask, request
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
from app.routers.years import years_bp
from app.routers.harvests import harvests_bp

try:
    from app.routers.smart_resources import smart_resources_bp
    SMART_RESOURCES_AVAILABLE = True
except ImportError:
    print("警告: opencv-python未安装，智能资源功能不可用")
    SMART_RESOURCES_AVAILABLE = False

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app_config = config['app']

def create_app():
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

    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            from flask import jsonify, make_response
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response

    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(regulations_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(teaching_bp)
    app.register_blueprint(textbook_bp)
    app.register_blueprint(courseware_bp)
    app.register_blueprint(courses_bp, url_prefix='/api/v2/courses')
    app.register_blueprint(homework_bp, url_prefix='/api/v2/homework')
    app.register_blueprint(years_bp, url_prefix='/api/v2/years')
    app.register_blueprint(harvests_bp)

    if SMART_RESOURCES_AVAILABLE:
        app.register_blueprint(smart_resources_bp)
    
    @app.route('/')
    def index():
        return {'message': 'Learning Community Backend API', 'version': app_config['version']}
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(
        host=app_config['host'],
        port=app_config['port'],
        debug=app_config['debug']
    )