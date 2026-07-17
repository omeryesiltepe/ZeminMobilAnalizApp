import flet as ft
import requests
import base64

# Analizleri yapacak olan ücretsiz bulut sunucu adresi
API_URL = "https://zemin-analiz-api.adreseklenecek.com/analiz" 

def main(page: ft.Page):
    page.title = "Mühendislik Zemin Analiz Laboratuvarı"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    
    lbl_info = ft.Text("Zemin fotoğrafı çekerek veya yükleyerek tam analizi başlatın.", size=14, italic=True)
    lbl_durum = ft.Text("", size=13, weight=ft.FontWeight.W_500)
    
    # Sonuçların ve Logaritmik Grafiğin Gösterileceği Alanlar
    img_grafik = ft.Image(visible=False, width=350, height=250, fit=ft.ImageFit.CONTAIN)
    txt_sonuc = ft.Text(value="", size=15, color=ft.Colors.BLUE_900, weight=ft.FontWeight.BOLD)

    def dosya_secildi(e: ft.FilePickerResultEvent):
        if not e.files:
            lbl_durum.value = "Seçim iptal edildi."
            page.update()
            return
            
        lbl_durum.value = "Fotoğraf bulut laboratuvarına gönderiliyor, lütfen bekleyin..."
        lbl_durum.color = ft.Colors.ORANGE_800
        img_grafik.visible = False
        txt_sonuc.value = ""
        page.update()
        
        try:
            # Fotoğrafı oku ve sunucuya göndermek için hazırla
            with open(e.files[0].path, "rb") as f:
                img_bytes = f.read()
            
            # Sunucuya güvenli istek atma
            files = {'file': (e.files[0].name, img_bytes, 'image/jpeg')}
            response = requests.post(API_URL, files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Değerleri ekrana yazdır
                txt_sonuc.value = (
                    f"📊 GEOTEKNİK ANALİZ SONUÇLARI:\n"
                    f"-----------------------------------------\n"
                    f"Tespit Edilen Tane Sayısı: {data.get('tane_adedi')} adet\n"
                    f"D10 Çapı: {data.get('d10')} mm\n"
                    f"D30 Çapı: {data.get('d30')} mm\n"
                    f"D60 Çapı: {data.get('d60')} mm\n"
                    f"Uniformluk Katsayısı (Cu): {data.get('cu')}\n"
                    f"Süreklilik Katsayısı (Cc): {data.get('cc')}\n"
                    f"-----------------------------------------\n"
                    f"🏷️ USCS (ASTM) Sınıfı: {data.get('zemin_sinifi')}"
                )
                
                # Gelen logaritmik grafiği ekranda göster
                grafik_base64 = data.get('grafik_base64')
                if grafik_base64:
                    img_grafik.src_base64 = grafik_base64
                    img_grafik.visible = True
                
                lbl_durum.value = "✅ Analiz başarıyla tamamlandı!"
                lbl_durum.color = ft.Colors.GREEN_700
            else:
                lbl_durum.value = "❌ Sunucu hatası! Lütfen daha net bir fotoğraf deneyin."
                lbl_durum.color = ft.Colors.RED
                
        except Exception as ex:
            lbl_durum.value = f"Bağlantı Hatası: Analiz sunucusuna erişilemedi."
            lbl_durum.color = ft.Colors.RED
        page.update()

    file_picker = ft.FilePicker(on_result=dosya_secildi)
    page.overlay.append(file_picker)

    btn_foto = ft.ElevatedButton(
        "Kamera / Fotoğraf Yükle",
        icon=ft.Icons.CAMERA_ALT,
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700),
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("🔬 Mobil Zemin Mekaniği Laboratuvarı", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                ft.Divider(),
                lbl_info,
                btn_foto,
                lbl_durum,
                ft.Divider(),
                img_grafik,
                txt_sonuc
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15
        )
    )

ft.app(target=main)
