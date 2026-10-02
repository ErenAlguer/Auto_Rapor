"""
Araç Servis Takip Otomasyonu - Ana Kullanıcı Arayüzü Penceresi (PyQt6)
Plaka bazlı arama, kronolojik bakım dökümü, araç künyesi, yazdırma ve PDF entegrasyonu.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QFont, QIcon, QAction, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QCompleter, QStatusBar,
    QAbstractItemView, QListWidget, QListWidgetItem, QMenu, QFileDialog
)

from database import DatabaseManager
from dialogs import VehicleDialog, MaintenanceDialog, VehicleListDialog
from printer_service import PrintService


MODERN_STYLE = """
QMainWindow {
    background-color: #f1f5f9;
}
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    color: #1e293b;
}
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}
QFrame#topBar {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}
QFrame#topBar QPushButton {
    padding: 5px 8px;
    font-size: 8.5pt;
    border-radius: 4px;
}
QLineEdit {
    background-color: #ffffff;
    border: 1.5px solid #94a3b8;
    border-radius: 5px;
    padding: 5px 9px;
    font-size: 9.5pt;
}
QLineEdit:focus {
    border: 2px solid #0284c7;
    background-color: #ffffff;
}
QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 5px;
    padding: 6px 11px;
    font-size: 9pt;
}
QPushButton:hover {
    background-color: #0369a1;
}
QPushButton:pressed {
    background-color: #075985;
}
QPushButton#btnSuccess {
    background-color: #16a34a;
}
QPushButton#btnSuccess:hover {
    background-color: #15803d;
}
QPushButton#btnWarning {
    background-color: #ea580c;
}
QPushButton#btnWarning:hover {
    background-color: #c2410c;
}
QPushButton#btnSecondary {
    background-color: #475569;
}
QPushButton#btnSecondary:hover {
    background-color: #334155;
}
QPushButton#btnDanger {
    background-color: #dc2626;
}
QPushButton#btnDanger:hover {
    background-color: #b91c1c;
}
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    gridline-color: #f1f5f9;
    selection-background-color: #e0f2fe;
    selection-color: #0369a1;
}
QHeaderView::section {
    background-color: #f8fafc;
    color: #334155;
    font-weight: 700;
    padding: 8px 6px;
    border: none;
    border-bottom: 2px solid #cbd5e1;
    font-size: 10pt;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
}
QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #f1f5f9;
}
QListWidget::item:selected {
    background-color: #e0f2fe;
    color: #0369a1;
    font-weight: bold;
}
QListWidget::item:hover {
    background-color: #f8fafc;
}
QStatusBar {
    background-color: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
}
"""


class MainWindow(QMainWindow):
    """Ana uygulama penceresi."""

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.current_vehicle: Optional[Dict[str, Any]] = None
        self.current_maintenances: List[Dict[str, Any]] = []

        self.setWindowTitle("Oto Servis & Periyodik Bakım Takip Otomasyonu")
        self.resize(1180, 740)
        self.setMinimumSize(950, 600)
        self.setStyleSheet(MODERN_STYLE)

        self.setup_ui()
        self.setup_statusbar()
        self.refresh_all()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # --- 1. ÜST BAR: PLAKA ARAMA VE ANA EYLEMLER ---
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 5, 8, 5)
        top_layout.setSpacing(5)

        # Logo / Başlık
        brand_label = QLabel("🛠️ SERVİS TAKİP")
        brand_label.setStyleSheet("font-size: 10.5pt; font-weight: 900; color: #0369a1; margin-right: 4px;")
        top_layout.addWidget(brand_label)

        # Plaka Arama Girişi (Kullanıcı plaka yazıp Enter'a basabilir veya listeden seçebilir)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Plaka Ara...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(175)
        self.search_input.returnPressed.connect(self.search_plate)
        self.search_input.textChanged.connect(self._format_search_input)
        top_layout.addWidget(self.search_input)

        # Otomatik tamamlama
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.completer.activated.connect(self._on_completer_activated)
        self.search_input.setCompleter(self.completer)

        top_layout.addStretch()

        # Eylem Butonları
        self.btn_vehicle_list = QPushButton("📋 Araç Listesi")
        self.btn_vehicle_list.setToolTip("Kayıtlı tüm araçları listele ve detaylı arama yap")
        self.btn_vehicle_list.clicked.connect(self.open_vehicle_list_dialog)
        top_layout.addWidget(self.btn_vehicle_list)

        self.btn_new_vehicle = QPushButton("➕ Yeni Araç")
        self.btn_new_vehicle.clicked.connect(self.open_new_vehicle_dialog)
        top_layout.addWidget(self.btn_new_vehicle)

        self.btn_add_maintenance = QPushButton("🔧 Bakım Ekle")
        self.btn_add_maintenance.setObjectName("btnSuccess")
        self.btn_add_maintenance.clicked.connect(self.open_add_maintenance_dialog)
        top_layout.addWidget(self.btn_add_maintenance)

        self.btn_preview = QPushButton("👁️ Önizleme")
        self.btn_preview.setObjectName("btnSecondary")
        self.btn_preview.clicked.connect(self.preview_service_report)
        top_layout.addWidget(self.btn_preview)

        self.btn_print = QPushButton("🖨️ Yazdır")
        self.btn_print.setObjectName("btnSecondary")
        self.btn_print.clicked.connect(self.print_service_report)
        top_layout.addWidget(self.btn_print)

        self.btn_pdf = QPushButton("📄 PDF")
        self.btn_pdf.setObjectName("btnWarning")
        self.btn_pdf.clicked.connect(self.export_pdf)
        top_layout.addWidget(self.btn_pdf)

        # Veritabanı Yönetimi Butonu ve Açılır Menüsü
        self.btn_db = QPushButton("💾 Veritabanı")
        self.btn_db.setObjectName("btnSecondary")
        db_menu = QMenu(self)
        
        act_backup = db_menu.addAction("💾 Veritabanı Yedeği Al (Dışa Aktar)...")
        act_backup.triggered.connect(self.backup_database_action)
        
        act_restore = db_menu.addAction("📥 Yedekten Geri Yükle...")
        act_restore.triggered.connect(self.restore_database_action)
        
        db_menu.addSeparator()
        
        act_open_dir = db_menu.addAction("📁 Veritabanı Klasörünü Aç (Windows)")
        act_open_dir.triggered.connect(self.open_db_folder_action)
        
        act_info = db_menu.addAction("ℹ️ Veritabanı Durumu & Bilgi...")
        act_info.triggered.connect(self.show_db_info_action)
        
        self.btn_db.setMenu(db_menu)
        top_layout.addWidget(self.btn_db)

        self.btn_refresh = QPushButton("🔄 Yenile")
        self.btn_refresh.setObjectName("btnSecondary")
        self.btn_refresh.clicked.connect(self.refresh_all)
        top_layout.addWidget(self.btn_refresh)

        main_layout.addWidget(top_bar)

        # --- 2. ORTA BÖLÜM: SOL KÜNYE & SAĞ BAKIM TABLOSU (SPLITTER) ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # Sol Panel (Araç Künyesi + Hızlı Liste)
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        # Plaka Plaket Görünümü
        self.plate_badge = QLabel("PLAKA SEÇİLMEDİ")
        self.plate_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plate_badge.setStyleSheet("""
            background-color: #0f172a;
            color: #ffffff;
            font-size: 16pt;
            font-weight: 800;
            padding: 8px 14px;
            border-radius: 6px;
            border: 2px solid #38bdf8;
            letter-spacing: 1px;
        """)
        left_layout.addWidget(self.plate_badge)

        # Araç Detay Bilgileri
        self.vehicle_info_label = QLabel("Aramak için yukarıya bir plaka yazın veya aşağıdaki listeden bir araç seçin.")
        self.vehicle_info_label.setWordWrap(True)
        self.vehicle_info_label.setStyleSheet("color: #475569; font-size: 10.5pt; line-height: 1.5;")
        left_layout.addWidget(self.vehicle_info_label)

        # İstatistik Kutusu
        self.stats_box = QFrame()
        self.stats_box.setStyleSheet("background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 10px;")
        stats_layout = QVBoxLayout(self.stats_box)
        stats_layout.setSpacing(6)

        self.lbl_stat_count = QLabel("Toplam Bakım: -")
        self.lbl_stat_km = QLabel("Son Kilometre: -")
        self.lbl_stat_date = QLabel("Son İşlem Tarihi: -")
        self.lbl_stat_total = QLabel("Toplam Servis Harcaması: -")
        self.lbl_stat_total.setStyleSheet("font-weight: bold; color: #0369a1; font-size: 11pt;")

        stats_layout.addWidget(self.lbl_stat_count)
        stats_layout.addWidget(self.lbl_stat_km)
        stats_layout.addWidget(self.lbl_stat_date)
        stats_layout.addWidget(self.lbl_stat_total)
        left_layout.addWidget(self.stats_box)

        # Araç Butonları (Düzenle / Sil)
        vehicle_btn_layout = QHBoxLayout()
        self.btn_edit_vehicle = QPushButton("✏️ Düzenle")
        self.btn_edit_vehicle.setObjectName("btnSecondary")
        self.btn_edit_vehicle.clicked.connect(self.open_edit_vehicle_dialog)
        vehicle_btn_layout.addWidget(self.btn_edit_vehicle)

        self.btn_delete_vehicle = QPushButton("🗑️ Sil")
        self.btn_delete_vehicle.setObjectName("btnDanger")
        self.btn_delete_vehicle.clicked.connect(self.delete_current_vehicle)
        vehicle_btn_layout.addWidget(self.btn_delete_vehicle)
        left_layout.addLayout(vehicle_btn_layout)

        # Hızlı Araç Seçim Listesi
        list_header_layout = QHBoxLayout()
        lbl_list_title = QLabel("Kayıtlı Araçlar:")
        lbl_list_title.setStyleSheet("font-weight: bold; color: #334155;")
        list_header_layout.addWidget(lbl_list_title)
        list_header_layout.addStretch()

        btn_view_all = QPushButton("🔍 Ara / Liste")
        btn_view_all.setObjectName("btnSecondary")
        btn_view_all.setStyleSheet("padding: 2px 8px; font-size: 8.5pt;")
        btn_view_all.clicked.connect(self.open_vehicle_list_dialog)
        list_header_layout.addWidget(btn_view_all)
        left_layout.addLayout(list_header_layout)

        self.vehicles_list = QListWidget()
        self.vehicles_list.itemClicked.connect(self._on_vehicle_list_item_clicked)
        left_layout.addWidget(self.vehicles_list)

        left_panel.setFixedWidth(320)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(left_panel)

        # Sağ Panel: Kronolojik Bakım Geçmişi Tablosu
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)

        # Sağ Panel Başlığı
        right_header = QHBoxLayout()
        self.history_title = QLabel("Kronolojik Bakım ve Onarım Geçmişi")
        self.history_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #0f172a;")
        right_header.addWidget(self.history_title)
        right_header.addStretch()

        self.lbl_records_count = QLabel("0 Kayıt")
        self.lbl_records_count.setStyleSheet("color: #64748b; font-weight: 600;")
        right_header.addWidget(self.lbl_records_count)
        right_layout.addLayout(right_header)

        # Bakım Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Kilometre", "Yapılan İşlem", "Açıklama / Parça Notu", "Tutar (₺)", "İşlemler"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)  # ID sütununu gizle

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table.cellDoubleClicked.connect(self._on_table_row_double_click)
        right_layout.addWidget(self.table)

        # Alt Toplamlar Barı
        bottom_summary_layout = QHBoxLayout()
        bottom_summary_layout.addStretch()

        self.lbl_grand_total = QLabel("Seçili Araç Genel Toplam: 0,00 ₺")
        self.lbl_grand_total.setStyleSheet("""
            background-color: #e0f2fe;
            color: #0369a1;
            font-size: 12pt;
            font-weight: 800;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #7dd3fc;
        """)
        bottom_summary_layout.addWidget(self.lbl_grand_total)
        right_layout.addLayout(bottom_summary_layout)

        splitter.addWidget(right_panel)
        splitter.setSizes([320, 800])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.db_status_label = QLabel("[SQLite] Bağlı")
        self.db_status_label.setStyleSheet("color: #16a34a; font-weight: bold; margin-left: 8px;")
        self.statusbar.addWidget(self.db_status_label)

        self.status_label = QLabel("Hazır")
        self.statusbar.addPermanentWidget(self.status_label)

    def _format_search_input(self, text: str):
        pos = self.search_input.cursorPosition()
        upper = self.db.normalize_plate(text)
        if upper != text:
            self.search_input.blockSignals(True)
            self.search_input.setText(upper)
            self.search_input.setCursorPosition(min(pos, len(upper)))
            self.search_input.blockSignals(False)

    def _on_completer_activated(self, text: str):
        self.search_input.setText(text)
        self.search_plate()

    def _on_vehicle_list_item_clicked(self, item: QListWidgetItem):
        plaka = item.data(Qt.ItemDataRole.UserRole)
        if plaka:
            self.search_input.setText(plaka)
            self.load_vehicle(plaka)

    def refresh_all(self):
        """Kayıtlı plakaları, hızlı araç listesini ve varsa mevcut aracı yeniler."""
        plates = self.db.get_all_plates()
        self.completer_model.setStringList(plates)

        # Sol araç listesini doldur
        self.vehicles_list.clear()
        vehicles = self.db.get_all_vehicles()
        for v in vehicles:
            p = v["plaka"]
            marka_model = f"{v.get('marka', '')} {v.get('model', '')}".strip()
            sahip = v.get("sahip_ad_soyad", "")
            display_text = f"🚗 {p} - {marka_model}"
            if sahip:
                display_text += f" ({sahip})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, p)
            self.vehicles_list.addItem(item)

        info = self.db.get_db_info()
        self.db_status_label.setText(f"[SQLite] {info['path']}")
        self.status_label.setText(f"Kayıtlı: {len(vehicles)} Araç | {info['maintenance_count']} Bakım")

        # Eğer zaten bir araç açıksa onu tazele
        if self.current_vehicle:
            self.load_vehicle(self.current_vehicle["plaka"])
        elif plates:
            # İlk aracı otomatik yükle
            self.load_vehicle(plates[0])
            self.search_input.setText(plates[0])
        else:
            self._clear_view()

    def search_plate(self):
        plaka = self.db.normalize_plate(self.search_input.text())
        if not plaka:
            QMessageBox.information(self, "Bilgi", "Lütfen aramak istediğiniz plakayı yazınız.")
            return

        vehicle = self.db.get_vehicle(plaka)
        if not vehicle:
            reply = QMessageBox.question(
                self, "Araç Bulunamadı",
                f"'{plaka}' plakalı araç sistemde kayıtlı değil.\n\nŞimdi yeni araç olarak kaydetmek ister misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.open_new_vehicle_dialog(initial_plate=plaka)
            return

        self.load_vehicle(plaka)

    def load_vehicle(self, plaka: str):
        """Seçilen plakaya ait araç künyesini ve bakım tablosunu yükler."""
        norm_plaka = self.db.normalize_plate(plaka)
        vehicle = self.db.get_vehicle(norm_plaka)
        if not vehicle:
            self._clear_view()
            return

        self.current_vehicle = vehicle
        self.plate_badge.setText(norm_plaka)

        # Künye metni
        marka = vehicle.get("marka", "-")
        model = vehicle.get("model", "-")
        yil = vehicle.get("yil") or "-"
        sahip = vehicle.get("sahip_ad_soyad") or "-"
        telefon = vehicle.get("telefon") or "-"
        notlar = vehicle.get("notlar") or "-"

        info_text = (
            f"<b>Marka / Model:</b> {marka} {model}<br/>"
            f"<b>Model Yılı:</b> {yil}<br/>"
            f"<b>Araç Sahibi:</b> {sahip}<br/>"
            f"<b>İletişim:</b> {telefon}<br/>"
            f"<b>Notlar:</b> {notlar}"
        )
        self.vehicle_info_label.setText(info_text)

        # İstatistikler
        summary = self.db.get_vehicle_summary(norm_plaka)
        toplam_bakim = summary.get("toplam_bakim", 0)
        son_km = summary.get("son_km", 0)
        son_tarih = summary.get("son_tarih", "-")
        toplam_harcama = summary.get("toplam_harcama", 0.0)

        # Son tarihi formatla
        if son_tarih and son_tarih != "-":
            try:
                son_tarih = datetime.strptime(son_tarih, "%Y-%m-%d").strftime("%d.%m.%Y")
            except Exception:
                pass

        km_str = f"{son_km:,} km".replace(",", ".") if son_km > 0 else "-"
        harcama_str = f"{toplam_harcama:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")

        self.lbl_stat_count.setText(f"Toplam Bakım: <b>{toplam_bakim} adet</b>")
        self.lbl_stat_km.setText(f"Son Kilometre: <b>{km_str}</b>")
        self.lbl_stat_date.setText(f"Son İşlem Tarihi: <b>{son_tarih}</b>")
        self.lbl_stat_total.setText(f"Toplam Harcama: {harcama_str}")
        self.lbl_grand_total.setText(f"Seçili Araç Genel Toplam: {harcama_str}")

        # Bakım Tablosunu Doldur (Kronolojik)
        self.current_maintenances = self.db.get_maintenances_by_plate(norm_plaka, chronological_desc=True)
        self.table.setRowCount(len(self.current_maintenances))
        self.lbl_records_count.setText(f"{len(self.current_maintenances)} Kayıt")

        for row_idx, m in enumerate(self.current_maintenances):
            # ID
            item_id = QTableWidgetItem(str(m["id"]))
            self.table.setItem(row_idx, 0, item_id)

            # Tarih
            t_raw = m.get("tarih", "")
            try:
                t_fmt = datetime.strptime(t_raw, "%Y-%m-%d").strftime("%d.%m.%Y")
            except Exception:
                t_fmt = t_raw
            item_tarih = QTableWidgetItem(t_fmt)
            item_tarih.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, item_tarih)

            # Kilometre
            km_val = f"{m.get('kilometre', 0):,} km".replace(",", ".")
            item_km = QTableWidgetItem(km_val)
            item_km.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 2, item_km)

            # İşlem
            item_islem = QTableWidgetItem(m.get("islem", ""))
            item_islem.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row_idx, 3, item_islem)

            # Açıklama
            item_aciklama = QTableWidgetItem(m.get("aciklama", ""))
            self.table.setItem(row_idx, 4, item_aciklama)

            # Maliyet
            maliyet_val = f"{m.get('maliyet', 0.0):,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
            item_maliyet = QTableWidgetItem(maliyet_val)
            item_maliyet.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_maliyet.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row_idx, 5, item_maliyet)

            # İşlem Butonları (Düzenle / Sil)
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            btn_row_edit = QPushButton("✏️")
            btn_row_edit.setToolTip("Bakım Kaydını Düzenle")
            btn_row_edit.setFixedSize(30, 26)
            btn_row_edit.setObjectName("btnSecondary")
            m_id = m["id"]
            btn_row_edit.clicked.connect(lambda _, mid=m_id: self.edit_maintenance_by_id(mid))
            btn_layout.addWidget(btn_row_edit)

            btn_row_del = QPushButton("🗑️")
            btn_row_del.setToolTip("Bakım Kaydını Sil")
            btn_row_del.setFixedSize(30, 26)
            btn_row_del.setObjectName("btnDanger")
            btn_row_del.clicked.connect(lambda _, mid=m_id: self.delete_maintenance_by_id(mid))
            btn_layout.addWidget(btn_row_del)

            self.table.setCellWidget(row_idx, 6, btn_container)
            self.table.setRowHeight(row_idx, 38)

        self.history_title.setText(f"{norm_plaka} - Kronolojik Bakım Geçmişi")
        self.btn_add_maintenance.setEnabled(True)
        self.btn_edit_vehicle.setEnabled(True)
        self.btn_delete_vehicle.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_print.setEnabled(True)
        self.btn_pdf.setEnabled(True)

    def _clear_view(self):
        self.current_vehicle = None
        self.current_maintenances = []
        self.plate_badge.setText("ARAÇ SEÇİLMEDİ")
        self.vehicle_info_label.setText("Lütfen bir araç arayın veya yeni araç ekleyin.")
        self.lbl_stat_count.setText("Toplam Bakım: -")
        self.lbl_stat_km.setText("Son Kilometre: -")
        self.lbl_stat_date.setText("Son İşlem Tarihi: -")
        self.lbl_stat_total.setText("Toplam Harcama: -")
        self.lbl_grand_total.setText("Seçili Araç Genel Toplam: 0,00 ₺")
        self.table.setRowCount(0)
        self.history_title.setText("Kronolojik Bakım ve Onarım Geçmişi")
        self.lbl_records_count.setText("0 Kayıt")
        self.btn_add_maintenance.setEnabled(False)
        self.btn_edit_vehicle.setEnabled(False)
        self.btn_delete_vehicle.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_print.setEnabled(False)
        self.btn_pdf.setEnabled(False)

    # --- Diyalog ve Eylem Metotları ---

    def open_vehicle_list_dialog(self):
        """Kayıtlı tüm araçların listesini ve detaylı arama tablosunu açar."""
        dialog = VehicleListDialog(self.db, parent=self)
        if dialog.exec() == VehicleListDialog.DialogCode.Accepted:
            if dialog.selected_plate:
                self.refresh_all()
                self.search_input.setText(dialog.selected_plate)
                self.load_vehicle(dialog.selected_plate)

    def open_new_vehicle_dialog(self, initial_plate: str = ""):
        dialog = VehicleDialog(self.db, parent=self)
        if initial_plate:
            dialog.plaka_input.setText(initial_plate)
        if dialog.exec() == VehicleDialog.DialogCode.Accepted:
            new_plate = self.db.normalize_plate(dialog.plaka_input.text())
            self.refresh_all()
            self.search_input.setText(new_plate)
            self.load_vehicle(new_plate)
            QMessageBox.information(self, "Başarılı", f"'{new_plate}' plakalı araç başarıyla kaydedildi.")

    def open_edit_vehicle_dialog(self):
        if not self.current_vehicle:
            return
        dialog = VehicleDialog(self.db, vehicle=self.current_vehicle, parent=self)
        if dialog.exec() == VehicleDialog.DialogCode.Accepted:
            updated_plate = self.db.normalize_plate(dialog.plaka_input.text())
            self.refresh_all()
            self.search_input.setText(updated_plate)
            self.load_vehicle(updated_plate)
            QMessageBox.information(self, "Başarılı", "Araç bilgileri güncellendi.")

    def delete_current_vehicle(self):
        if not self.current_vehicle:
            return
        plaka = self.current_vehicle["plaka"]
        reply = QMessageBox.question(
            self, "Araç Silme Onayı",
            f"'{plaka}' plakalı aracı ve TÜM BAKIM GEÇMİŞİNİ silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_vehicle(plaka)
            self.current_vehicle = None
            self.refresh_all()
            QMessageBox.information(self, "Silindi", f"'{plaka}' plakalı araç sistemden silindi.")

    def open_add_maintenance_dialog(self):
        if not self.current_vehicle:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir araç seçiniz.")
            return

        plaka = self.current_vehicle["plaka"]
        dialog = MaintenanceDialog(self.db, plaka=plaka, parent=self)
        if dialog.exec() == MaintenanceDialog.DialogCode.Accepted:
            self.load_vehicle(plaka)
            QMessageBox.information(self, "Başarılı", "Yeni bakım kaydı eklendi.")

    def _on_table_row_double_click(self, row: int, col: int):
        id_item = self.table.item(row, 0)
        if id_item:
            self.edit_maintenance_by_id(int(id_item.text()))

    def edit_maintenance_by_id(self, maintenance_id: int):
        target = next((m for m in self.current_maintenances if m["id"] == maintenance_id), None)
        if not target or not self.current_vehicle:
            return

        dialog = MaintenanceDialog(
            self.db,
            plaka=self.current_vehicle["plaka"],
            maintenance=target,
            parent=self
        )
        if dialog.exec() == MaintenanceDialog.DialogCode.Accepted:
            self.load_vehicle(self.current_vehicle["plaka"])
            QMessageBox.information(self, "Başarılı", "Bakım kaydı güncellendi.")

    def delete_maintenance_by_id(self, maintenance_id: int):
        reply = QMessageBox.question(
            self, "Kayıt Sil",
            "Bu bakım kaydını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_maintenance(maintenance_id)
            if self.current_vehicle:
                self.load_vehicle(self.current_vehicle["plaka"])

    def preview_service_report(self):
        """Servis fişi / bakım dökümünü yazdırma önizlemesine gönderir."""
        if not self.current_vehicle:
            QMessageBox.warning(self, "Uyarı", "Önizlenecek araç seçilmedi.")
            return

        summary = self.db.get_vehicle_summary(self.current_vehicle["plaka"])
        PrintService.preview(self, self.current_vehicle, self.current_maintenances, summary)

    def print_service_report(self):
        """Servis fişini doğrudan Windows yazıcısına gönderir."""
        if not self.current_vehicle:
            QMessageBox.warning(self, "Uyarı", "Yazdırılacak araç seçilmedi.")
            return

        summary = self.db.get_vehicle_summary(self.current_vehicle["plaka"])
        PrintService.print_direct(self, self.current_vehicle, self.current_maintenances, summary)

    def export_pdf(self):
        """Bakım geçmişini PDF dosyası olarak dışa aktarır."""
        if not self.current_vehicle:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak araç seçilmedi.")
            return

        summary = self.db.get_vehicle_summary(self.current_vehicle["plaka"])
        PrintService.export_pdf(self, self.current_vehicle, self.current_maintenances, summary)

    # --- Veritabanı Yönetimi & Yedekleme Eylemleri ---

    def backup_database_action(self):
        """Veritabanını harici bir .db dosyası olarak yedekler."""
        default_name = f"servis_takip_yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Veritabanı Yedeğini Kaydet",
            default_name,
            "SQLite Veritabanı (*.db)"
        )
        if file_path:
            try:
                self.db.backup_database(file_path)
                QMessageBox.information(
                    self, "Yedekleme Başarılı",
                    f"Veritabanı yedeği güvenle oluşturuldu:\n\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Yedekleme Hatası", f"Yedek alınırken hata oluştu:\n{str(e)}")

    def restore_database_action(self):
        """Yedek .db dosyasından verileri doğrular ve geri yükler."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Geri Yüklenecek Veritabanı Dosyasını Seçin",
            "",
            "SQLite Veritabanı (*.db)"
        )
        if file_path:
            reply = QMessageBox.warning(
                self, "Geri Yükleme Onayı",
                "Seçilen yedek dosyasındaki veriler mevcut veritabanına aktarılacaktır.\n\n"
                "Devam etmek istediğinize emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db.restore_database(file_path)
                    self.refresh_all()
                    QMessageBox.information(
                        self, "Geri Yükleme Başarılı",
                        "Veritabanı başarıyla geri yüklendi ve tüm kayıtlar güncellendi."
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Geri Yükleme Hatası", f"Geri yükleme başarısız:\n{str(e)}")

    def open_db_folder_action(self):
        """Veritabanı dosyasının bulunduğu klasörü Windows Gezgini'nde açar."""
        try:
            self.db.open_db_directory()
        except Exception as e:
            QMessageBox.critical(self, "Klasör Hatası", f"Klasör açılamadı:\n{str(e)}")

    def show_db_info_action(self):
        """Aktif veritabanı dosyasının konumunu, boyutunu ve kayıt sayılarını gösterir."""
        info = self.db.get_db_info()
        msg = (
            f"<b>Veritabanı Motoru:</b> SQLite 3 (İlişkisel Veritabanı)<br/>"
            f"<b>Kalıcı Dosya Yolu:</b><br/><code>{info['path']}</code><br/><br/>"
            f"<b>Toplam Kayıtlı Araç:</b> {info['vehicle_count']} adet<br/>"
            f"<b>Toplam Bakım Kaydı:</b> {info['maintenance_count']} adet<br/>"
            f"<b>Dosya Boyutu:</b> {info['size_kb']:.2f} KB<br/>"
            f"<b>Son Güncelleme:</b> {info['last_modified']}<br/><br/>"
            f"<i>💡 Verileriniz bu dosyada güvenle saklanmaktadır. Programı yeniden açtığınızda, "
            f"güncellediğinizde veya bilgisayarı yeniden başlattığınızda tüm kayıtlarınız kalıcı olarak korunur.</i>"
        )
        QMessageBox.about(self, "Veritabanı Durumu & Bilgi", msg)
