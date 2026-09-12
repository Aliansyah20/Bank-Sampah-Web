from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Cek apakah user sudah ada agar tidak dobel
    if not User.query.filter_by(username='sekben1').first():
        sekben = User(
            nama_lengkap="Rizki",
            username="sekben1",
            password=generate_password_hash("rahasia123"),
            role="sekben"
        )
        db.session.add(sekben)
        db.session.commit()
        print("Berhasil! Akun Sekben dibuat. Username: sekben1 | Pass: rahasia123")
    else:
        print("Akun sekben1 sudah ada di database.")
        print("Verivikasi akun")