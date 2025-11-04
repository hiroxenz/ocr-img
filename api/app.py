from flask import Flask, request, jsonify
import requests
import base64
import random
import string


def random_serial(length=32):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

app = Flask(__name__)
ua = random.choice([
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
])
def ocr_captcha(img_con: bytes):
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
            files=files
        )
        print (code_cp.json())
        return code_cp.json()['result']['output'][0]
    except Exception as e:
        return None

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    if 'image_base64' not in data:
        return jsonify({'error': 'No image_base64 provided'}), 400
    
    try:
        # Decode base64 string to bytes
        img_bytes = base64.b64decode(data['image_base64'])
        
        # Verify it's an image-like bytes (optional, but good practice)
        if not img_bytes.startswith(b'\xff\xd8\xff') and not img_bytes.startswith(b'GIF8'):  # JPEG or GIF start bytes
            return jsonify({'error': 'Invalid image data'}), 400
        
        result = ocr_captcha(img_bytes)
        
        if result:
            return jsonify({'result': result})
        else:
            return jsonify({'error': 'OCR processing failed'}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to decode base64 or process image'}), 400

# For Vercel WSGI compatibility
if __name__ == '__main__':
    app.run(debug=True)
