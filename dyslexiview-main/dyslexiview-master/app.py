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
import nltk
from nltk.tokenize import word_tokenize
import re

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

def format_text_for_dyslexia(text):
    # Nettoyer le texte
    cleaned_text = text.strip()
    
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    # Définir les voyelles pour la séparation des syllabes
    vowels = 'aeiouyàâäéèêëîïôöùûüÿAEIOUYÀÂÄÉÈÊËÎÏÔÖÙÛÜŸ'
    
    # Séparer le texte en phrases
    sentences = nltk.sent_tokenize(cleaned_text)
    formatted_words = []
    
    for sentence in sentences:
        # Séparer en mots
        words = word_tokenize(sentence)
        
        for word in words:
            if word.isalnum() and len(word) > 3:
                # Diviser les mots longs en syllabes
                syllables = []
                i = 0
                current_syllable = ""
                
                while i < len(word):
                    current_syllable += word[i]
                    
                    # Règles de séparation des syllabes
                    if len(current_syllable) >= 2:
                        # Si on a une voyelle suivie d'une consonne
                        if (i < len(word) - 1 and 
                            word[i] in vowels and 
                            word[i+1] not in vowels):
                            syllables.append(current_syllable)
                            current_syllable = ""
                        # Si on a deux consonnes consécutives
                        elif (i < len(word) - 1 and 
                              word[i] not in vowels and 
                              word[i+1] not in vowels):
                            syllables.append(current_syllable)
                            current_syllable = ""
                    
                    i += 1
                
                if current_syllable:
                    syllables.append(current_syllable)
                
                # Si aucune syllabe n'a été trouvée, utiliser le mot entier
                if not syllables:
                    syllables = [word]
            else:
                # Garder les mots courts et la ponctuation intacts
                syllables = [word]
            
            formatted_words.append({
                'word': word,
                'syllables': syllables,
                'type': 'word' if word.isalnum() else 'punctuation',
                'syllable_colors': ['#0066CC', '#003366'] * (len(syllables) // 2 + 1)  # Alternance de bleus pour meilleur contraste
            })
    
    return {
        'original': text,
        'words': formatted_words,
        'formatting': {
            'font_family': 'OpenDyslexic',
            'letter_spacing': '0.25em',      # Augmentation de l'espacement des lettres
            'word_spacing': '0.5em',         # Ajout d'espacement entre les mots
            'line_height': '2.5',            # Augmentation de l'interligne
            'background_color': '#FFF8DC',   # Fond beige clair (moins agressif)
            'text_color': '#000000',         # Texte noir pour un meilleur contraste
            'text_align': 'left',
            'paragraph_spacing': '2em',      # Espacement entre les paragraphes
            'max_line_length': '60ch',       # Limitation de la longueur des lignes
            'font_size': '18px',            # Taille de police plus grande
            'font_weight': '500',           # Police légèrement plus grasse
            'margin': '2em',               # Marges pour éviter la surcharge visuelle
            'use_rulers': True,            # Utilisation de règles pour suivre les lignes
            'highlight_hover': True        # Surbrillance au survol pour aide à la lecture
        }
    }

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
                
                # Formater le texte pour les dyslexiques
                formatted_text = format_text_for_dyslexia(original_text)
            except Exception as ocr_error:
                return jsonify({'success': False, 'error': f'OCR failed: {str(ocr_error)}'})

            try:
                # Import gTTS here to avoid startup issues
                from gtts import gTTS
                
                # Generate audio file for original text
                tts = gTTS(original_text, lang='en')
                audio_filename = os.path.join(SRC_FOLDER, 'original.wav')
                tts.save(audio_filename)
            except Exception as audio_error:
                return jsonify({
                    'success': False, 
                    'error': f'Audio generation failed: {str(audio_error)}',
                    'original_text': original_text
                })

            return jsonify({
                'success': True,
                'original_text': original_text,
                'formatted_text': formatted_text,
                'original_sound': 'src/original.wav'
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Invalid file format'})

if __name__ == "__main__":
    app.run("localhost", 5000, debug=True)
