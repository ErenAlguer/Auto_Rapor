"""
Araç Servis Takip Otomasyonu - Diyalog Pencereleri
Yeni araç ekleme/düzenleme ve bakım kaydı ekleme/düzenleme formlarını içerir.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QTextEdit, QComboBox, QPushButton,
    QLabel, QMessageBox, QDateEdit, QCompleter, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame
)

from database import DatabaseManager


class VehicleDialog(QDialog):
    """Yeni araç ekleme veya mevcut araç bilgilerini düzenleme diyaloğu."""

    def __init__(self, db: DatabaseManager, vehicle: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.vehicle = vehicle
        self.is_edit_mode = vehicle is not None

        self.setWindowTitle("Araç Bilgilerini Düzenle" if self.is_edit_mode else "Yeni Araç Kaydı")
        self.setMinimumWidth(440)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        header_label = QLabel("Araç ve Müşteri Bilgileri")
        header_label.setStyleSheet("font-size: 15pt; font-weight: bold; color: #0284c7; margin-bottom: 5px;")
        layout.addWidget(header_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        # Plaka alanı
        self.plaka_input = QLineEdit()
        self.plaka_input.setPlaceholderText("Örn: 34 ABC 123")
        self.plaka_input.textChanged.connect(self._format_plate)

        # Marka & Model
        self.marka_input = QLineEdit()
        self.marka_input.setPlaceholderText("Örn: Volkswagen")

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Örn: Golf 1.6 TDI Highline")

        # Model Yılı
        self.yil_input = QSpinBox()
        self.yil_input.setRange(1950, datetime.now().year + 1)
        self.yil_input.setValue(2018)

        # Sahip & Telefon
        self.sahip_input = QLineEdit()
        self.sahip_input.setPlaceholderText("Ad ve Soyad")

        self.telefon_input = QLineEdit()
        self.telefon_input.setPlaceholderText("05XX XXX XX XX")

        # Notlar
        self.notlar_input = QTextEdit()
        self.notlar_input.setPlaceholderText("Araçla ilgili ek detaylar, şasi no, usta notları...")
        self.notlar_input.setMaximumHeight(80)

        form.addRow("Plaka *:", self.plaka_input)
        form.addRow("Marka *:", self.marka_input)
        form.addRow("Model *:", self.model_input)
        form.addRow("Model Yılı:", self.yil_input)
        form.addRow("Müşteri Ad Soyad:", self.sahip_input)
        form.addRow("Telefon:", self.telefon_input)
        form.addRow("Özel Notlar:", self.notlar_input)

        layout.addLayout(form)

        # Butonlar
        button_box = QHBoxLayout()
        button_box.addStretch()

        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.clicked.connect(self.reject)
        button_box.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Kaydet")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                padding: 6px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_save.clicked.connect(self.save)
        button_box.addWidget(self.btn_save)

        layout.addLayout(button_box)

        # Düzenleme modunda alanları doldur
        if self.is_edit_mode and self.vehicle:
            self.plaka_input.setText(self.vehicle.get("plaka", ""))
            self.marka_input.setText(self.vehicle.get("marka", ""))
            self.model_input.setText(self.vehicle.get("model", ""))
            yil_val = self.vehicle.get("yil")
            if yil_val:
                self.yil_input.setValue(int(yil_val))
            self.sahip_input.setText(self.vehicle.get("sahip_ad_soyad", ""))
            self.telefon_input.setText(self.vehicle.get("telefon", ""))
            self.notlar_input.setPlainText(self.vehicle.get("notlar", ""))

    def _format_plate(self, text: str):
        """Plakayı otomatik büyük harfe dönüştürür."""
        pos = self.plaka_input.cursorPosition()
        upper_text = self.db.normalize_plate(text)
        if upper_text != text:
            self.plaka_input.blockSignals(True)
            self.plaka_input.setText(upper_text)
            self.plaka_input.setCursorPosition(min(pos, len(upper_text)))
            self.plaka_input.blockSignals(False)

    def save(self):
        plaka = self.db.normalize_plate(self.plaka_input.text())
        marka = self.marka_input.text().strip()
        model = self.model_input.text().strip()
        yil = self.yil_input.value()
        sahip = self.sahip_input.text().strip()
        telefon = self.telefon_input.text().strip()
        notlar = self.notlar_input.toPlainText().strip()

        if not plaka:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen araç plakasını giriniz.")
            self.plaka_input.setFocus()
            return

        if not marka or not model:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen marka ve model bilgilerini giriniz.")
            self.marka_input.setFocus()
            return

        try:
            if self.is_edit_mode:
                old_plaka = self.vehicle["plaka"]
                self.db.update_vehicle(old_plaka, plaka, marka, model, yil, sahip, telefon, notlar)
            else:
                existing = self.db.get_vehicle(plaka)
                if existing:
                    QMessageBox.warning(
                        self, "Kayıt Mevcut",
                        f"'{plaka}' plakalı araç zaten sistemde kayıtlı!"
                    )
                    return
                self.db.add_vehicle(plaka, marka, model, yil, sahip, telefon, notlar)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"Kayıt işlemi başarısız:\n{str(e)}")


class MaintenanceDialog(QDialog):
    """
    Yeni bakım kaydı ekleme veya düzenleme diyaloğu.
    Yapılan işlem alanı hem elle serbest yazılabilir hem de açılır listeden seçilebilir.
    """

    def __init__(self, db: DatabaseManager, plaka: str,
                 maintenance: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.plaka = self.db.normalize_plate(plaka)
        self.maintenance = maintenance
        self.is_edit_mode = maintenance is not None

        self.setWindowTitle("Bakım Kaydını Düzenle" if self.is_edit_mode else f"Yeni Bakım Kaydı - {self.plaka}")
        self.setMinimumWidth(480)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        header_label = QLabel(f"Bakım İşlem Bilgisi ({self.plaka})")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #0284c7; margin-bottom: 5px;")
        layout.addWidget(header_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        # Tarih
        self.tarih_input = QDateEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDisplayFormat("dd.MM.yyyy")
        self.tarih_input.setDate(QDate.currentDate())

        # Kilometre
        self.km_input = QSpinBox()
        self.km_input.setRange(0, 2000000)
        self.km_input.setSingleStep(1000)
        self.km_input.setSuffix(" km")
        self.km_input.setGroupSeparatorShown(True)

        # Son kilometre bilgisini öneri olarak getir
        summary = self.db.get_vehicle_summary(self.plaka)
        last_km = summary.get("son_km", 0)
        self.km_input.setValue(last_km if last_km > 0 else 50000)

        # Yapılan İşlem (Editable ComboBox - Hem seçilebilir hem elle yazılabilir!)
        self.islem_combo = QComboBox()
        self.islem_combo.setEditable(True)
        self.islem_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.islem_combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.islem_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        # İşlem seçeneklerini yükle
        operations = self.db.get_distinct_operations()
        self.islem_combo.addItem("")  # Boş seçenek
        for op in operations:
            self.islem_combo.addItem(op)

        self.islem_combo.lineEdit().setPlaceholderText("İşlem seçin veya elle yazın (örn: Sağ ön disk değişimi)...")

        # Maliyet / Tutar
        self.maliyet_input = QDoubleSpinBox()
        self.maliyet_input.setRange(0.0, 1000000.0)
        self.maliyet_input.setDecimals(2)
        self.maliyet_input.setSingleStep(100.0)
        self.maliyet_input.setSuffix(" ₺")
        self.maliyet_input.setGroupSeparatorShown(True)
        self.maliyet_input.setValue(0.0)

        # Açıklama / Usta Notu
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setPlaceholderText("Kullanılan parça markası, garanti süresi, özel servis açıklaması...")
        self.aciklama_input.setMaximumHeight(85)

        form.addRow("Bakım Tarihi *:", self.tarih_input)
        form.addRow("Araç Kilometresi *:", self.km_input)
        form.addRow("Yapılan İşlem *:", self.islem_combo)
        form.addRow("İşlem Ücreti (₺):", self.maliyet_input)
        form.addRow("Açıklama / Parça Notu:", self.aciklama_input)

        layout.addLayout(form)

        # Bilgilendirme Notu
        info_label = QLabel("💡 Yapılan işlemi açılır listeden seçebilir veya dilediğiniz işlemi doğrudan klavyeyle yazabilirsiniz.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #64748b; font-size: 9.5pt; font-style: italic;")
        layout.addWidget(info_label)

        # Butonlar
        button_box = QHBoxLayout()
        button_box.addStretch()

        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.clicked.connect(self.reject)
        button_box.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Kaydet")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                padding: 6px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_save.clicked.connect(self.save)
        button_box.addWidget(self.btn_save)

        layout.addLayout(button_box)

        # Düzenleme modunda alanları doldur
        if self.is_edit_mode and self.maintenance:
            try:
                date_obj = datetime.strptime(self.maintenance.get("tarih", ""), "%Y-%m-%d").date()
                self.tarih_input.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            except Exception:
                pass

            self.km_input.setValue(int(self.maintenance.get("kilometre", 0)))
            self.islem_combo.setEditText(self.maintenance.get("islem", ""))
            self.maliyet_input.setValue(float(self.maintenance.get("maliyet", 0.0)))
            self.aciklama_input.setPlainText(self.maintenance.get("aciklama", ""))

    def save(self):
        tarih = self.tarih_input.date().toString("yyyy-MM-dd")
        km = self.km_input.value()
        islem = self.islem_combo.currentText().strip()
        maliyet = self.maliyet_input.value()
        aciklama = self.aciklama_input.toPlainText().strip()

        if not islem:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen yapılan işlemi seçiniz veya elle yazınız.")
            self.islem_combo.setFocus()
            return

        try:
            if self.is_edit_mode:
                m_id = self.maintenance["id"]
                self.db.update_maintenance(m_id, tarih, km, islem, maliyet, aciklama)
            else:
                self.db.add_maintenance(self.plaka, tarih, km, islem, maliyet, aciklama)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Bakım kaydı kaydedilemedi:\n{str(e)}")


class VehicleListDialog(QDialog):
    """
    Kayıtlı tüm araçları arama çubuğu ve detaylı istatistik tablosu ile
    listeleyen diyalog penceresi.
    Kullanıcı anlık arama yapabilir, bir araca çift tıklayarak veya 'Seç' butonuna basarak
    ana ekrana yükleyebilir.
    """

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_plate: Optional[str] = None
        self.vehicles_data: List[Dict[str, Any]] = []

        self.setWindowTitle("Kayıtlı Araç Listesi & Detaylı Arama")
        self.resize(1050, 620)
        self.setMinimumSize(850, 480)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Üst Arama Çubuğu
        search_frame = QFrame()
        search_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px;")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 6, 8, 6)
        search_layout.setSpacing(10)

        lbl_search = QLabel("🔍 Arama:")
        lbl_search.setStyleSheet("font-weight: bold; color: #0284c7; font-size: 11pt;")
        search_layout.addWidget(lbl_search)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Plaka, Araç Sahibi, Marka, Model veya Telefon numarası ile anında arayın...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.load_data)
        search_layout.addWidget(self.search_input)

        self.btn_new_vehicle = QPushButton("➕ Yeni Araç Ekle")
        self.btn_new_vehicle.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
        """)
        self.btn_new_vehicle.clicked.connect(self._open_new_vehicle)
        search_layout.addWidget(self.btn_new_vehicle)

        layout.addWidget(search_frame)

        # Araç Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Plaka", "Marka", "Model", "Model Yılı", "Araç Sahibi",
            "Telefon", "Bakım Adedi", "Son KM", "Son Bakım Tarihi", "Toplam Harcama (₺)"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

        # Alt Bilgi ve Butonlar
        bottom_layout = QHBoxLayout()
        self.lbl_count = QLabel("Toplam: 0 araç listeleniyor")
        self.lbl_count.setStyleSheet("font-weight: 600; color: #475569;")
        bottom_layout.addWidget(self.lbl_count)

        bottom_layout.addStretch()

        self.btn_edit = QPushButton("✏️ Düzenle")
        self.btn_edit.clicked.connect(self._edit_selected)
        bottom_layout.addWidget(self.btn_edit)

        self.btn_select = QPushButton("🔎 Seç ve Bakım Geçmişini Aç")
        self.btn_select.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                padding: 7px 18px;
                border-radius: 4px;
                font-size: 10.5pt;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_select.clicked.connect(self._select_and_open)
        bottom_layout.addWidget(self.btn_select)

        self.btn_close = QPushButton("Kapat")
        self.btn_close.clicked.connect(self.reject)
        bottom_layout.addWidget(self.btn_close)

        layout.addLayout(bottom_layout)

    def load_data(self):
        query = self.search_input.text().strip()
        self.vehicles_data = self.db.get_all_vehicles_with_stats(query)
        self.table.setRowCount(len(self.vehicles_data))
        self.lbl_count.setText(f"Toplam {len(self.vehicles_data)} araç bulundu (Filtre: '{query}')" if query else f"Toplam {len(self.vehicles_data)} araç kayıtlı")

        for row_idx, v in enumerate(self.vehicles_data):
            # Plaka
            item_plaka = QTableWidgetItem(v.get("plaka", ""))
            item_plaka.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_plaka.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, item_plaka)

            # Marka
            self.table.setItem(row_idx, 1, QTableWidgetItem(v.get("marka", "")))

            # Model
            self.table.setItem(row_idx, 2, QTableWidgetItem(v.get("model", "")))

            # Yıl
            yil_val = str(v.get("yil") or "-")
            item_yil = QTableWidgetItem(yil_val)
            item_yil.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, item_yil)

            # Müşteri
            self.table.setItem(row_idx, 4, QTableWidgetItem(v.get("sahip_ad_soyad", "")))

            # Telefon
            item_tel = QTableWidgetItem(v.get("telefon", ""))
            item_tel.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 5, item_tel)

            # Bakım Sayısı
            item_count = QTableWidgetItem(f"{v.get('toplam_bakim', 0)} adet")
            item_count.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 6, item_count)

            # Son KM
            son_km = v.get("son_km", 0)
            km_str = f"{son_km:,} km".replace(",", ".") if son_km > 0 else "-"
            item_km = QTableWidgetItem(km_str)
            item_km.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 7, item_km)

            # Son Bakım Tarihi
            son_tarih = v.get("son_tarih", "-")
            if son_tarih and son_tarih != "-":
                try:
                    son_tarih = datetime.strptime(son_tarih, "%Y-%m-%d").strftime("%d.%m.%Y")
                except Exception:
                    pass
            item_tarih = QTableWidgetItem(son_tarih)
            item_tarih.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 8, item_tarih)

            # Toplam Harcama
            toplam_harcama = v.get("toplam_harcama", 0.0)
            harcama_str = f"{toplam_harcama:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
            item_harcama = QTableWidgetItem(harcama_str)
            item_harcama.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_harcama.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row_idx, 9, item_harcama)

            self.table.setRowHeight(row_idx, 34)

    def _get_current_selected_plate(self) -> Optional[str]:
        row = self.table.currentRow()
        if 0 <= row < len(self.vehicles_data):
            return self.vehicles_data[row].get("plaka")
        return None

    def _on_row_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.vehicles_data):
            self.selected_plate = self.vehicles_data[row].get("plaka")
            self.accept()

    def _select_and_open(self):
        plate = self._get_current_selected_plate()
        if not plate:
            QMessageBox.information(self, "Seçim Yapılmadı", "Lütfen açmak istediğiniz aracı tablodan seçiniz.")
            return
        self.selected_plate = plate
        self.accept()

    def _open_new_vehicle(self):
        diag = VehicleDialog(self.db, parent=self)
        if diag.exec() == VehicleDialog.DialogCode.Accepted:
            new_plate = self.db.normalize_plate(diag.plaka_input.text())
            self.load_data()
            self.selected_plate = new_plate
            self.accept()

    def _edit_selected(self):
        plate = self._get_current_selected_plate()
        if not plate:
            QMessageBox.information(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz aracı seçiniz.")
            return

        veh = self.db.get_vehicle(plate)
        if veh:
            diag = VehicleDialog(self.db, vehicle=veh, parent=self)
            if diag.exec() == VehicleDialog.DialogCode.Accepted:
                self.load_data()
