"""
Araç Servis Takip Otomasyonu - Veritabanı Modülü (SQLite)
Araclar ve Bakimlar tabloları ile ilişkisel veri yönetimi sağlar.
"""

import os
import sys
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DEFAULT_OPERATIONS = [
    "Periyodik Yağ Bakımı (Yağ + Filtreler)",
    "Motor Yağı ve Yağ Filtresi Değişimi",
    "Hava Filtresi & Polen Filtresi Değişimi",
    "Yakıt (Mazot/Benzin) Filtresi Değişimi",
    "Ön Fren Balatası Değişimi",
    "Arka Fren Balatası Değişimi",
    "Ön Fren Disk Değişimi",
    "Arka Fren Disk Değişimi",
    "Sağ Ön Disk Değişimi",
    "Sol Ön Disk Değişimi",
    "Fren Hidrolik Yağı Değişimi",
    "Buji Değişimi (Takım)",
    "Akü Değişimi & Şarj Kontrolü",
    "Triger Kayışı / Seti Değişimi",
    "V Kayışı & Gergi Rulmanı Değişimi",
    "Devirdaim Su Pompası Değişimi",
    "Antifriz Değişimi & Soğutma Sıvısı Kontrolü",
    "Amortisör & Alt Takım Onarımı",
    "Rot Başı & Salıncak Burçları Değişimi",
    "Rot-Balans ve Ön Düzen Ayarı",
    "Klima Gazı Dolumu & Gaz Kaçak Kontrolü",
    "Şanzıman Yağı Değişimi",
    "Debriyaj Baskı Balata Değişimi",
    "Ateşleme Bobini Değişimi",
    "Egzoz & Katalizör Onarımı",
    "Genel Servis Kontrolü & Bilgisayarlı Arıza Tespiti",
]


import shutil


def get_safe_appdata_dir() -> str:
    """Windows üzerinde kalıcı ve bağımsız veritabanı dizinini döner (%APPDATA%/AracServis)."""
    app_data = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    target_dir = os.path.join(app_data, "AracServis")
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


def get_default_db_path() -> str:
    """
    Veritabanı dosyasının kalıcı ve bağımsız konumunu belirler (%APPDATA%/AracServis/servis.db).
    Program her açıldığında bu dizini kontrol eder; dizin veya dosya yoksa sıfırdan oluşturulur.
    Böylece programın yüklendiği her bilgisayar tamamen kendine ait, bağımsız bir veritabanı ile başlar.
    """
    safe_dir = get_safe_appdata_dir()
    appdata_db = os.path.join(safe_dir, "servis.db")

    # Eğer AppData/AracServis altında henüz veritabanı yoksa, önceki konumlardan veri kurtarmayı dene
    if not os.path.exists(appdata_db) or os.path.getsize(appdata_db) == 0:
        app_data = os.environ.get("APPDATA") or ""
        candidates = [
            os.path.join(app_data, "AutoServisTakip", "servis_takip.db"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "servis.db"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "servis_takip.db"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "servis.db"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "servis_takip.db"),
        ]
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            candidates.insert(0, os.path.join(exe_dir, "servis.db"))

        for cand in candidates:
            if cand and os.path.exists(cand) and os.path.getsize(cand) > 0:
                try:
                    shutil.copy2(cand, appdata_db)
                    break
                except Exception:
                    pass

    return appdata_db


from contextlib import contextmanager

class DatabaseManager:
    """SQLite veritabanı işlemlerini yürüten sınıf."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        self.init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Tabloları ve indeksleri oluşturur."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Araclar tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Araclar (
                    plaka TEXT PRIMARY KEY,
                    marka TEXT NOT NULL,
                    model TEXT NOT NULL,
                    yil INTEGER,
                    sahip_ad_soyad TEXT,
                    telefon TEXT,
                    notlar TEXT,
                    kayit_tarihi TEXT
                );
            """)

            # Bakimlar tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Bakimlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plaka TEXT NOT NULL,
                    tarih TEXT NOT NULL,
                    kilometre INTEGER NOT NULL DEFAULT 0,
                    islem TEXT NOT NULL,
                    maliyet REAL NOT NULL DEFAULT 0.0,
                    aciklama TEXT,
                    kayit_tarihi TEXT,
                    FOREIGN KEY (plaka) REFERENCES Araclar(plaka) 
                        ON UPDATE CASCADE 
                        ON DELETE CASCADE
                );
            """)

            # İndeksler
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bakimlar_plaka ON Bakimlar(plaka);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bakimlar_tarih ON Bakimlar(tarih);")
            conn.commit()

    @staticmethod
    def normalize_plate(plate: str) -> str:
        """Plakayı büyük harflere dönüştürüp aradaki fazla boşlukları temizler."""
        if not plate:
            return ""
        # Türkçe karakter duyarlı büyütme
        tr_map = str.maketrans("iı", "İI")
        plate = plate.translate(tr_map).upper()
        # Çoklu boşlukları teke indir
        parts = plate.split()
        return " ".join(parts).strip()

    # --- Araç İşlemleri ---

    def add_vehicle(self, plaka: str, marka: str, model: str, yil: Optional[int],
                    sahip_ad_soyad: str, telefon: str, notlar: str = "") -> bool:
        """Yeni bir araç ekler."""
        norm_plaka = self.normalize_plate(plaka)
        if not norm_plaka:
            raise ValueError("Plaka boş bırakılamaz.")

        kayit_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Araclar (plaka, marka, model, yil, sahip_ad_soyad, telefon, notlar, kayit_tarihi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (norm_plaka, marka.strip(), model.strip(), yil, sahip_ad_soyad.strip(), telefon.strip(), notlar.strip(), kayit_tarihi))
            conn.commit()
            return True

    def update_vehicle(self, old_plaka: str, new_plaka: str, marka: str, model: str,
                       yil: Optional[int], sahip_ad_soyad: str, telefon: str, notlar: str = "") -> bool:
        """Mevcut bir aracın bilgilerini ve gerekirse plakasını günceller."""
        old_norm = self.normalize_plate(old_plaka)
        new_norm = self.normalize_plate(new_plaka)
        if not new_norm:
            raise ValueError("Plaka boş bırakılamaz.")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Araclar 
                SET plaka = ?, marka = ?, model = ?, yil = ?, sahip_ad_soyad = ?, telefon = ?, notlar = ?
                WHERE plaka = ?
            """, (new_norm, marka.strip(), model.strip(), yil, sahip_ad_soyad.strip(), telefon.strip(), notlar.strip(), old_norm))
            conn.commit()
            return cursor.rowcount > 0

    def get_vehicle(self, plaka: str) -> Optional[Dict[str, Any]]:
        """Plakaya göre araç kaydını getirir."""
        norm_plaka = self.normalize_plate(plaka)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Araclar WHERE plaka = ?", (norm_plaka,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def delete_vehicle(self, plaka: str) -> bool:
        """Aracı ve ona bağlı tüm bakım kayıtlarını siler."""
        norm_plaka = self.normalize_plate(plaka)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Araclar WHERE plaka = ?", (norm_plaka,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Tüm kayıtlı araçları listeler."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Araclar ORDER BY plaka ASC")
            return [dict(row) for row in cursor.fetchall()]

    def search_vehicles(self, query: str) -> List[Dict[str, Any]]:
        """Plaka, araç sahibi veya marka/model araması yapar."""
        q = f"%{query.strip()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM Araclar 
                WHERE plaka LIKE ? OR sahip_ad_soyad LIKE ? OR marka LIKE ? OR model LIKE ?
                ORDER BY plaka ASC
            """, (q, q, q, q))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_vehicles_with_stats(self, query: str = "") -> List[Dict[str, Any]]:
        """
        Araçları bakım istatistikleriyle (toplam bakım sayısı, son km, son tarih, toplam harcama)
        birlikte döner. Query verilirse plaka, sahip, marka, model veya telefona göre filtreler.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if query.strip():
                q = f"%{query.strip()}%"
                cursor.execute("""
                    SELECT 
                        a.plaka, a.marka, a.model, a.yil, a.sahip_ad_soyad, a.telefon, a.notlar, a.kayit_tarihi,
                        COUNT(b.id) as toplam_bakim,
                        COALESCE(MAX(b.kilometre), 0) as son_km,
                        COALESCE(MAX(b.tarih), '-') as son_tarih,
                        COALESCE(SUM(b.maliyet), 0.0) as toplam_harcama
                    FROM Araclar a
                    LEFT JOIN Bakimlar b ON a.plaka = b.plaka
                    WHERE a.plaka LIKE ? OR a.sahip_ad_soyad LIKE ? OR a.marka LIKE ? OR a.model LIKE ? OR a.telefon LIKE ?
                    GROUP BY a.plaka
                    ORDER BY a.plaka ASC
                """, (q, q, q, q, q))
            else:
                cursor.execute("""
                    SELECT 
                        a.plaka, a.marka, a.model, a.yil, a.sahip_ad_soyad, a.telefon, a.notlar, a.kayit_tarihi,
                        COUNT(b.id) as toplam_bakim,
                        COALESCE(MAX(b.kilometre), 0) as son_km,
                        COALESCE(MAX(b.tarih), '-') as son_tarih,
                        COALESCE(SUM(b.maliyet), 0.0) as toplam_harcama
                    FROM Araclar a
                    LEFT JOIN Bakimlar b ON a.plaka = b.plaka
                    GROUP BY a.plaka
                    ORDER BY a.plaka ASC
                """)
            return [dict(row) for row in cursor.fetchall()]

    def get_all_plates(self) -> List[str]:
        """Otomatik tamamlama için kayıtlı tüm plakaları döner."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT plaka FROM Araclar ORDER BY plaka ASC")
            return [row["plaka"] for row in cursor.fetchall()]

    # --- Bakım İşlemleri ---

    def add_maintenance(self, plaka: str, tarih: str, kilometre: int,
                        islem: str, maliyet: float, aciklama: str = "") -> int:
        """Yeni bir bakım kaydı ekler ve eklenen ID'yi döner."""
        norm_plaka = self.normalize_plate(plaka)
        if not norm_plaka:
            raise ValueError("Plaka belirtilmelidir.")
        if not islem.strip():
            raise ValueError("Yapılan işlem boş bırakılamaz.")

        kayit_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Bakimlar (plaka, tarih, kilometre, islem, maliyet, aciklama, kayit_tarihi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (norm_plaka, tarih.strip(), int(kilometre), islem.strip(), float(maliyet), aciklama.strip(), kayit_tarihi))
            conn.commit()
            return cursor.lastrowid

    def update_maintenance(self, maintenance_id: int, tarih: str, kilometre: int,
                           islem: str, maliyet: float, aciklama: str = "") -> bool:
        """Bakım kaydını günceller."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Bakimlar
                SET tarih = ?, kilometre = ?, islem = ?, maliyet = ?, aciklama = ?
                WHERE id = ?
            """, (tarih.strip(), int(kilometre), islem.strip(), float(maliyet), aciklama.strip(), int(maintenance_id)))
            conn.commit()
            return cursor.rowcount > 0

    def delete_maintenance(self, maintenance_id: int) -> bool:
        """Bakım kaydını siler."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Bakimlar WHERE id = ?", (int(maintenance_id),))
            conn.commit()
            return cursor.rowcount > 0

    def get_maintenances_by_plate(self, plaka: str, chronological_desc: bool = True) -> List[Dict[str, Any]]:
        """
        Belirtilen plakaya ait tüm bakım işlemlerini kronolojik olarak döner.
        chronological_desc=True -> En yeniden eskiye (önerilen varsayılan)
        chronological_desc=False -> Eskiden yeniye
        """
        norm_plaka = self.normalize_plate(plaka)
        order = "DESC" if chronological_desc else "ASC"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM Bakimlar 
                WHERE plaka = ? 
                ORDER BY tarih {order}, id {order}
            """, (norm_plaka,))
            return [dict(row) for row in cursor.fetchall()]

    def get_vehicle_summary(self, plaka: str) -> Dict[str, Any]:
        """Bir aracın toplam bakım sayısı, son km'si, son bakım tarihi ve toplam tutarını döner."""
        norm_plaka = self.normalize_plate(plaka)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as toplam_bakim,
                    COALESCE(SUM(maliyet), 0.0) as toplam_harcama,
                    COALESCE(MAX(kilometre), 0) as son_km,
                    COALESCE(MAX(tarih), '-') as son_tarih
                FROM Bakimlar 
                WHERE plaka = ?
            """, (norm_plaka,))
            row = cursor.fetchone()
            return dict(row) if row else {
                "toplam_bakim": 0, "toplam_harcama": 0.0, "son_km": 0, "son_tarih": "-"
            }

    def get_distinct_operations(self) -> List[str]:
        """
        Daha önce girilmiş işlemler ile varsayılan standart servis işlemleri listesini
        birleştirip sıralı ve benzersiz olarak döner.
        """
        ops_set = set(DEFAULT_OPERATIONS)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT islem FROM Bakimlar WHERE islem IS NOT NULL AND trim(islem) != ''")
            for row in cursor.fetchall():
                ops_set.add(row["islem"].strip())
        
        return sorted(list(ops_set), key=lambda x: x.lower())

    # --- Yedekleme ve Veritabanı Yönetimi ---

    def backup_database(self, destination_path: str) -> bool:
        """
        Aktif veritabanını SQLite'ın güvenli online backup API'si ile hedef dosyaya yedekler.
        İşlem sırasında veri kaybı veya kilitlenme yaşanmaz.
        """
        if not destination_path.lower().endswith(".db"):
            destination_path += ".db"

        # Hedef dizini oluştur
        os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)

        with self._get_connection() as src_conn:
            dst_conn = sqlite3.connect(destination_path)
            try:
                src_conn.backup(dst_conn)
                return True
            finally:
                dst_conn.close()

    def restore_database(self, source_path: str) -> bool:
        """
        Yedek bir .db dosyasından verileri doğrular ve aktif veritabanına geri yükler.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Yedek dosyası bulunamadı: {source_path}")

        # Doğrulama: dosya geçerli bir SQLite veritabanı mı ve gerekli tablolar var mı?
        test_conn = sqlite3.connect(source_path)
        try:
            cur = test_conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Araclar', 'Bakimlar');")
            tables = [row[0] for row in cur.fetchall()]
            if 'Araclar' not in tables or 'Bakimlar' not in tables:
                raise ValueError("Seçilen dosya geçerli bir Servis Takip veritabanı yedeği değil (Tablolar eksik).")
        finally:
            test_conn.close()

        # Doğrulandıysa, kopyala
        shutil.copy2(source_path, self.db_path)
        return True

    def get_db_info(self) -> Dict[str, Any]:
        """Aktif veritabanı dosyası hakkında ayrıntılı durum bilgisi döner."""
        exists = os.path.exists(self.db_path)
        size_kb = (os.path.getsize(self.db_path) / 1024.0) if exists else 0.0
        mtime = datetime.fromtimestamp(os.path.getmtime(self.db_path)).strftime("%d.%m.%Y %H:%M:%S") if exists else "-"

        vehicle_count = 0
        maintenance_count = 0
        if exists:
            try:
                with self._get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM Araclar")
                    vehicle_count = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM Bakimlar")
                    maintenance_count = cur.fetchone()[0]
            except Exception:
                pass

        return {
            "path": os.path.abspath(self.db_path),
            "size_kb": size_kb,
            "vehicle_count": vehicle_count,
            "maintenance_count": maintenance_count,
            "last_modified": mtime,
        }

    def open_db_directory(self):
        """Veritabanı dosyasının bulunduğu klasörü Windows Gezgini'nde açar."""
        folder = os.path.dirname(os.path.abspath(self.db_path))
        if os.path.exists(folder):
            os.startfile(folder)
