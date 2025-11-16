from flask import Flask, request, jsonify
import requests
import base64
import random
import string
import json
import re
import os  # Untuk cleanup jika diperlukan, tapi tidak digunakan sekarang

def random_serial(length=32):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

# Daftar User-Agent untuk rotasi
ua_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
]
ua = random.choice(ua_list)

def ocr_decopy(img_con: bytes) -> str | None:
    """Mode Decopy: Menggunakan API Decopy AI untuk OCR."""
    try:
        headers = {
            'User-Agent': ua,
            'Referer': 'https://decopy.ai/',
            'Origin': 'https://decopy.ai',
            'Product-Code': '0967003',
            'Product-Serial': random_serial(),
        }
        files = {
            'upload_images': ('BotDetectCaptcha.jpg', img_con, 'image/jpeg'),
        }
        code_cp = requests.post(
            'https://api.decopy.ai/api/decopy/image-to-text/create-job',
            headers=headers,
            files=files,
            timeout=30
        )
        print(code_cp.json())  # Debug, ganti dengan logging di produksi
        data = code_cp.json()
        if 'result' in data and 'output' in data['result'] and data['result']['output']:
            return data['result']['output'][0]
        return None
    except Exception as e:
        print(f"Error in Decopy mode: {e}")  # Debug
        return None

def ocr_gpt(img_con: bytes) -> str | None:
    """Mode GPT: Menggunakan Supabase unified-prompt untuk OCR berbasis GPT.
    Sekarang menerima bytes langsung, bukan file_path."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': '*/*',
            'Accept-Language': 'id,en-US;q=0.7,en;q=0.3',
            'Referer': 'https://generateprompt.ai/',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhYnBmcXN2ZGtkanBqamtibm9rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzczNjk5MjEsImV4cCI6MjA1Mjk0NTkyMX0.wGGq1SWLIRELdrntLntBz-QH-JxoHUdz8Gq-0ha-4a4',
            'Origin': 'https://generateprompt.ai',
            'Connection': 'keep-alive',
        }
        json_data = {
            'feature': 'extract-text-from-img-en',
            'language': 'en',
            'image': f'data:image/jpeg;base64,{base64.b64encode(img_con).decode()}',
        }
        url = 'https://wabpfqsvdkdjpjjkbnok.supabase.co/functions/v1/unified-prompt'
        resp = requests.post(url, headers=headers, json=json_data, timeout=30)
        if not resp.ok:
            return None
        contents = []
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                try:
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        continue
                    data_json = json.loads(data_str)
                    delta = data_json.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        contents.append(delta["content"])
                except Exception:
                    pass
        full_text = ''.join(contents)
        full_text = re.sub(r'\s+', '', full_text)  # Hapus semua spasi
        return full_text or None
    except requests.exceptions.RequestException:
        return None
    except Exception as e:
        print(f"Error in GPT mode: {e}")  # Debug
        return None

def send_captcha_image(img_con: bytes, mode: str = 'gpt') -> str | None:
    """
    Fungsi unified untuk mengirim gambar captcha dengan mode pilihan.
    Sekarang menerima bytes langsung, bukan file_path.
    
    Args:
        img_con (bytes): Bytes gambar (JPEG/GIF).
        mode (str): 'decopy' untuk Decopy AI, 'gpt' untuk GPT-based OCR.
    
    Returns:
        str | None: Teks yang diekstrak atau None jika gagal.
    """
    try:
        # Validasi sederhana gambar
        if not img_con.startswith(b'\xff\xd8\xff') and not img_con.startswith(b'GIF8'):
            return None
        
        if mode.lower() == 'decopy':
            return ocr_decopy(img_con)
        elif mode.lower() == 'gpt':
            return ocr_gpt(img_con)
        else:
            raise ValueError("Mode harus 'decopy' atau 'gpt'")
    except Exception as e:
        print(f"Error in send_captcha_image: {e}")
        return None

# Contoh penggunaan di endpoint Flask (adaptasi dari kode sebelumnya)
app = Flask(__name__)

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
   
    data = request.get_json()
    if 'image_base64' not in data:
        return jsonify({'error': 'No image_base64 provided'}), 400
    if 'mode' not in data:
        data['mode'] = 'gpt'  # Default mode
    
    try:
        # Decode base64 string to bytes
        img_bytes = base64.b64decode(data['image_base64'])
       
        # Langsung gunakan bytes tanpa simpan file temp
        result = send_captcha_image(img_bytes, data['mode'])
       
        if result:
            return jsonify({'result': result, 'mode': data['mode']})
        else:
            return jsonify({'error': 'OCR processing failed'}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to decode base64 or process image'}), 400

if __name__ == '__main__':
    app.run(debug=True)
