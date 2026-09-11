from flask import Flask
from .extensions import db
import os
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    db_user = os.getenv('DB_USERNAME')
    db_pass = os.getenv('DB_PASSWORD') or ''
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    db.init_app(app)

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.routes.sekben_routes import sekben_bp
    app.register_blueprint(sekben_bp, url_prefix='/sekben')

    @app.route('/')
    def index():
        return "<h2>Mantap! Server Bank Sampah Flask sudah menyala!</h2> <a href='/auth/login'>Ke Halaman Login</a>"

    return app