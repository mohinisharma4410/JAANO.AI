from flask import Flask, request, jsonify
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk
import pdfplumber
import os
from flask import Flask, request, jsonify, send_file
from pytube import YouTube
from moviepy import VideoFileClip, AudioFileClip
from gtts import gTTS
import speech_recognition as sr
from deep_translator import GoogleTranslator
from indic_transliteration import transliterate, sanscript
import speech_recognition as sr
nltk.download('punkt')
cloudinary.config(
    cloud_name='dtjcecoee',
    api_key='248441932477955',
    api_secret='oBIKnqn98nry6XfgL6gHUXDzeOk'
)

app = Flask(__name__)

@app.route('/docsummarize', methods=['POST'])
def doc_summarize():
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file uploaded."}), 400

    pdf_file = request.files['pdf']
    sentence_count = int(request.form.get('sentences_count', 30))
    lang_code = request.form.get('lang_code', 'en').strip().lower()

    # Language validation map
    supported_langs = {
        "english": "en", "hindi": "hi", "urdu": "ur", "gujarati": "gu", "marathi": "mr",
        "malayalam": "ml", "tamil": "ta", "telugu": "te", "kannada": "kn",
        "bengali": "bn", "assamese": "as", "oriya": "or", "punjabi": "pa", "bhojpuri": "hi"
    }

    if lang_code not in supported_langs.values():
        return jsonify({"error": f"Unsupported language code '{lang_code}'."}), 400

    # Save the PDF temporarily
    temp_path = 'temp_uploaded_file.pdf'
    pdf_file.save(temp_path)

    # Extract text from PDF
    try:
        with pdfplumber.open(temp_path) as pdf:
            text = ''.join(page.extract_text() or '' for page in pdf.pages)
    except Exception as e:
        return jsonify({"error": "Failed to read PDF.", "details": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Generate summary
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        summary_text = ' '.join(str(sentence) for sentence in summary)
    except Exception as e:
        return jsonify({"error": "Failed to generate summary.", "details": str(e)}), 500

    # Translate summary
    try:
        if lang_code == "en":
            translated_summary = summary_text
        else:
            translated_summary = GoogleTranslator(source='auto', target=lang_code).translate(summary_text)
    except Exception as e:
        return jsonify({"error": "Translation failed", "details": str(e)}), 500

    return jsonify({
        "summary": translated_summary,
        "language_code": lang_code
    })


@app.route('/youtube', methods=['POST'])
def youtube_transcribe_translate():
    data = request.get_json()
    video_url = data.get('url')
    lang = data.get('lang', 'hindi')

    if not video_url:
        return jsonify({'error': 'No YouTube URL provided'}), 400

    # Language mappings
    code = {
        "english": "en", "hindi": "hi", "urdu": "ur", "gujarati": "gu", "marathi": "mr",
        "malayalam": "ml", "tamil": "ta", "telugu": "te", "kannada": "kn",
        "bengali": "bn", "assamese": "as", "oriya": "or", "punjabi": "pa", "bhojpuri": "bho"
    }

    speech_code = {
        "english": "en", "hindi": "hi", "urdu": "ur", "gujarati": "gu", "marathi": "mr",
        "malayalam": "ml", "tamil": "ta", "telugu": "te", "kannada": "kn",
        "bengali": "bn", "assamese": "bn", "oriya": "bn", "bhojpuri": "hi", "punjabi": "hi"
    }

    if lang not in code:
        return jsonify({'error': 'Invalid language'}), 400

    try:
        # Setup paths
        save_dir = 'youtube_downloads'
        os.makedirs(save_dir, exist_ok=True)
        video_path = os.path.join(save_dir, 'video.mp4')
        audio_path = os.path.join(save_dir, 'audio.wav')
        tts_path = os.path.join(save_dir, f'{lang}.mp3')
        final_video_path = os.path.join(save_dir, f'final_output_{lang}.mp4')

        # 1. Download video
        yt = YouTube(video_url)
        stream = yt.streams.filter(file_extension='mp4', res="720p").first()
        stream.download(output_path=save_dir, filename='video.mp4')

        # 2. Extract original audio
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path)

        # 3. Speech to Text
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)

        # 4. Translate
        lang_code = code[lang]
        translated_text = GoogleTranslator(source='auto', target=lang_code).translate(text)

        # 5. TTS
        if lang == "punjabi":
            translated_text = transliterate(translated_text, sanscript.GURMUKHI, sanscript.DEVANAGARI)

        speech_lang = speech_code[lang]
        tts = gTTS(text=translated_text, lang=speech_lang)
        tts.save(tts_path)

        # 6. Replace audio in video
        tts_audio = AudioFileClip(tts_path).set_duration(clip.duration)
        final_clip = clip.set_audio(tts_audio)
        final_clip.write_videofile(final_video_path, codec='libx264', audio_codec='aac')

        # Clean up
        clip.close()
        final_clip.close()

        return send_file(final_video_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audiotoaudio', methods=['POST'])
def audio_to_audio():
    try:
        if 'audio' not in request.files or 'lang_code' not in request.form:
            return jsonify({'error': 'Audio file or language code missing'}), 400

        audio_file = request.files['audio']
        lang_code = request.form['lang_code'].lower()

        if audio_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        # Save uploaded audio
        upload_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Uploaded_Audio"
        os.makedirs(upload_folder, exist_ok=True)
        input_path = os.path.join(upload_folder, 'input.wav')
        audio_file.save(input_path)

        # Transcribe using SpeechRecognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(input_path) as source:
            audio_data = recognizer.record(source)

        try:
            extracted_text = recognizer.recognize_google(audio_data)
            print("Transcribed Text:", extracted_text)
        except sr.UnknownValueError:
            return jsonify({'error': 'Could not understand audio'}), 400
        except sr.RequestError as e:
            return jsonify({'error': f'Google API error: {str(e)}'}), 500

        # Language code validation
        valid_translation_codes = {
            "en", "hi", "ur", "gu", "mr", "ml", "ta", "te", "kn", "bn", "as", "or", "bho"
        }
        speech_code_map = {
            "en": "en", "hi": "hi", "ur": "ur", "gu": "gu", "mr": "mr", "ml": "ml",
            "ta": "ta", "te": "te", "kn": "kn", "bn": "bn", "as": "bn", "or": "bn", "bho": "hi"
        }

        if lang_code not in valid_translation_codes:
            return jsonify({'error': 'Unsupported language code'}), 400

        # Translate
        translated_text = extracted_text
        if lang_code != 'en':
            translated_text = GoogleTranslator(source='auto', target=lang_code).translate(extracted_text)

        # Generate audio
        speech_lang = speech_code_map[lang_code]
        output_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\All_Audio"
        os.makedirs(output_folder, exist_ok=True)
        output_audio_path = os.path.join(output_folder, f"translated_{lang_code}.mp3")

        tts = gTTS(text=translated_text, lang=speech_lang)
        tts.save(output_audio_path)

        return send_file(output_audio_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route("/generate_video_cloud", methods=["POST"])
def generate_video_cloud():
    data = request.json
    title = data.get("title")
    article = data.get("article")
    target_language = data.get("language")

    if not title or not article or not target_language:
        return jsonify({"error": "Missing required fields: title, article, language"}), 400

    lang_map = {
        "english": "en", "hindi": "hi", "urdu": "ur", "gujarati": "gu",
        "marathi": "mr", "tamil": "ta", "telugu": "te", "kannada": "kn",
        "bengali": "bn", "assamese": "as", "oriya": "or", "bhojpuri": "hi"
    }

    if target_language not in lang_map:
        return jsonify({"error": f"Language '{target_language}' not supported."}), 400

    def generate_summary(text):
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, 2)
        return " ".join(str(sentence) for sentence in summary)

    def upload_to_cloudinary(file_data, resource_type, public_id):
        result = cloudinary.uploader.upload(
            file_data,
            resource_type=resource_type,
            public_id=public_id,
            overwrite=True
        )
        return result["secure_url"]

    try:
        summary = generate_summary(article)
        translated_text = GoogleTranslator(source='auto', target=lang_map[target_language]).translate(summary)

        # Generate TTS
        tts = gTTS(text=translated_text, lang=lang_map[target_language])
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_url = upload_to_cloudinary(audio_buffer, "video", f"cloud_audio/{target_language}_{title}")

        # Generate images with translated text
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        lines = translated_text.split('.')[:3]
        img_urls = []
        for idx, line in enumerate(lines):
            img = Image.new("RGB", (1920, 1080), color="black")
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(font_path, 60)
            draw.text((100, 500), line.strip(), font=font, fill="white")
            img_io = BytesIO()
            img.save(img_io, format="PNG")
            img_io.seek(0)
            img_url = upload_to_cloudinary(img_io, "image", f"cloud_images/{target_language}_{title}_{idx}")
            img_urls.append(img_url)

        # Download audio locally
        temp_audio = f"{target_language}_temp.mp3"
        with open(temp_audio, "wb") as f:
            f.write(requests.get(audio_url).content)

        # Create video
        image_clips = [ImageClip(url).set_duration(3) for url in img_urls]
        final_clip = concatenate_videoclips(image_clips, method="compose").set_audio(AudioFileClip(temp_audio))
        output_path = f"{target_language}_{title}.mp4"
        final_clip.write_videofile(output_path, codec="libx264", fps=24, logger=None)

        # Upload video
        video_url = upload_to_cloudinary(output_path, "video", f"cloud_videos/{target_language}_{title}")
        os.remove(temp_audio)
        os.remove(output_path)

        return jsonify({
            "language": target_language,
            "video_url": video_url,
            "summary": summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
