from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import os
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        WIDTH, HEIGHT = 1404, 1872
        image = Image.new("L", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(image)

        # 下載高清粗體字體 (確保 E1003 上極之清晰)
        font_url = "https://github.com/google/fonts/raw/main/ofl/dejavusans/DejaVuSans-Bold.ttf"
        font_path = "/tmp/font_bold.ttf"
        if not os.path.exists(font_path):
            try:
                r = requests.get(font_url, timeout=5)
                with open(font_path, "wb") as f:
                    f.write(r.content)
            except:
                pass

        try:
            font_title = ImageFont.truetype(font_path, 70)
            font_big = ImageFont.truetype(font_path, 80)
            font_time = ImageFont.truetype(font_path, 65)
            font_small = ImageFont.truetype(font_path, 40)
        except:
            font_title = font_big = font_time = font_small = ImageFont.load_default()

        # --- 1. 天氣 API ---
        temp, humidity, wind, rain, feels = "25.1", "83.", "15.3", "0.1", "27.9"
        try:
            w_res = requests.get("https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc", timeout=3).json()
            if "temperature" in w_res:
                temp = str(w_res["temperature"]["data"][0]["value"])
            if "humidity" in w_res:
                humidity = str(w_res["humidity"]["data"][0]["value"]) + "."
        except:
            pass

        # --- 2. 城巴 API ---
        def get_citybus_eta(stop_id, route):
            url = f"https://rt.data.gov.hk/v1/transport/citybus-nwfb/eta/CTB/{stop_id}/{route}"
            try:
                res = requests.get(url, timeout=3).json()
                eta_list = []
                for item in res.get("data", []):
                    if item.get("eta"):
                        eta_list.append(item["eta"][11:16])
                    if len(eta_list) == 3: break
                while len(eta_list) < 3: eta_list.append("N/A")
                return eta_list
            except:
                return ["N/A", "N/A", "N/A"]

        # --- 3. 專線小巴 API (依據你截圖的正確 URL) ---
        def get_gmb_eta(stop_id):
            url = f"https://data.etagmb.gov.hk/eta/stop/{stop_id}"
            try:
                res = requests.get(url, timeout=3).json()
                eta_list = []
                # 提取 data[0].eta 陣列
                eta_array = res.get("data", [])[0].get("eta", [])
                for item in eta_array:
                    if item.get("timestamp"):
                        eta_list.append(item["timestamp"][11:16])
                    if len(eta_list) == 3: break
                while len(eta_list) < 3: eta_list.append("N/A")
                return eta_list
            except:
                return ["N/A", "N/A", "N/A"]

        # ==================== 開始繪圖 (100% 復刻排版) ====================
        
        # 中間分隔線
        draw.line([(560, 0), (560, HEIGHT)], fill=0, width=4)

        # 【左上：日期與實時天氣】
        now = datetime.now()
        draw.text((30, 30), now.strftime("%d.%m.%Y"), fill=0, font=font_title)
        draw.text((420, 30), now.strftime("%a"), fill=0, font=font_title)

        draw.rectangle([(20, 120), (540, 850)], outline=0, width=3)
        draw.text((50, 150), temp, fill=0, font=ImageFont.truetype(font_path, 130) if os.path.exists(font_path) else font_big)
        draw.text((50, 400), f"{humidity}", fill=0, font=font_big)
        draw.text((220, 400), f"{wind}", fill=0, font=font_big)
        draw.text((410, 400), f"{rain}", fill=0, font=font_big)
        draw.text((50, 470), "Humidity (%)  Wind Speed (km/h) Rain (mm)", fill=0, font=font_small)
        draw.text((100, 580), f"Feels like (°C)  {feels}", fill=0, font=font_big)

        # 【左下：未來 3 天預報】
        draw.line([(20, 870), (540, 870)], fill=0, width=3)
        draw.text((50, 900), "Fri         Sat         Sun", fill=0, font=font_big)

        # 【右上：Bus 巴士】
        draw.text((600, 30), "Bus 🚌", fill=0, font=font_title)
        draw.line([(600, 110), (1380, 110)], fill=0, width=5)

        bus_routes = [
            ("81",  "002533"),
            ("11",  "002533"),
            ("25A", "002533"),
            ("26",  "002533"),
            ("63",  "002533"),
            ("108", "002533"),
            ("511", "002533")
        ]

        y = 130
        for route, stop_id in bus_routes:
            etas = get_citybus_eta(stop_id, route)
            draw.text((600, y), route, fill=0, font=font_big)
            draw.text((820, y), etas[0], fill=0, font=font_time)
            draw.text((1020, y), etas[1], fill=0, font=font_time)
            draw.text((1220, y), etas[2], fill=0, font=font_time)
            y += 120

        # 【右下：Minibus 小巴】
        y += 20
        draw.text((600, y), "Minibus 🚐", fill=0, font=font_title)
        draw.line([(600, y + 90), (1380, y + 90)], fill=0, width=5)
        y += 110

        minibus_stops = [
            ("21M", "20000125"),
            ("14M", "20003493")
        ]

        for route, stop_id in minibus_stops:
            etas = get_gmb_eta(stop_id)
            draw.text((600, y), route, fill=0, font=font_big)
            draw.text((820, y), etas[0], fill=0, font=font_time)
            draw.text((1020, y), etas[1], fill=0, font=font_time)
            draw.text((1220, y), etas[2], fill=0, font=font_time)
            y += 120

        # 輸出 PNG
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(img_io.getvalue())
