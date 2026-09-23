from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import func
from app.models import User, Penjualan, Pengeluaran
from app.extensions import db
from app.utils import role_required

pengawas_bp = Blueprint('pengawas', __name__)

@pengawas_bp.route('/dashboard')
@role_required(['pengawas'])
def dashboard():
    # 1. Total Saldo
    total_kas_rw = db.session.query(func.sum(Penjualan.bagian_kas)).scalar() or Decimal('0.00')
    total_saldo_warga = db.session.query(func.sum(User.saldo_terkini)).filter_by(role='warga').scalar() or Decimal('0.00')
    total_seluruh_saldo = total_kas_rw + total_saldo_warga

    # 2. Antrean Verifikasi Registrasi Petugas (Admin selain warga)
    antrean_petugas = User.query.filter(User.role != 'warga', User.is_aktif == False).all()

    # 3. Data Warga untuk Pencairan Saldo
    daftar_warga = User.query.filter_by(role='warga').order_by(User.nama_lengkap.asc()).all()

    # 4. Riwayat Pengeluaran / Penarikan Dana
    riwayat_pengeluaran = Pengeluaran.query.order_by(Pengeluaran.id.desc()).limit(20).all()

    return render_template(
        'dashboard/pengawas_dashboard.html',
        total_kas_rw=total_kas_rw,
        total_saldo_warga=total_saldo_warga,
        total_seluruh_saldo=total_seluruh_saldo,
        antrean_petugas=antrean_petugas,
        daftar_warga=daftar_warga,
        riwayat_pengeluaran=riwayat_pengeluaran
    )

# --- VERIFIKASI REGISTRASI ADMIN / PETUGAS ---
@pengawas_bp.route('/verifikasi-petugas/<int:user_id>/<string:aksi>', methods=['POST'])
@role_required(['pengawas'])
def verifikasi_petugas(user_id, aksi):
    petugas = User.query.get_or_404(user_id)
    if aksi == 'setujui':
        petugas.is_aktif = True
        flash(f'Akun petugas {petugas.nama_lengkap} ({petugas.role}) berhasil disetujui & aktif!', 'success')
    else:
        db.session.delete(petugas)
        flash(f'Pendaftaran akun {petugas.nama_lengkap} telah ditolak dan dihapus.', 'warning')
    
    db.session.commit()
    return redirect(url_for('pengawas.dashboard'))

# --- HANYA PENGAWAS YANG BISA MENGELUARKAN UANG (TARIK SALDO PER WARGA) ---
@pengawas_bp.route('/cairkan-saldo-warga', methods=['POST'])
@role_required(['pengawas'])
def cairkan_saldo_warga():
    id_warga = request.form.get('id_warga')
    nominal_raw = request.form.get('nominal', '0').strip().replace(',', '.')
    keterangan = request.form.get('keterangan', 'Penarikan saldo tunai')

    try:
        nominal = Decimal(nominal_raw)
        if nominal <= 0:
            flash('Nominal penarikan harus lebih dari 0!', 'danger')
            return redirect(url_for('pengawas.dashboard'))
    except Exception:
        flash('Format nominal tidak valid!', 'danger')
        return redirect(url_for('pengawas.dashboard'))

    warga = User.query.get_or_404(id_warga)
    if (warga.saldo_terkini or 0) < nominal:
        flash(f'Gagal! Saldo warga tidak mencukupi (Saldo saat ini: Rp {warga.saldo_terkini:,.2f})', 'danger')
        return redirect(url_for('pengawas.dashboard'))

    # Kurangi saldo tabungan warga
    warga.saldo_terkini -= nominal

    # Catat buku pengeluaran kas
    pengeluaran = Pengeluaran(
        id_warga=warga.id,
        id_pengawas=session.get('user_id'),
        nominal=nominal,
        keterangan=keterangan
    )
    db.session.add(pengeluaran)
    db.session.commit()

    flash(f'Uang sebesar Rp {nominal:,.2f} berhasil dicairkan untuk {warga.nama_lengkap}. Sisa saldo: Rp {warga.saldo_terkini:,.2f}', 'success')
    return redirect(url_for('pengawas.dashboard'))