from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # Role: sekben, pengolah, marketing, pengawas, warga
    role = db.Column(db.String(20), nullable=False, default='warga')
    saldo_terkini = db.Column(db.Numeric(12, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    penyetoran_warga = db.relationship('Penyetoran', foreign_keys='Penyetoran.id_warga', backref='warga', lazy=True)

class JenisSampah(db.Model):
    __tablename__ = 'jenis_sampah'
    id = db.Column(db.Integer, primary_key=True)
    nama_jenis = db.Column(db.String(50), nullable=False)

class Penyetoran(db.Model):
    __tablename__ = 'penyetoran'
    id = db.Column(db.Integer, primary_key=True)
    id_warga = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id_sekben = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    waktu_setor = db.Column(db.DateTime, default=datetime.utcnow)
    
    details = db.relationship('DetailPenyetoran', backref='penyetoran', lazy=True)

class DetailPenyetoran(db.Model):
    __tablename__ = 'detail_penyetoran'
    id = db.Column(db.Integer, primary_key=True)
    id_penyetoran = db.Column(db.Integer, db.ForeignKey('penyetoran.id'), nullable=False)
    id_jenis_sampah = db.Column(db.Integer, db.ForeignKey('jenis_sampah.id'), nullable=False)
    berat_awal = db.Column(db.Numeric(8, 2), nullable=False)
    berat_verifikasi = db.Column(db.Numeric(8, 2), nullable=True)
    id_pengolah = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Status alur: 'menunggu', 'siap_jual', 'ditolak', 'terjual'
    status = db.Column(db.String(20), default='menunggu')
    foto_bukti = db.Column(db.String(255), nullable=True)
    alasan_tolak = db.Column(db.String(255), nullable=True)

    jenis_sampah = db.relationship('JenisSampah', backref='detail_setoran', lazy=True)
    pengolah = db.relationship('User', foreign_keys=[id_pengolah], backref='verifikasi_pengolah', lazy=True)

class Penjualan(db.Model):
    __tablename__ = 'penjualan'
    id = db.Column(db.Integer, primary_key=True)
    id_detail_penyetoran = db.Column(db.Integer, db.ForeignKey('detail_penyetoran.id'), nullable=False)
    id_marketing = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    nama_pengepul = db.Column(db.String(100), nullable=False)
    harga_per_kg = db.Column(db.Numeric(10, 2), nullable=False)
    total_pendapatan = db.Column(db.Numeric(12, 2), nullable=False)
    bagian_warga = db.Column(db.Numeric(12, 2), nullable=False)      # 80%
    bagian_kas = db.Column(db.Numeric(12, 2), nullable=False)        # 20%
    tanggal_jual = db.Column(db.DateTime, default=datetime.utcnow)

    detail = db.relationship('DetailPenyetoran', backref='transaksi_penjualan', uselist=False)
    marketing = db.relationship('User', backref='riwayat_penjualan_marketing', lazy=True)