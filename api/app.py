from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

def ocr_captcha(img_con: bytes):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/209100101 Firefox/144.0',
            'Referer': 'https://decopy.ai/',
            'Origin': 'https://decopy.ai',
            'Product-Code': '0967003',
            'Product-Serial': '2a0d2fc3c7b0d1a118dd6713259968fb5',
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
