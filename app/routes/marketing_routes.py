from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import func
from app.models import DetailPenyetoran, Penjualan, User, JenisSampah
from app.extensions import db
from app.utils import role_required
import calendar
from datetime import datetime

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route('/dashboard')
@role_required(['marketing'])
def dashboard():
    # 1. Agregasi total stok siap jual per kategori sampah (tanpa identitas warga)
    stok_kategori = (
        db.session.query(
            JenisSampah.id.label('id_jenis'),
            JenisSampah.nama_jenis,
            func.sum(DetailPenyetoran.berat_verifikasi).label('total_berat'),
            func.count(DetailPenyetoran.id).label('jumlah_kantong')
        )
        .join(DetailPenyetoran, JenisSampah.id == DetailPenyetoran.id_jenis_sampah)
        .filter(DetailPenyetoran.status == 'siap_jual')
        .group_by(JenisSampah.id, JenisSampah.nama_jenis)
        .all()
    )

    # 2. Riwayat transaksi penjualan ke pengepul
    riwayat_penjualan = Penjualan.query.order_by(Penjualan.id.desc()).limit(20).all()
    total_kas_terkumpul = sum(p.bagian_kas for p in riwayat_penjualan)

    return render_template(
        'dashboard/marketing_dashboard.html',
        stok=stok_kategori,
        penjualan=riwayat_penjualan,
        total_kas=total_kas_terkumpul
    )

@marketing_bp.route('/jual/<int:id_jenis>', methods=['POST'])
@role_required(['marketing'])
def proses_penjualan(id_jenis):
    nama_pengepul = request.form.get('nama_pengepul', '').strip()
    harga_raw = request.form.get('harga_per_kg', '0').strip().replace(',', '.')

    # 1. Validasi input nama pengepul dan harga
    try:
        harga_per_kg = Decimal(harga_raw)
        if harga_per_kg <= 0 or not nama_pengepul:
            flash('Nama pengepul dan harga per Kg wajib diisi dengan benar!', 'danger')
            return redirect(url_for('marketing.dashboard'))
    except Exception:
        flash('Format harga jual tidak valid!', 'danger')
        return redirect(url_for('marketing.dashboard'))

    # 2. Ambil seluruh kantong sampah siap jual pada kategori jenis ini
    daftar_item = DetailPenyetoran.query.filter_by(
        id_jenis_sampah=id_jenis,
        status='siap_jual'
    ).all()

    if not daftar_item:
        flash('Stok sampah kategori ini kosong atau sudah terjual!', 'warning')
        return redirect(url_for('marketing.dashboard'))

    total_berat = sum(Decimal(str(item.berat_verifikasi)) for item in daftar_item)

    # 3. Batasan minimal 10 Kg untuk angkut pengepul
    if total_berat < Decimal('10.0'):
        flash(f'Total sampah baru terkumpul {total_berat:.2f} Kg. Batas minimal angkut pengepul adalah 10 Kg!', 'warning')
        return redirect(url_for('marketing.dashboard'))

    total_pendapatan_kategori = Decimal('0.0')
    total_bagi_warga = Decimal('0.0')
    total_bagi_kas = Decimal('0.0')

    # 4. Proses jual sekaligus dan bagi hasil otomatis ke masing-masing warga penyetor
    for item in daftar_item:
        berat_item = Decimal(str(item.berat_verifikasi))
        pendapatan_item = berat_item * harga_per_kg
        bagian_warga = pendapatan_item * Decimal('0.60')  # 60% Hak Warga
        bagian_kas = pendapatan_item * Decimal('0.40')    # 40% Kas RW

        total_pendapatan_kategori += pendapatan_item
        total_bagi_warga += bagian_warga
        total_bagi_kas += bagian_kas

        # Catat ke buku penjualan
        penjualan_baru = Penjualan(
            id_detail_penyetoran=item.id,
            id_marketing=session.get('user_id'),
            nama_pengepul=nama_pengepul,
            harga_per_kg=harga_per_kg,
            total_pendapatan=pendapatan_item,
            bagian_warga=bagian_warga,
            bagian_kas=bagian_kas
        )
        db.session.add(penjualan_baru)

        # Saldo otomatis masuk ke rekening tabungan warga penyetor
        warga = item.penyetoran.warga
        warga.saldo_terkini = Decimal(str(warga.saldo_terkini or 0)) + bagian_warga

        # Perbarui status item sampah
        item.status = 'terjual'

    db.session.commit()

    flash(
        f'Sukses menjual {total_berat:.2f} Kg ke {nama_pengepul}! Total: Rp {total_pendapatan_kategori:,.2f}. '
        f'Dana 80% (Rp {total_bagi_warga:,.2f}) otomatis masuk ke saldo warga penyetor, dan 20% (Rp {total_bagi_kas:,.2f}) masuk ke Kas RW.',
        'success'
    )
    return redirect(url_for('marketing.dashboard'))

# --- ROUTE CETAK LAPORAN REKAP BULANAN ---
@marketing_bp.route('/cetak-laporan')
@role_required(['marketing'])
def cetak_laporan():
    # Ambil bulan dan tahun dari parameter URL (bawaan: bulan & tahun berjalan)
    sekarang = datetime.now()
    tahun = int(request.args.get('tahun', sekarang.year))
    bulan = int(request.args.get('bulan', sekarang.month))

    # Tentukan rentang awal dan akhir bulan
    _, hari_terakhir = calendar.monthrange(tahun, bulan)
    waktu_mulai = datetime(tahun, bulan, 1, 0, 0, 0)
    waktu_selesai = datetime(tahun, bulan, hari_terakhir, 23, 59, 59)

    # Ambil seluruh transaksi penjualan pada rentang bulan tersebut
    daftar_penjualan = Penjualan.query.filter(
        Penjualan.tanggal_jual >= waktu_mulai,
        Penjualan.tanggal_jual <= waktu_selesai
    ).order_by(Penjualan.tanggal_jual.asc()).all()

    # Hitung ringkasan total otomatis
    total_omzet = sum(p.total_pendapatan for p in daftar_penjualan)
    total_warga = sum(p.bagian_warga for p in daftar_penjualan)
    total_kas = sum(p.bagian_kas for p in daftar_penjualan)
    total_berat = sum(p.detail.berat_verifikasi for p in daftar_penjualan if p.detail and p.detail.berat_verifikasi)

    daftar_nama_bulan = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    nama_bulan = daftar_nama_bulan[bulan]

    return render_template(
        'dashboard/cetak_laporan_marketing.html',
        daftar_penjualan=daftar_penjualan,
        bulan=bulan,
        tahun=tahun,
        nama_bulan=nama_bulan,
        total_omzet=total_omzet,
        total_warga=total_warga,
        total_kas=total_kas,
        total_berat=total_berat,
        tgl_cetak=sekarang.strftime('%d/%m/%Y %H:%M')
    )