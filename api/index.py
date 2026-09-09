from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
import requests
import io
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. 建立 1404 x 1872 畫布 (E1003 原生解析度，純白底)
        WIDTH, HEIGHT = 1404, 1872
        image = Image.new("L", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(image)

        # 2. 載入字體 (預設)
        font_title = ImageFont.load_default()
        font_main = ImageFont.load_default()

        # 3. 抓取城巴 ETA 函數
        def get_bus_eta(stop_id, route):
            url = f"https://rt.data.gov.hk/v1/transport/citybus-nwfb/eta/CTB/{stop_id}/{route}"
            try:
                res = requests.get(url, timeout=4).json()
                eta_list = []
                for item in res.get("data", []):
                    if item.get("eta"):
                        # 直接擷取 HH:mm (第 11 到 16 個字元)
                        eta_time = item["eta"][11:16]
                        eta_list.append(eta_time)
                    if len(eta_list) == 3:
                        break
                while len(eta_list) < 3:
                    eta_list.append("N/A")
                return "   ".join(eta_list)
            except:
                return "N/A   N/A   N/A"

        # 4. 繪製標題與時間
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M")
        draw.text((80, 80), f"Last Update: {now_str}", fill=0, font=font_title)
        draw.line([(80, 140), (1324, 140)], fill=0, width=4)

        # 5. 繪製路線 (範例路線，可隨時修改)
        routes = [
            ("81",  "002533"),
            ("11",  "002533"),
            ("25A", "002533"),
            ("26",  "002533"),
            ("63",  "002533")
        ]

        y = 200
        for route, stop_id in routes:
            eta = get_bus_eta(stop_id, route)
            draw.text((100, y), f"{route:<6} {eta}", fill=0, font=font_main)
            y += 120

        # 6. 將圖片轉為 PNG 輸出
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(img_io.getvalue())
