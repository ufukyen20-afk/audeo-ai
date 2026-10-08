from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from enum import Enum
import yt_dlp
import os
import uuid
import shutil
import zipfile


class FormatSecenegi(str, Enum):
    mp4 = "mp4"
    mp3 = "mp3"
class VideoKalite(str, Enum):
    en_yuksek = "best"
    p2160 = "2160"
    p1440 = "1440"
    p1080 = "1080"
    p720 = "720"
    p480 = "480"
    p360 = "360"
class SesKalite(str, Enum):
    kbps_320 = "320"
    kbps_256 = "256"
    kbps_192 = "192"
    kbps_128 = "128"
# API Başlığı ve açıklamalarını Türkçe yapıyoruz
app = FastAPI(
    title="AuDeo AI - Yönetim Paneli",
    description="AuDeo AI medya indirme servisi kontrol ve test arayüzü.",
    version="1.0.0"
)
from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def anasayfa():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


def klasor_ve_dosya_sil(dosya_yolu: str, klasor_yolu: str = None):
    try:
        if os.path.exists(dosya_yolu):
            os.remove(dosya_yolu)
            print(f"[Temizlik] Dosya başarıyla silindi: {dosya_yolu}")
        if klasor_yolu and os.path.exists(klasor_yolu):
            shutil.rmtree(klasor_yolu)
            print(f"[Temizlik] Geçici klasör silindi: {klasor_yolu}")
    except Exception as e:
        print(f"[Temizlik Hatası] {e}")
# Winget ile yüklenen FFmpeg'in varsayılan konumu
ffmpeg_yolu = os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages")
def ffmpeg_bul():
    for root, dirs, files in os.walk(ffmpeg_yolu):
        if "ffmpeg.exe" in files:
            return root
    return None
@app.get("/", summary="Sunucu Durum Kontrolü", tags=["Genel"])
def ana_sayfa():
    """Sunucunun aktif ve çalışır durumda olduğunu doğrular."""
    return {"mesaj": "AuDeo AI Sistem Sunucusu Aktif!"}

@app.post("/download", summary="YouTube Videosu İndir", tags=["Video İşlemleri"])
def video_indir_api(
    url: str = Query(..., description="YouTube video adresi"),
    format_tipi: FormatSecenegi = Query(FormatSecenegi.mp4, description="Dosya formatı"),
    video_kalitesi: str = Query("2160p"),
):
    """
    Gönderilen YouTube bağlantısındaki videoyu en yüksek kalitede (Video + Ses) bilgisayara indirir.
    """
    if not url:
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir bağlantı adresi (URL) girin.")
    
        # Format ve Kalite Konfigürasyonu
        # Format ve Kalite Konfigürasyonu
    if format_tipi == FormatSecenegi.mp3:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredcodec': 'mp3',
    'preferredquality': '320',
}],
'outtmpl': '%(title)s_%(id)s.%(ext)s',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
            }
        }
    else:
        kalite_sayi = "".join(filter(str.isdigit, str(video_kalitesi)))
        if not kalite_sayi or video_kalitesi == "en_yuksek":
            format_str = 'bestvideo+bestaudio/best'
        else:
            format_str = f'bestvideo[height<={kalite_sayi}]+bestaudio/best'


        
        ydl_opts = {
            'format': format_str,
            'outtmpl': '%(title)s_%(height)sp_%(id)s.%(ext)s',
            'outtmpl_na_placeholder': '',
            'noplaylist': True,
            'overwrites': True,
            'cachedir': False,
            'rm_cachedir': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }

    ffmpeg_bin = ffmpeg_bul()
    if ffmpeg_bin:
        ydl_opts['ffmpeg_location'] = ffmpeg_bin
        ydl_opts['merge_output_format'] = 'mp4'  # Ayrı ses/videoyu mp4 olarak birleştirmeye zorla
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            hazirlanan_yol = ydl.prepare_filename(info)

            # MP3 isteği için uzantıyı zorla .mp3 yap
            if format_tipi == FormatSecenegi.mp3:
                dosya_yolu = os.path.splitext(hazirlanan_yol)[0] + ".mp3"
            else:
                # Gerçekten diske kaydedilen dosyayı (webm, mp4, mkv) kontrol edip bul
                kok_yol = os.path.splitext(hazirlanan_yol)[0]
                dosya_yolu = hazirlanan_yol
                for uzanti in ['.mp4', '.webm', '.mkv']:
                    if os.path.exists(kok_yol + uzanti):
                        dosya_yolu = kok_yol + uzanti
                        break
            return FileResponse(
                path=dosya_yolu, 
                filename=os.path.basename(dosya_yolu),
                media_type='application/octet-stream'
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İndirme hatası: {str(e)}")
@app.get("/info", summary="Video Bilgilerini Getir", tags=["Video İşlemleri"])
def video_bilgisi_al(url: str = Query(..., description="YouTube video adresi")):
    if not url:
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir bağlantı adresi girin.")
    ydl_opts = {
        'noplaylist': True,
            'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    }   
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False) 
            return {
            "baslik": info.get("title"),
            "kapak_resmi": info.get("thumbnail"),
            "sure_saniye": info.get("duration"),
            "kanal": info.get("uploader"),
            "max_height": info.get("height")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bilgiler alınamadı: {str(e)}")
@app.post("/download-playlist", summary="Playlist/Toplu İndirme (ZIP)", tags=["Video İşlemleri"])
def playlist_indir(
    url: str = Query(..., description="YouTube Playlist bağlantı adresi"),
    format_tipi: FormatSecenegi = Query(FormatSecenegi.mp3, description="Dosya formatı"),
    video_kalitesi: str = Query("2160p"),
    ses_kalitesi: SesKalite = Query(SesKalite.kbps_320, description="Ses kalitesi/bitrate (MP3 için)"),
    background_tasks: BackgroundTasks = None
):
    if not url:
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir bağlantı adresi girin.")
    # 1. Benzersiz geçici klasör ve ZIP dosyası ismi oluşturma
    oturum_id = str(uuid.uuid4())
    gecici_klasor = f"temp_{oturum_id}"
    os.makedirs(gecici_klasor, exist_ok=True)
    zip_dosya_adi = f"playlist_{oturum_id}.zip"
        # 2. yt-dlp ayarlarını yapılandırma (Max 10 video limiti)
    if format_tipi == FormatSecenegi.mp3:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{gecici_klasor}/%(title)s.%(ext)s',
            'playlistend': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': ses_kalitesi.value,
            }],
        }
    else:
        kalite_sayi = "".join(filter(str.isdigit, str(video_kalitesi)))
        if not kalite_sayi or video_kalitesi == "en_yuksek":
            format_str = 'bestvideo+bestaudio/best'
        else:
            format_str = f'bestvideo[height<={kalite_sayi}]+bestaudio/best'


        ydl_opts = {
            'format': format_str,
            'outtmpl': f'{gecici_klasor}/%(title)s.%(ext)s',
            'playlistend': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
            }
        }
    if ffmpeg_bul():
        ydl_opts['ffmpeg_location'] = ffmpeg_bul()
    try:
        # 3. İndirme işlemini başlatma
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        # 4. İndirilen dosyaları ZIP arşivine doldurma
        with zipfile.ZipFile(zip_dosya_adi, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(gecici_klasor):
                for file in files:
                    zipf.write(os.path.join(root, file), file)
        # 5. Arka plan temizleme görevini ekleme (ZIP ve geçici klasörü siler)
        if background_tasks:
            background_tasks.add_task(klasor_ve_dosya_sil, zip_dosya_adi, gecici_klasor)
        # 6. ZIP dosyasını kullanıcıya gönderme
        return FileResponse(
            path=zip_dosya_adi,
            filename="playlist.zip",
            media_type="application/zip"
        )
    except Exception as e:
        print("SİSTEM HATASI:", e)
        # Hata durumunda geçici klasörü temizle
        if os.path.exists(gecici_klasor):
            shutil.rmtree(gecici_klasor)
        raise HTTPException(status_code=500, detail=f"Playlist indirme hatası: {str(e)}")
@app.get("/info")
def video_bilgisi(url: str = Query(..., description="YouTube video URL'si")):
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            max_height = info.get('height') or 1080
            formats = info.get('formats', [])
            
            for f in formats:
                h = f.get('height')
                if h and h > max_height:
                    max_height = h

                    return {
            "baslik": info.get("title"),
            "kanal": info.get("uploader"),
            "kapak_resmi": info.get("thumbnail"),
            "sure_saniye": info.get("duration"),
            "max_height": max_height
        }


    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bilgi alınamadı: {str(e)}")


PROTECTED_LUTS = {
    "test": {
        "title": "Test LUT",
        "size": 2,
        "data": [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
            [1.0, 1.0, 1.0]
        ]
    }
}

@app.get("/api/lut/{lut_name}")
async def get_protected_lut(lut_name: str):
    if lut_name in PROTECTED_LUTS:
        return PROTECTED_LUTS[lut_name]
    return {"error": "LUT bulunamadı"}






