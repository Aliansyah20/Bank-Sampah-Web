import os
from flask import Flask
from .extensions import db
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    # Konfigurasi Database & Secret Key ...
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD') or ''}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Konfigurasi Upload Foto Bukti
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'bukti')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # Registrasi Seluruh Blueprint
    from app.routes.auth_routes import auth_bp
    from app.routes.sekben_routes import sekben_bp
    from app.routes.pengolah_routes import pengolah_bp
    from app.routes.marketing_routes import marketing_bp
    from app.routes.warga_routes import warga_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(sekben_bp, url_prefix='/sekben')
    app.register_blueprint(pengolah_bp, url_prefix='/pengolah')
    app.register_blueprint(marketing_bp, url_prefix='/marketing')
    app.register_blueprint(warga_bp, url_prefix='/warga')

    return app