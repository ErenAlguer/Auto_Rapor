"""
Araç Servis Takip Otomasyonu - Yazdırma ve PDF Servisi
Bakım geçmişini temiz bir kurumsal servis şablonuyla yazıcıya gönderir veya PDF formatında kaydeder.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import QSizeF
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
from PyQt6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog


def generate_service_html(vehicle: Dict[str, Any], maintenances: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    """Araç bakım geçmişi için kurumsal ve modern bir HTML şablonu üretir."""
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    plaka = vehicle.get("plaka", "-")
    marka = vehicle.get("marka", "-")
    model = vehicle.get("model", "-")
    yil = vehicle.get("yil") or "-"
    sahip = vehicle.get("sahip_ad_soyad", "-")
    telefon = vehicle.get("telefon", "-")
    notlar = vehicle.get("notlar", "")
    
    toplam_bakim = summary.get("toplam_bakim", len(maintenances))
    toplam_harcama = summary.get("toplam_harcama", sum(m.get("maliyet", 0.0) for m in maintenances))
    son_km = summary.get("son_km", "-")

    # Bakım satırları
    rows_html = ""
    if not maintenances:
        rows_html = """
        <tr>
            <td colspan="5" style="text-align:center; padding: 18px; color: #777;">
                Kayıtlı bakım geçmişi bulunmamaktadır.
            </td>
        </tr>
        """
    else:
        for idx, m in enumerate(maintenances, start=1):
            tarih_raw = m.get("tarih", "")
            try:
                # YYYY-MM-DD -> DD.MM.YYYY
                tarih_fmt = datetime.strptime(tarih_raw, "%Y-%m-%d").strftime("%d.%m.%Y")
            except Exception:
                tarih_fmt = tarih_raw

            km_val = f"{m.get('kilometre', 0):,} km".replace(",", ".")
            islem_val = m.get("islem", "-")
            aciklama_val = m.get("aciklama", "").replace("\n", "<br/>") or "-"
            maliyet_val = f"{m.get('maliyet', 0.0):,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")

            bg_color = "#f9fbfd" if idx % 2 == 0 else "#ffffff"
            rows_html += f"""
            <tr style="background-color: {bg_color};">
                <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11pt; text-align: center;">{tarih_fmt}</td>
                <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11pt; text-align: right; font-weight: bold;">{km_val}</td>
                <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11pt; font-weight: 600; color: #1e293b;">{islem_val}</td>
                <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 10pt; color: #475569;">{aciklama_val}</td>
                <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11pt; text-align: right; font-weight: bold; color: #0f172a;">{maliyet_val}</td>
            </tr>
            """

    toplam_harcama_fmt = f"{toplam_harcama:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")

    notlar_section = ""
    if notlar.strip():
        notlar_section = f"""
        <div style="margin-top: 15px; padding: 10px 14px; background: #fefce8; border-left: 4px solid #eab308; font-size: 10pt; color: #713f12;">
            <strong>Araç / Müşteri Notu:</strong> {notlar}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
        color: #1e293b;
        margin: 20px;
        line-height: 1.4;
    }}
    .header {{
        border-bottom: 3px solid #0284c7;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }}
    .title {{
        font-size: 20pt;
        font-weight: 800;
        color: #0369a1;
        letter-spacing: -0.5px;
    }}
    .subtitle {{
        font-size: 10pt;
        color: #64748b;
    }}
    .meta-box {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
    }}
    .meta-box td {{
        padding: 8px 14px;
        font-size: 10.5pt;
    }}
    .label {{
        font-weight: bold;
        color: #475569;
        width: 18%;
    }}
    .val {{
        color: #0f172a;
        width: 32%;
    }}
    .data-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }}
    .data-table th {{
        background-color: #0284c7;
        color: #ffffff;
        font-size: 10.5pt;
        font-weight: 700;
        padding: 9px;
        text-align: left;
        border: 1px solid #0284c7;
    }}
    .summary-box {{
        margin-top: 18px;
        width: 100%;
        border-collapse: collapse;
    }}
    .summary-box td {{
        padding: 6px 12px;
        font-size: 11pt;
    }}
    .footer-signatures {{
        margin-top: 45px;
        width: 100%;
        border-collapse: collapse;
    }}
    .signature-cell {{
        width: 48%;
        text-align: center;
        border-top: 1px dashed #94a3b8;
        padding-top: 10px;
        font-size: 10.5pt;
        color: #475569;
    }}
</style>
</head>
<body>

<div class="header">
    <table style="width: 100%;">
        <tr>
            <td>
                <div class="title">ARAÇ SERVİS VE BAKIM RAPORU</div>
                <div class="subtitle">Oto Servis Takip ve Periyodik Bakım Sistemi</div>
            </td>
            <td style="text-align: right; vertical-align: bottom;">
                <div style="font-size: 10pt; color: #64748b;">Rapor Tarihi: <strong>{now_str}</strong></div>
            </td>
        </tr>
    </table>
</div>

<table class="meta-box">
    <tr>
        <td class="label">Plaka:</td>
        <td class="val"><strong style="font-size: 13pt; color: #0284c7;">{plaka}</strong></td>
        <td class="label">Araç Sahibi:</td>
        <td class="val"><strong>{sahip}</strong></td>
    </tr>
    <tr>
        <td class="label">Marka / Model:</td>
        <td class="val">{marka} {model}</td>
        <td class="label">Telefon:</td>
        <td class="val">{telefon}</td>
    </tr>
    <tr>
        <td class="label">Model Yılı:</td>
        <td class="val">{yil}</td>
        <td class="label">Güncel KM:</td>
        <td class="val">{f"{son_km:,} km".replace(",", ".") if isinstance(son_km, (int, float)) and son_km > 0 else son_km}</td>
    </tr>
</table>

{notlar_section}

<h3 style="color: #0f172a; margin-top: 20px; margin-bottom: 8px; font-size: 12pt;">
    Bakım ve Onarım Geçmişi (Toplam: {len(maintenances)} İşlem)
</h3>

<table class="data-table">
    <thead>
        <tr>
            <th style="width: 14%; text-align: center;">Tarih</th>
            <th style="width: 14%; text-align: right;">Kilometre</th>
            <th style="width: 32%;">Yapılan İşlem</th>
            <th style="width: 25%;">Açıklama / Parça Notu</th>
            <th style="width: 15%; text-align: right;">Tutar (₺)</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>

<table class="summary-box">
    <tr>
        <td style="width: 60%;"></td>
        <td style="width: 22%; text-align: right; font-size: 11pt; font-weight: bold; color: #334155; padding-top: 15px;">Genel Toplam:</td>
        <td style="width: 18%; text-align: right; font-size: 13pt; font-weight: 800; color: #0284c7; border-bottom: 2px solid #0284c7; padding-top: 15px;">
            {toplam_harcama_fmt}
        </td>
    </tr>
</table>

<table class="footer-signatures">
    <tr>
        <td class="signature-cell">
            <strong>Servis Yetkilisi / Usta</strong><br/>
            İmza & Kaşe
        </td>
        <td style="width: 4%;"></td>
        <td class="signature-cell">
            <strong>Araç Sahibi / Teslim Alan</strong><br/>
            {sahip}
        </td>
    </tr>
</table>

<div style="margin-top: 35px; text-align: center; font-size: 8.5pt; color: #94a3b8;">
    Bu döküm Oto Servis Takip Otomasyonu tarafından oluşturulmuştur.
</div>

</body>
</html>
"""
    return html


class PrintService:
    """Belgeleri yazıcıya aktarma, önizleme ve PDF oluşturma yöneticisi."""

    @staticmethod
    def _create_document(html_content: str, printer: Optional[QPrinter] = None) -> QTextDocument:
        """HTML içeriğini A4 sayfa boyutlarına uygun bir QTextDocument nesnesine çevirir."""
        doc = QTextDocument()
        if printer:
            # Yazıcının yazdırılabilir alan boyutunu piksel/nokta bazında uygula
            page_rect = printer.pageRect(QPrinter.Unit.Point)
            doc.setPageSize(QSizeF(page_rect.width(), page_rect.height()))
        doc.setHtml(html_content)
        return doc

    @classmethod
    def preview(cls, parent: QWidget, vehicle: Dict[str, Any], maintenances: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Yazdırma önizleme penceresini açar (kullanıcı önizleme ekranından doğrudan yazdırabilir)."""
        if not vehicle:
            QMessageBox.warning(parent, "Uyarı", "Yazdırılacak araç bilgisi bulunamadı.")
            return

        try:
            html_content = generate_service_html(vehicle, maintenances, summary)
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

            preview_dialog = QPrintPreviewDialog(printer, parent)
            preview_dialog.setWindowTitle(f"Servis Raporu Önizleme - {vehicle.get('plaka', '')}")
            preview_dialog.resize(950, 800)

            def paint_requested(p: QPrinter):
                doc = cls._create_document(html_content, p)
                doc.print(p)

            preview_dialog.paintRequested.connect(paint_requested)
            preview_dialog.exec()
        except Exception as e:
            QMessageBox.critical(parent, "Önizleme Hatası", f"Önizleme hazırlanırken hata oluştu:\n{str(e)}")

    @classmethod
    def print_direct(cls, parent: QWidget, vehicle: Dict[str, Any], maintenances: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Windows yazıcı seçim diyaloğunu açar ve belgeyi doğrudan seçilen yazıcıya gönderir."""
        if not vehicle:
            QMessageBox.warning(parent, "Uyarı", "Yazdırılacak araç bilgisi bulunamadı.")
            return

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

            dialog = QPrintDialog(printer, parent)
            dialog.setWindowTitle(f"Yazdır - {vehicle.get('plaka', '')}")
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                html_content = generate_service_html(vehicle, maintenances, summary)
                doc = cls._create_document(html_content, printer)
                doc.print(printer)
                QMessageBox.information(parent, "Başarılı", "Servis formu başarıyla yazıcıya gönderildi.")
        except Exception as e:
            QMessageBox.critical(parent, "Yazdırma Hatası", f"Yazıcıya gönderilirken bir hata oluştu:\n{str(e)}")

    @classmethod
    def export_pdf(cls, parent: QWidget, vehicle: Dict[str, Any], maintenances: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Servis raporunu seçilen konuma PDF dosyası olarak kaydeder."""
        if not vehicle:
            QMessageBox.warning(parent, "Uyarı", "Dışa aktarılacak araç bilgisi bulunamadı.")
            return

        plaka = vehicle.get("plaka", "arac").replace(" ", "_")
        default_filename = f"Servis_Raporu_{plaka}_{datetime.now().strftime('%Y%m%d')}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "PDF Olarak Kaydet",
            default_filename,
            "PDF Dosyaları (*.pdf)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

            html_content = generate_service_html(vehicle, maintenances, summary)
            doc = cls._create_document(html_content, printer)
            doc.print(printer)

            reply = QMessageBox.information(
                parent,
                "PDF Başarıyla Oluşturuldu",
                f"Servis raporu başarıyla kaydedildi:\n\n{file_path}\n\nOluşturulan PDF dosyasını şimdi açmak ister misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(file_path)

        except Exception as e:
            QMessageBox.critical(parent, "PDF Hatası", f"PDF oluşturulurken bir hata oluştu:\n{str(e)}")
