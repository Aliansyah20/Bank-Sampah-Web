from flask import Blueprint, render_template, session
from app.models import User, Penyetoran, DetailPenyetoran
from app.utils import role_required

warga_bp = Blueprint('warga', __name__)

@warga_bp.route('/dashboard')
@role_required(['warga'])
def dashboard():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    # Ambil semua data detail setoran milik warga ini
    riwayat_setoran = (
        DetailPenyetoran.query
        .join(Penyetoran, DetailPenyetoran.id_penyetoran == Penyetoran.id)
        .filter(Penyetoran.id_warga == user_id)
        .order_by(DetailPenyetoran.id.desc())
        .all()
    )
    
    # Hitung ringkasan statistik pribadi warga
    total_transaksi = len(riwayat_setoran)
    total_berat_verifikasi = sum(
        float(item.berat_verifikasi) for item in riwayat_setoran if item.berat_verifikasi
    )
    
    return render_template(
        'dashboard/warga_dashboard.html',
        warga=user,
        riwayat=riwayat_setoran,
        total_transaksi=total_transaksi,
        total_berat=total_berat_verifikasi
    )