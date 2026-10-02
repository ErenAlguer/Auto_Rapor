"""
Araç Servis ve Periyodik Bakım Takip Otomasyonu
Uygulamanın ana başlangıç noktası (Entry Point).
"""

import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from database import DatabaseManager
from main_window import MainWindow


def seed_demo_data_if_empty(db: DatabaseManager):
    """İlk açılışta kullanıcının sistemi hemen deneyimleyebilmesi için örnek bir araç ve bakım kayıtları ekler."""
    if len(db.get_all_vehicles()) == 0:
        demo_plaka = "34 ABC 789"
        db.add_vehicle(
            plaka=demo_plaka,
            marka="Volkswagen",
            model="Golf 1.6 TDI Comfortline",
            yil=2019,
            sahip_ad_soyad="Ahmet Yılmaz",
            telefon="0532 123 45 67",
            notlar="Müşteri periyodik servis kullanıcısı. Triger seti 120.000 km'de değişecek."
        )

        db.add_maintenance(
            plaka=demo_plaka,
            tarih="2023-04-15",
            kilometre=45000,
            islem="Periyodik Yağ Bakımı (Yağ + Filtreler)",
            maliyet=2450.0,
            aciklama="Castrol 5W-30 Edge Motor Yağı, Mann Yağ/Hava/Polen Filtresi değişti."
        )
        db.add_maintenance(
            plaka=demo_plaka,
            tarih="2023-11-20",
            kilometre=58200,
            islem="Ön Fren Balatası Değişimi",
            maliyet=1850.0,
            aciklama="Ferodo marka ön balata takımı takıldı. Fren hidroliği seviyesi tamamlandı."
        )
        db.add_maintenance(
            plaka=demo_plaka,
            tarih="2024-06-10",
            kilometre=72000,
            islem="Sağ Ön Disk Değişimi",
            maliyet=3200.0,
            aciklama="Sağ ve sol ön fren diskleri takım olarak Brembo diskler ile yenilendi."
        )
        db.add_maintenance(
            plaka=demo_plaka,
            tarih="2024-12-05",
            kilometre=86500,
            islem="Klima Gazı Dolumu & Bakımı",
            maliyet=1500.0,
            aciklama="R134a klima gazı basıldı, polen filtresi yenilendi, ozonla dezenfekte edildi."
        )


def main():
    # Windows DPI ve Render ayarları
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("OtoServisTakip")
    app.setOrganizationName("OtoServis")

    # Genel Font
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)

    # Veritabanını başlat
    db = DatabaseManager()
    seed_demo_data_if_empty(db)

    # Ana pencereyi oluştur ve göster
    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
