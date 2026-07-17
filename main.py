import flet as ft
import numpy as np
import cv2

# --- Geoteknik Parametreler ---
REFERANS_CAP_MM = 26.15  # 1 TL Referans Çapı

def interpolasyon_bul(caplar, yuzdeler, hedef_yuzde):
    if hedef_yuzde < min(yuzdeler) or hedef_yuzde > max(yuzdeler):
        return None
    for i in range(len(yuzdeler) - 1):
        y1, y2 = yuzdeler[i], yuzdeler[i+1]
        x1, x2 = caplar[i], caplar[i+1]
        if (y1 >= hedef_yuzde >= y2) or (y1 <= hedef_yuzde <= y2):
            if x1 == 0 or x2 == 0:
                continue
            log_x = np.log10(x1) + (hedef_yuzde - y1) * (np.log10(x2) - np.log10(x1)) / (y2 - y1)
            return 10**log_x
    return None

def siniflandir_zemin_gelismis(caplar):
    if len(caplar) < 5:
        return "Yetersiz Veri", "Yetersiz Veri", "-", "-", ("-", "-", "-")
    total_adet = len(caplar)
    sirali_caplar = np.sort(caplar)[::-1]
    yuzde_gecen = [(1 - (i / total_adet)) * 100 for i in range(len(sirali_caplar))]
    
    d60 = interpolasyon_bul(sirali_caplar, yuzde_gecen, 60.0)
    d30 = interpolasyon_bul(sirali_caplar, yuzde_gecen, 30.0)
    d10 = interpolasyon_bul(sirali_caplar, yuzde_gecen, 10.0)
    
    cu_str, cc_str = "Hesaplanamadı", "Hesaplanamadı"
    cu, cc = None, None
    
    if d60 and d10 and d10 > 0:
        cu = d60 / d10
        cu_str = f"{cu:.2f}"
        if d30:
            cc = (d30**2) / (d60 * d10)
            cc_str = f"{cc:.2f}"

    cakil_orani = sum(1 for c in caplar if c > 4.75) / total_adet * 100
    kum_orani = sum(1 for c in caplar if 0.075 <= c <= 4.75) / total_adet * 100
    ince_orani = sum(1 for c in caplar if c < 0.075) / total_adet * 100
    
    if ince_orani >= 50:
        astm = "İnce Daneli Zemin"
    else:
        if cakil_orani > kum_orani:
            astm = "GW (İyi Çakıl)" if (cu and cc and cu >= 4 and 1 <= cc <= 3) else "GP (Kötü Çakıl)"
        else:
            astm = "SW (İyi Kum)" if (cu and cc and cu >= 6 and 1 <= cc <= 3) else "SP (Kötü Kum)"
                
    return astm, f"Cu: {cu_str} | Cc: {cc_str}", f"D10: {d10:.2f}mm" if d10 else "-", f"D30: {d30:.2f}mm" if d30 else "-", f"D60: {d60:.2f}mm" if d60 else "-"

def main(page: ft.Page):
    page.title = "Gelişmiş Zemin Analizi"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    lbl_info = ft.Text("Zemin Fotoğrafı Seçerek Analizi Başlatın", size=16, weight=ft.FontWeight.BOLD)
    lbl_resim_durum = ft.Text("", size=12, italic=True)
    txt_sonuc = ft.Text(value="", size=15, color=ft.Colors.BLUE_900, weight=ft.FontWeight.W_600)

    def dosya_secildi(e: ft.FilePickerResultEvent):
        if not e.files:
            lbl_resim_durum.value = "Seçim iptal edildi."
            page.update()
            return
            
        lbl_resim_durum.value = f"Fotoğraf işleniyor: {e.files[0].name}"
        page.update()
        
        try:
            with open(e.files[0].path, "rb") as f:
                dosya_bytes = f.read()
                
            nparr = np.frombuffer(dosya_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                lbl_resim_durum.value = "❌ Hata: Görsel okunamadı."
                page.update()
                return
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.medianBlur(gray, 5)
            
            circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 100, param1=50, param2=30, minRadius=30, maxRadius=150)
            pixel_to_mm = 0.15
            if circles is not None:
                circles = np.uint16(np.around(circles))
                r_pixel = circles[0, 0][2]
                pixel_to_mm = REFERANS_CAP_MM / (r_pixel * 2)
            
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            tane_boyutlari = []
            for c in contours:
                if cv2.contourArea(c) < 50:
                    continue
                if len(c) >= 5:
                    _, (d_kisa, _), _ = cv2.fitEllipse(c)
                    tane_boyutlari.append(d_kisa * pixel_to_mm)
            
            if len(tane_boyutlari) < 5:
                txt_sonuc.value = "❌ Fotoğrafta yeterli zemin tanesi tespit edilemedi!"
            else:
                astm, katsayilar, d10, d30, d60 = siniflandir_zemin_gelismis(tane_boyutlari)
                txt_sonuc.value = (
                    f"📊 ANALİZ SONUÇLARI:\n"
                    f"-----------------------------\n"
                    f"Tespit Edilen Tane: {len(tane_boyutlari)} adet\n"
                    f"{d10}\n{d30}\n{d60}\n"
                    f"{katsayilar}\n"
                    f"-----------------------------\n"
                    f"🏷️ Sınıflandırma: {astm}"
                )
            lbl_resim_durum.value = "Analiz Tamamlandı!"
        except Exception as ex:
            txt_sonuc.value = f"Sistemsel Hata: {str(ex)}"
            lbl_resim_durum.value = "❌ İşlem başarısız."
        page.update()

    file_picker = ft.FilePicker(on_result=dosya_secildi)
    page.overlay.append(file_picker)

    btn_sec = ft.ElevatedButton(
        "Zemin Fotoğrafı Yükle",
        icon=ft.Icons.PHOTO_CAMERA,
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("🔬 Mühendislik Zemin Analiz Laboratuvarı", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                ft.Divider(),
                lbl_info,
                btn_sec,
                lbl_resim_durum,
                ft.Divider(),
                txt_sonuc
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15
        )
    )

ft.app(target=main)
