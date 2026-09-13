from datetime import date
from flask import Blueprint, render_template, session
from sqlalchemy import func
from app.models import User, Penyetoran, DetailPenyetoran, Penjualan
from app.extensions import db
from app.utils import role_required

pengawas_bp = Blueprint('pengawas', __name__)

@pengawas_bp.route('/dashboard')
@role_required(['pengawas'])
def dashboard():
    hari_ini = date.today()

    # 1. Metrik Utama Tingkat RW
    total_warga = User.query.filter_by(role='warga').count()
    
    # Total setoran & sampah masuk hari ini
    setoran_hari_ini = Penyetoran.query.filter(func.date(Penyetoran.waktu_setor) == hari_ini).count()
    berat_masuk_hari_ini = (
        db.session.query(func.sum(DetailPenyetoran.berat_awal))
        .join(Penyetoran, DetailPenyetoran.id_penyetoran == Penyetoran.id)
        .filter(func.date(Penyetoran.waktu_setor) == hari_ini)
        .scalar() or 0
    )

    # Total Kas RW yang sudah terkumpul dari alokasi 20%
    total_kas_rw = db.session.query(func.sum(Penjualan.bagian_kas)).scalar() or 0

    # 2. Status Sampah di Gudang Saat Ini
    antrean_menunggu = DetailPenyetoran.query.filter_by(status='menunggu').count()
    siap_jual = DetailPenyetoran.query.filter_by(status='siap_jual').count()
    total_terjual = DetailPenyetoran.query.filter_by(status='terjual').count()
    total_ditolak = DetailPenyetoran.query.filter_by(status='ditolak').count()

    # 3. Log Aktivitas Penyetoran Terkini Warga
    riwayat_aktivitas = (
        DetailPenyetoran.query
        .order_by(DetailPenyetoran.id.desc())
        .limit(15)
        .all()
    )

    return render_template(
        'dashboard/pengawas_dashboard.html',
        total_warga=total_warga,
        setoran_hari_ini=setoran_hari_ini,
        berat_masuk_hari_ini=berat_masuk_hari_ini,
        total_kas_rw=total_kas_rw,
        antrean_menunggu=antrean_menunggu,
        siap_jual=siap_jual,
        total_terjual=total_terjual,
        total_ditolak=total_ditolak,
        riwayat=riwayat_aktivitas,
        tanggal_hari_ini=hari_ini.strftime('%d %B %Y')
    )