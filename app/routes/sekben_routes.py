from flask import Blueprint, render_template, session
from app.utils import role_required

sekben_bp = Blueprint('sekben', __name__)

# Route utama untuk dashboard sekben
@sekben_bp.route('/dashboard')
@role_required(['sekben']) # Menggunakan "satpam" yang sudah kita buat
def dashboard():
    # Mengambil nama lengkap dari session saat user login
    nama = session.get('nama_lengkap', 'Sekben')
    return render_template('dashboard/sekben_dashboard.html', nama=nama)