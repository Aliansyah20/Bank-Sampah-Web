from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import DetailPenyetoran, Penjualan, User
from app.extensions import db
from app.utils import role_required

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route('/dashboard')
@role_required(['marketing'])
def dashboard():
    # Mengambil stok sampah yang sudah disetujui pengolah
    stok_siap_jual = DetailPenyetoran.query.filter_by(status='siap_jual').all()
    riwayat_penjualan = Penjualan.query.order_by(Penjualan.id.desc()).all()
    total_kas_terkumpul = sum(p.bagian_kas for p in riwayat_penjualan)

    return render_template(
        'dashboard/marketing_dashboard.html',
        stok=stok_siap_jual,
        penjualan=riwayat_penjualan,
        total_kas=total_kas_terkumpul
    )

@marketing_bp.route('/jual/<int:detail_id>', methods=['POST'])
@role_required(['marketing'])
def proses_penjualan(detail_id):
    detail = DetailPenyetoran.query.get_or_404(detail_id)
    nama_pengepul = request.form.get('nama_pengepul', '').strip()
    harga_per_kg = Decimal(request.form.get('harga_per_kg', '0'))

    if not nama_pengepul or harga_per_kg <= 0:
        flash('Data pengepul dan harga per Kg harus diisi dengan benar!', 'danger')
        return redirect(url_for('marketing.dashboard'))

    # Perhitungan Transaksi & Bagi Hasil
    berat_sah = Decimal(str(detail.berat_verifikasi))
    total_pendapatan = berat_sah * harga_per_kg
    
    bagian_warga = total_pendapatan * Decimal('0.80') # 80% Hak Warga
    bagian_kas = total_pendapatan * Decimal('0.20')   # 20% Kas Bank Sampah

    # 1. Catat ke tabel Laporan Penjualan
    penjualan_baru = Penjualan(
        id_detail_penyetoran=detail.id,
        id_marketing=session.get('user_id'),
        nama_pengepul=nama_pengepul,
        harga_per_kg=harga_per_kg,
        total_pendapatan=total_pendapatan,
        bagian_warga=bagian_warga,
        bagian_kas=bagian_kas
    )
    db.session.add(penjualan_baru)

    # 2. Tambahkan hak bagi hasil 80% langsung ke saldo akun warga
    warga = detail.penyetoran.warga
    warga.saldo_terkini = Decimal(str(warga.saldo_terkini)) + bagian_warga

    # 3. Perbarui status sampah menjadi 'terjual'
    detail.status = 'terjual'

    db.session.commit()

    flash(
        f'Sukses menjual ke {nama_pengepul}! Total: Rp {total_pendapatan:,.2f}. '
        f'Saldo warga bertambah Rp {bagian_warga:,.2f} (80%), Kas Bank Sampah menerima Rp {bagian_kas:,.2f} (20%).',
        'success'
    )
    return redirect(url_for('marketing.dashboard'))