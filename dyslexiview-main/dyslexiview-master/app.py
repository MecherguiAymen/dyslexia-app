import json
from flask import Flask, request, jsonify, send_file
import os
import tempfile
from flask_cors import CORS
import shutil
import subprocess
from datetime import datetime
from pydub import AudioSegment
from pydub.effects import normalize

app = Flask(__name__)
CORS(app)

# Configure directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
TEMP_FOLDER = os.path.join(BASE_DIR, 'temp')
SRC_FOLDER = os.path.join(BASE_DIR, 'src')
RECORDINGS_FOLDER = os.path.join(SRC_FOLDER, 'recordings')

# Create necessary folders
for folder in [UPLOAD_FOLDER, TEMP_FOLDER, SRC_FOLDER, RECORDINGS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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

def enhance_audio(audio_path):
    try:
        # Load the audio file
        audio = AudioSegment.from_wav(audio_path)
        
        # Normalize audio (adjust volume to a standard level)
        audio = normalize(audio)
        
        # Increase volume slightly
        audio = audio + 5
        
        # Apply basic noise reduction by removing very quiet parts
        silence_threshold = -50  # dB
        audio = audio.strip_silence(silence_thresh=silence_threshold)
        
        # Save enhanced audio
        enhanced_path = audio_path.replace('.wav', '_enhanced.wav')
        audio.export(enhanced_path, format="wav")
        
        return enhanced_path
    except Exception as e:
        print(f"Error enhancing audio: {str(e)}")
        return audio_path

@app.route('/api/recordings', methods=['GET'])
def list_recordings():
    try:
        recordings = []
        for filename in os.listdir(RECORDINGS_FOLDER):
            if filename.endswith('.wav'):
                file_path = os.path.join(RECORDINGS_FOLDER, filename)
                recordings.append({
                    'id': filename.replace('.wav', ''),
                    'filename': filename,
                    'url': f'/api/recordings/{filename}',
                    'timestamp': os.path.getctime(file_path),
                    'enhanced': os.path.exists(file_path.replace('.wav', '_enhanced.wav'))
                })
        return jsonify(sorted(recordings, key=lambda x: x['timestamp'], reverse=True))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recordings/<filename>')
def serve_recording(filename):
    try:
        return send_file(
            os.path.join(RECORDINGS_FOLDER, filename),
            mimetype='audio/wav'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/recordings', methods=['POST'])
def save_recording():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        if not audio_file.filename:
            return jsonify({'error': 'No selected file'}), 400
            
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'recording_{timestamp}.wav'
        filepath = os.path.join(RECORDINGS_FOLDER, filename)
        
        # Save original recording
        audio_file.save(filepath)
        
        # Enhance audio
        enhanced_path = enhance_audio(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/api/recordings/{filename}',
            'enhanced_url': f'/api/recordings/{os.path.basename(enhanced_path)}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
