from app import create_app
from app.extensions import db
from app.models import * # Mengambil semua struktur tabel

app = create_app()

with app.app_context():
    # Menghapus tabel lama (jika ada) dan membuat yang baru sesuai models.py
    db.drop_all()
    db.create_all()
    print("Database dan semua tabel berhasil dibuat!")