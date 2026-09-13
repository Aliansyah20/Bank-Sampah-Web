import json
from datetime import date, timedelta
from flask import Blueprint, render_template, session
from sqlalchemy import func
from app.models import User, Penyetoran, DetailPenyetoran, Penjualan, JenisSampah
from app.extensions import db
from app.utils import role_required

pengawas_bp = Blueprint('pengawas', __name__)

@pengawas_bp.route('/dashboard')
@role_required(['pengawas'])
def dashboard():
    hari_ini = date.today()

    # 1. Metrik Utama Ringkup RW
    total_warga = User.query.filter_by(role='warga').count()
    setoran_hari_ini = Penyetoran.query.filter(func.date(Penyetoran.waktu_setor) == hari_ini).count()
    berat_masuk_hari_ini = (
        db.session.query(func.sum(DetailPenyetoran.berat_awal))
        .join(Penyetoran, DetailPenyetoran.id_penyetoran == Penyetoran.id)
        .filter(func.date(Penyetoran.waktu_setor) == hari_ini)
        .scalar() or 0
    )
    total_kas_rw = db.session.query(func.sum(Penjualan.bagian_kas)).scalar() or 0

    # 2. Status Sampah di Gudang
    antrean_menunggu = DetailPenyetoran.query.filter_by(status='menunggu').count()
    siap_jual = DetailPenyetoran.query.filter_by(status='siap_jual').count()
    total_terjual = DetailPenyetoran.query.filter_by(status='terjual').count()
    total_ditolak = DetailPenyetoran.query.filter_by(status='ditolak').count()

    # 3. Data Grafik 1: Tren Volume Sampah 7 Hari Terakhir (Bar Chart)
    tren_labels = []
    tren_data = []
    for i in range(6, -1, -1):
        tgl = hari_ini - timedelta(days=i)
        vol = (
            db.session.query(func.sum(DetailPenyetoran.berat_awal))
            .join(Penyetoran, DetailPenyetoran.id_penyetoran == Penyetoran.id)
            .filter(func.date(Penyetoran.waktu_setor) == tgl)
            .scalar() or 0
        )
        tren_labels.append(tgl.strftime('%d %b'))
        tren_data.append(float(vol))

    # 4. Data Grafik 2: Komposisi Kategori Sampah (Doughnut Chart)
    kategori_stats = (
        db.session.query(
            JenisSampah.nama_jenis,
            func.sum(DetailPenyetoran.berat_awal)
        )
        .join(DetailPenyetoran, JenisSampah.id == DetailPenyetoran.id_jenis_sampah)
        .group_by(JenisSampah.nama_jenis)
        .all()
    )
    cat_labels = [row[0] for row in kategori_stats] or ['Belum Ada']
    cat_data = [float(row[1]) for row in kategori_stats] or [0]

    # 5. Log Aktivitas Terakhir
    riwayat_aktivitas = DetailPenyetoran.query.order_by(DetailPenyetoran.id.desc()).limit(15).all()

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
        tanggal_hari_ini=hari_ini.strftime('%d %B %Y'),
        tren_labels=json.dumps(tren_labels),
        tren_data=json.dumps(tren_data),
        cat_labels=json.dumps(cat_labels),
        cat_data=json.dumps(cat_data)
    )