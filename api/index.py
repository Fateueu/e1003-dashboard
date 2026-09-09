from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
import requests
import io
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            WIDTH, HEIGHT = 1404, 1872
            image = Image.new("L", (WIDTH, HEIGHT), 255)
            draw = ImageDraw.Draw(image)

            # 使用安全內建字體 (避免任何檔案下載失敗)
            font = ImageFont.load_default()

            # --- 1. 天氣 API ---
            temp, humidity, wind, rain, feels = "25.1", "83.", "15.3", "0.1", "27.9"
            try:
                w_res = requests.get("https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc", timeout=3).json()
                if "temperature" in w_res and len(w_res["temperature"]["data"]) > 0:
                    temp = str(w_res["temperature"]["data"][0]["value"])
                if "humidity" in w_res and len(w_res["humidity"]["data"]) > 0:
                    humidity = str(w_res["humidity"]["data"][0]["value"]) + "."
            except Exception:
                pass

            # --- 2. 城巴 API ---
            def get_citybus_eta(stop_id, route):
                url = f"https://rt.data.gov.hk/v1/transport/citybus-nwfb/eta/CTB/{stop_id}/{route}"
                try:
                    res = requests.get(url, timeout=3).json()
                    eta_list = []
                    for item in res.get("data", []):
                        if item and item.get("eta"):
                            eta_list.append(item["eta"][11:16])
                        if len(eta_list) == 3: break
                    while len(eta_list) < 3: eta_list.append("N/A")
                    return eta_list
                except Exception:
                    return ["N/A", "N/A", "N/A"]

            # --- 3. 專线小巴 API ---
            def get_gmb_eta(stop_id):
                url = f"https://data.etagmb.gov.hk/eta/stop/{stop_id}"
                try:
                    res = requests.get(url, timeout=3).json()
                    eta_list = []
                    data_arr = res.get("data", [])
                    if data_arr and len(data_arr) > 0:
                        eta_array = data_arr[0].get("eta", [])
                        for item in eta_array:
                            if item and item.get("timestamp"):
                                eta_list.append(item["timestamp"][11:16])
                            if len(eta_list) == 3: break
                    while len(eta_list) < 3: eta_list.append("N/A")
                    return eta_list
                except Exception:
                    return ["N/A", "N/A", "N/A"]

            # ==================== 開始繪圖 ====================
            
            # 中間分隔線
            draw.line([(560, 0), (560, HEIGHT)], fill=0, width=4)

            # 【左上：日期與實時天氣】
            now = datetime.now()
            draw.text((30, 30), now.strftime("%d.%m.%Y"), fill=0, font=font)
            draw.text((420, 30), now.strftime("%a"), fill=0, font=font)

            draw.rectangle([(20, 120), (540, 850)], outline=0, width=3)
            draw.text((50, 150), f"Temp: {temp} C", fill=0, font=font)
            draw.text((50, 250), f"Humidity: {humidity}%", fill=0, font=font)
            draw.text((50, 350), f"Wind: {wind} km/h", fill=0, font=font)
            draw.text((50, 450), f"Rain: {rain} mm", fill=0, font=font)
            draw.text((50, 550), f"Feels like: {feels} C", fill=0, font=font)

            # 【左下：未來 3 天預報】
            draw.line([(20, 870), (540, 870)], fill=0, width=3)
            draw.text((50, 900), "Fri         Sat         Sun", fill=0, font=font)

            # 【右上：Bus 巴士】
            draw.text((600, 30), "Bus", fill=0, font=font)
            draw.line([(600, 70), (1380, 70)], fill=0, width=4)

            bus_routes = [
                ("81",  "002533"),
                ("11",  "002533"),
                ("25A", "002533"),
                ("26",  "002533"),
                ("63",  "002533"),
                ("108", "002533"),
                ("511", "002533")
            ]

            y = 100
            for route, stop_id in bus_routes:
                etas = get_citybus_eta(stop_id, route)
                draw.text((600, y), route, fill=0, font=font)
                draw.text((800, y), etas[0], fill=0, font=font)
                draw.text((1000, y), etas[1], fill=0, font=font)
                draw.text((1200, y), etas[2], fill=0, font=font)
                y += 110

            # 【右下：Minibus 小巴】
            y += 20
            draw.text((600, y), "Minibus", fill=0, font=font)
            draw.line([(600, y + 40), (1380, y + 40)], fill=0, width=4)
            y += 60

            minibus_stops = [
                ("21M", "20000125"),
                ("14M", "20003493")
            ]

            for route, stop_id in minibus_stops:
                etas = get_gmb_eta(stop_id)
                draw.text((600, y), route, fill=0, font=font)
                draw.text((800, y), etas[0], fill=0, font=font)
                draw.text((1000, y), etas[1], fill=0, font=font)
                draw.text((1200, y), etas[2], fill=0, font=font)
                y += 110

            # 輸出 PNG
            img_io = io.BytesIO()
            image.save(img_io, 'PNG')
            img_io.seek(0)

            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(img_io.getvalue())

        except Exception as e:
            # 防護機制：哪怕發生極端錯誤，也輸出錯誤圖片而非 500 頁面
            err_img = Image.new("L", (1404, 1872), 255)
            err_draw = ImageDraw.Draw(err_img)
            err_draw.text((100, 100), f"Error: {str(e)}", fill=0)
            img_io = io.BytesIO()
            err_img.save(img_io, 'PNG')
            img_io.seek(0)
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(img_io.getvalue())
