from flask import Flask
from .extensions import db
import os
from dotenv import load_dotenv

def create_app():
    # Mengambil data dari file .env
    load_dotenv()
    
    app = Flask(__name__)
    
    # Merakit koneksi ke MySQL
    db_user = os.getenv('DB_USERNAME')
    db_pass = os.getenv('DB_PASSWORD') or ''
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Menyambungkan database ke aplikasi
    db.init_app(app)

    # Route sementara untuk mengetes server
    @app.route('/')
    def index():
        return "<h2>Mantap! Server Bank Sampah Flask sudah menyala!</h2>"

    return app