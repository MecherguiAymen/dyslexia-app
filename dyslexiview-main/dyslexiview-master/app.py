import json
from flask import Flask, request, jsonify
import os
import tempfile
from flask_cors import CORS
import shutil
import subprocess

app = Flask(__name__)
CORS(app)

# Configure directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
TEMP_FOLDER = os.path.join(BASE_DIR, 'temp')
SRC_FOLDER = os.path.join(BASE_DIR, 'src')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

# Ensure all required directories exist
for folder in [UPLOAD_FOLDER, TEMP_FOLDER, SRC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def run_tesseract(image_path):
    # Créer un fichier temporaire pour la sortie
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', dir=TEMP_FOLDER) as tmp:
        output_path = tmp.name
    
    try:
        # Exécuter Tesseract directement
        tesseract_cmd = [
            r"C:\Users\ay.mechergui\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",  # Chemin correct après installation
            image_path,
            output_path.replace('.txt', '')  # Tesseract ajoute automatiquement .txt
        ]
        
        process = subprocess.run(
            tesseract_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Lire le résultat
        with open(output_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        return text.strip()
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"Tesseract error: {e.stderr}")
    finally:
        # Nettoyer les fichiers temporaires
        if os.path.exists(output_path):
            os.remove(output_path)

@app.route('/', methods=['POST', 'GET'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'})

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected image'})

    if file:
        try:
            # Save the uploaded file
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            try:
                # Process image with OCR using our custom function
                original_text = run_tesseract(filename)
                if not original_text:
                    original_text = "No text detected in the image"
            except Exception as ocr_error:
                return jsonify({'success': False, 'error': f'OCR failed: {str(ocr_error)}'})

            try:
                # Import gTTS here to avoid startup issues
                from gtts import gTTS
                
                # Generate audio files
                tts = gTTS(original_text, lang='en')
                audio_filename1 = os.path.join(SRC_FOLDER, '1.wav')
                audio_filename2 = os.path.join(SRC_FOLDER, '2.wav')
                
                tts.save(audio_filename1)
                tts.save(audio_filename2)
            except Exception as audio_error:
                return jsonify({
                    'success': False, 
                    'error': f'Audio generation failed: {str(audio_error)}',
                    'original_text': original_text
                })

            return jsonify({
                'success': True,
                'original_text': original_text,
                'summarized_text': original_text,  # For now, same as original
                'summary_sound': 'src/1.wav',
                'original_sound': 'src/2.wav'
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Invalid file format'})

if __name__ == "__main__":
    app.run("localhost", 5000, debug=True)
