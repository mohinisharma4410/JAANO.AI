from flask import Flask, render_template, request, send_file, send_from_directory, jsonify,redirect,url_for
import os
import openai
import string
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
import nltk
import shutil
nltk.download('punkt')
import requests
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlparse, parse_qs

from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import transliterate
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
from deep_translator import GoogleTranslator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
base_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Text_Images"
resized_image_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Resized_images"
all_audio_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\All_Audio"
image_folder = os.path.join(app.root_path, resized_image_folder)
deleted_folder = os.path.join(app.root_path, 'static/deleted_images')
manually_added_images = set()
UPLOAD_FOLDER = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Resized_images"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Define the upload folder and allowed extensions for file uploads
UPLOAD_FOLDER1 = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER1'] = UPLOAD_FOLDER1

# Store recent links
recent_links = []

def delete_all_folders(folder_path):
    try:
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
                print(f"Folder '{os.path.join(root, dir)}' has been deleted.")
        
        print("All folders within the specified directory have been deleted.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_summary(text, sentences_count=2):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    summary_text = " ".join(str(sentence) for sentence in summary)
    return summary_text
def regenerate_data():
    video = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Videos"
    delete_all_folders(video)
    language_folders = [folder for folder in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, folder))]

    def process_language_folder(lang_folder):
        text_image_folder = os.path.join(base_folder, lang_folder)
        images_text = [img for img in os.listdir(text_image_folder) if img.endswith(".jpg") or img.endswith(".jpeg") or img.endswith(".png")]
        images_resized = [img for img in os.listdir(UPLOAD_FOLDER) if img.endswith(".jpg") or img.endswith(".jpeg") or img.endswith(".png")]

        images_text.sort()
        images_resized.sort()

        if not images_text or not images_resized:
            print(f"No image files found in '{lang_folder}' folder.")
        else:
            audio_path = os.path.join(all_audio_folder, f"{lang_folder}.mp3")

            if not os.path.exists(audio_path):
                print(f"No audio file found for '{lang_folder}'.")
                return

            audio_duration = AudioFileClip(audio_path).duration

            image_durations_text = [audio_duration / 8] * len(images_text)
            image_durations_resized = [audio_duration / 10] * len(images_resized)

            image_clips = []
            start_time = 0

            for i in range(max(len(images_text), len(images_resized))):
                if i < len(images_text):
                    image_path = os.path.join(text_image_folder, images_text[i])
                    image_duration = min(image_durations_text[i], audio_duration - start_time)
                    img_clip = ImageClip(image_path, duration=image_duration)
                    image_clips.append(img_clip.set_duration(image_duration))
                    start_time += image_duration

                if i < len(images_resized):
                    image_path = os.path.join(resized_image_folder, images_resized[i])
                    image_duration = min(image_durations_resized[i], audio_duration - start_time)
                    img_clip = ImageClip(image_path, duration=image_duration)
                    image_clips.append(img_clip.set_duration(image_duration))
                    start_time += image_duration

            final_clip = concatenate_videoclips(image_clips, method="compose")
            audio = AudioFileClip(audio_path)
            final_clip = final_clip.set_audio(audio)

            output_video_path = fr"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Videos\{lang_folder}.mp4"
            final_clip.write_videofile(output_video_path, codec='libx264', fps=24)
            print(f"Video '{lang_folder}.mp4' has been generated.")

    # Utilize ThreadPoolExecutor to concurrently process each language folder
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
        executor.map(process_language_folder, language_folders)
        
    response_data = {'success': True}
    return jsonify(response_data)
    
# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    message = request.args.get('message')
    return render_template('index.html', recent_links=recent_links, message=message)

global title
title = ""
global article
article = ""
global images

@app.route('/submit', methods=['POST'])
def submit():
    global title
    global article
    global images
    title = request.form['title']
    article = request.form['article']
    images = request.files.getlist('image')
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(title)
    image_data_list = []
    filenames=[]

    for image in images:
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER1'], filename)
            image.save(filepath)
            filenames.append(filename)

            with open(filepath, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                image_data_list.append(image_data)

    print(f"Title: {title}")
    print(f"Article: {article}")
    print(f"Date: {date}")
    print(f"Image filenames: {filenames}")

    # Generate a new link for the submitted article
    link = url_for('recent', title=title, article=article, date=date, image=filenames, _external=True)
    recent_links.append(link)

    return redirect(url_for('home', message='Article submitted successfully!'))
@app.route('/image.html')
def image_page():
    images = os.listdir(image_folder)
    deleted_images = os.listdir(deleted_folder)
    return render_template('image.html', images=images, deleted_images=deleted_images)
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        resize_image(filepath)
        return jsonify({'success': True, 'image_name': filename})
    return jsonify({'success': False, 'message': 'File type not allowed'})

# Utility function to resize images
def resize_image(image_path, size=(1920, 1080)):
    with Image.open(image_path) as img:
        img = img.resize(size, Image.ANTIALIAS)
        img.save(image_path)

@app.route('/move_to_deleted', methods=['POST'])
def move_to_deleted():
    image_name = request.json.get('image_name')
    if image_name:
        source_path = os.path.join(image_folder, image_name)
        destination_path = os.path.join(deleted_folder, image_name)
        shutil.move(source_path, destination_path)
        return jsonify({'success': True})
    return jsonify({'success': False}), 400
@app.route('/regenerate', methods=['POST'])
def regenerate_images():
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    for image in images:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image)
        resize_image(image_path)
    regenerate_data()
    return jsonify({'success': True})



@app.route('/recent')
def recent():
    title = request.args.get('title')
    article = request.args.get('article')
    image = request.args.getlist('image')
    date = request.args.get('date')
    return render_template('recent.html', title=title, article=article, image=image, date=date)

@app.route('/generate_video', methods=['POST'])
def generate_video():
    base_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Text_Images"
    resized_image_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Resized_images"
    all_audio_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\All_Audio"
    video = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Videos"
    delete_all_folders(base_folder)
    delete_all_folders(all_audio_folder)
    delete_all_folders(video)
    delete_all_folders(resized_image_folder)
    # Function to extract paragraphs from a URL
    global title
    global article
    global images
   
    # urlipt = bg
    # paras=extract_paragraphs(urlipt)

    content =article
    Title_query= title
        # Function to download an image from a URL
   
    #print(Title_query)
   # print(content)
    #content = " ".join(posted_content_dict[1])
    #Title_query= title
    # Replace 'your-api-key' with your actual OpenAI API key
    # api_key = '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'

    # Text to be summarizedfl
    input_text = content
    # Create a prompt for summarization
    # prompt = f"Summarize the following text:\n{input_text}\nSummary:"

    # Initialize the OpenAI API client
    # openai.api_key = api_key

    # Specify the GPT-3 model (you can use a model like 'text-davinci-003')
    # model = 'text-davinci-003'
    # # Generate the summary using GPT-3
    # response = openai.Completion.create(
    #     engine=model,
    #     prompt=prompt,
    #     max_tokens=350  # Adjust the token limit as needed for the desired summary length
    # )
    summary=generate_summary(input_text)

    # Extract the generated summary from the response
    # summary = response.choices[0].text.strip()
    Total = Title_query + summary
    # Print the summary
    #print("Generated Summary:")
    #print(summary)
    
    #response_data = {'message': 'Video generated successfully'}
    #return jsonify(response_data)
    code = {
        "english": "en",
        "hindi": "hi",
        "urdu": "ur",
        "gujarati": "gu",
        "marathi": "mr",
        "malayalam": "ml",
        "tamil": "ta",
        "telugu": "te",
        "kannada": "kn",
        "bengali": "bn",
        "assamese": "as",
        "oriya": "or",
        # "punjabi": "pa",
        "bhojpuri": "bho"
    }

    # Store translations for each language in a dictionary
    translate_all = {}
    for lang, lang_code in code.items():
        if lang_code == "en":  # Skip translating to the same language (in this case, English)
            translate_all[lang] = summary
        translation = GoogleTranslator(source='auto', target=lang_code).translate(summary)
        translate_all[lang] = translation
        print(translate_all)
        speech_code = {
        "english": "en",
        "hindi": "hi",
        "urdu": "ur",
        "gujarati": "gu",
        "marathi": "mr",
        "malayalam": "ml",
        "tamil": "ta",
        "telugu": "te",
        "kannada": "kn",
        "bengali": "bn",
        "assamese": "bn",
        "oriya": "bn",
        "bhojpuri": "hi",
        # "punjabi": "hi"
    }
    output_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\All_Audio"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for lang, text in translate_all.items():
        if lang not in speech_code:
            continue
        # if lang == "punjabi":
        #     hindi_text = transliterate(text, sanscript.GURMUKHI, sanscript.DEVANAGARI)
        #     text = hindi_text
            # print("text me ayya "+ text)
            # tts = gTTS(text=text, lang = speech_tgt)
            # audio_file = os.path.join(output_folder, f"{lang}.mp3")  # You may consider a different filename
            # tts.save(audio_file)
        speech_tgt = speech_code[lang]
        tts = gTTS(text=text, lang = speech_tgt)
        audio_file = os.path.join(output_folder, f"{lang}.mp3")
        print("Audio files generated and stored in the 'all_audio' folder.")

        tts.save(audio_file)

        print("Audio files generated and stored in the 'all_audio' folder.")



    print("Audio files generated and stored in the 'all_audio' folder.")
    def search_google_images(query, api_key, cx, num_images=10):
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "searchType": "image",
            "num": num_images,
        }

        try:
            response = requests.get(base_url, params=params)
            response_data = response.json()

            if "items" in response_data:
                image_urls = [item["link"] for item in response_data["items"]]
                return image_urls

        except Exception as e:
            print(f"An error occurred: {e}")

        return []

    # Usage
    api_key = "AIzaSyAUubLfv1Y9_Lz_J4yRLvIj5E26bNOtjwQ"  # Replace with your Google API key
    cx = "270926dac31a34eea" # Replace with your Custom Search Engine ID
    search_query = Title_query  # Replace with your desired search query
    num_images = 10  # Number of images to retrieve
    image_urls = search_google_images(search_query, api_key, cx, num_images)
    d=[]
    if image_urls:
        for i, url in enumerate(image_urls, start=1):
            print(f"Image {i}: {url}")
            d.append(url)
    print(d)
    def filter_urls(url_list):
        valid_urls = [url for url in url_list if url.lower().endswith('.jpg')]
        return valid_urls
    filtered_urls = filter_urls(d)
    print(filtered_urls)
        
   # Function to download an image from a URL
    def download_image(url, save_path):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                    print(f"Downloaded: {save_path}")
                    print("hori hai")
            else:
                print(f"Failed to download: {url}")
                print("nhi ho pai image")
        except Exception as e:
            print(f"Error: {e}")
    # List of image URLs (replace these with your own URLs)
     # List of image URLs (replace these with your own URLs)
    image_urls = filtered_urls # Add your URLs here
    # Directory where you want to save the downloaded images
    save_directory = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Resized_images"

    # Create the save directory if it doesn't exist
    #os.makedirs(save_directory, exist_ok=True)

    # Utilize ThreadPoolExecutor to download multiple images concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
        for idx, url in enumerate(image_urls, start=1):
            image_extension = url.split('.')[-1]  # Get the file extension
            save_path = os.path.join(save_directory, f"image_{idx}.{image_extension}")
            executor.submit(download_image, url, save_path)
    



    # Source directory containing the images to resize
    # Source directory containing the images to resize
   # Source directory containing the images to resize
    source_directory = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Resized_images"
    print("aya aya")
    # Desired size for the resized images (width, height)
    # Desired size for the resized images (width, height)
    new_size = (1920, 1080)  # Replace with your desired dimensions

    # List of image file extensions (add more if needed)
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]

    # Function to resize and save an image
    def resize_image(source_file):
        with Image.open(source_file) as image:
            resized_image = image.resize(new_size)
            resized_image.save(source_file)
            print(f"Resized and saved {os.path.basename(source_file)} in the same folder")

    # Create the save directory if it doesn't exist
    #os.makedirs(source_directory, exist_ok=True)

    # Utilize ThreadPoolExecutor to concurrently resize and save images
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
        for filename in os.listdir(source_directory):
            source_file = os.path.join(source_directory, filename)
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                executor.submit(resize_image, source_file)

    print("Image resizing and replacement complete.")
    language = {
        "bengali": "Vrinda", "gujarati": "Shruti", "tamil": "Latha", "telugu": "Pothana",
        "kannada": "Tunga", "malayalam": "Kartika", "assamese": "Nirmala UI", "oriya": "Kalinga",
        "marathi": "Mangal", "urdu": "Dubai", "hindi": "Mangal", "bhojpuri": "Mangal", "english": "English"
    }
    dot = ["english", "gujarati", "tamil" , "telugu", "kannada", "malayalam" , "marathi"]
    line = ["hindi" , "bengali" , "assamese", "oriya", "bhojpuri"]

    font_path = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\New_all_lang.ttf"
    output_directory = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Text_Images"  # Output directory for storing language-wise images

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for lang, summary in translate_all.items():
        if lang in language:
            font_lang = language[lang]
            font = ImageFont.truetype(font_path, size=70)
            #if lang in dot:
            #   lines_div = summary.split('.')
            #f lang in line:
            #  lines_div = summary.split('।')
            if lang == "urdu":
                lines_div = summary.split("۔")
            else :    
                lines_div = summary.split('.') if lang in ["english", "gujarati", "tamil", "telugu", "kannada", "malayalam", "marathi", "bhojpuri"] else summary.split('।')
            
            n = len(lines_div)
            lines_div = lines_div[0:n - 1]

            # Create a directory for each language
            lang_directory = os.path.join(output_directory, lang)
            if not os.path.exists(lang_directory):
                os.makedirs(lang_directory)

            for i, line in enumerate(lines_div):
                image = Image.open(r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\WhatsApp Image 2023-11-03 at 4.04.14 PM.jpeg").resize((1920, 1080))
                draw = ImageDraw.Draw(image)
                x, y = 0, 0
                text_color = (255, 255, 255)  # White
                line_spacing = 1.5
                max_width = 1780 - x  # Maximum width available for text
                lines = []
                current_line = " "

                for word in line.split():
                    test_line = current_line + " " + word #if current_line else word
                    test_width, _ = draw.textsize(test_line, font=font)
                    if test_width <= max_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word

                if current_line:
                    lines.append(current_line)

                for lin in lines:
                    draw.text((x, y), lin, font=font, fill=text_color, spacing=line_spacing)
                    y += font.getsize(lin)[1]

                output_path = os.path.join(lang_directory, f"{lang}image{i}.png")
                image.save(output_path)
                print(lang)
                

    print("Images generated successfully.")

                #print(f"Resized and saved {filename} in the same folder")

    print("yaha aya")    
                #print(lang)
    #print("Images generated successfully.")
    base_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Text_Images"
    resized_image_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Resized_images"
    all_audio_folder = r"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\All_Audio"

    language_folders = [folder for folder in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, folder))]
    def process_language_folder(lang_folder):
        text_image_folder = os.path.join(base_folder, lang_folder)
        images_text = [img for img in os.listdir(text_image_folder) if img.endswith(".jpg") or img.endswith(".jpeg") or img.endswith(".png")]
        images_resized = [img for img in os.listdir(resized_image_folder) if img.endswith(".jpg") or img.endswith(".jpeg") or img.endswith(".png")]

        images_text.sort()
        images_resized.sort()
        print("yaha tak hua")

        if not images_text or not images_resized:
            print(f"No image files found in '{lang_folder}' folder.")
        else:
            audio_path = os.path.join(all_audio_folder, f"{lang_folder}.mp3")

            if not os.path.exists(audio_path):
                print(f"No audio file found for '{lang_folder}'.")
                return

            audio_duration = AudioFileClip(audio_path).duration
            print("yaha nhi aara hai")

            image_durations_text = [audio_duration / 8] * len(images_text)
            image_durations_resized = [audio_duration / 10] * len(images_resized)

            image_clips = []
            start_time = 0

            for i in range(max(len(images_text), len(images_resized))):
                if i < len(images_text):
                    image_path = os.path.join(text_image_folder, images_text[i])
                    image_duration = min(image_durations_text[i], audio_duration - start_time)
                    img_clip = ImageClip(image_path, duration=image_duration)
                    image_clips.append(img_clip.set_duration(image_duration))
                    start_time += image_duration

                if i < len(images_resized):
                    image_path = os.path.join(resized_image_folder, images_resized[i])
                    image_duration = min(image_durations_resized[i], audio_duration - start_time)
                    img_clip = ImageClip(image_path, duration=image_duration)
                    image_clips.append(img_clip.set_duration(image_duration))
                    start_time += image_duration

            final_clip = concatenate_videoclips(image_clips, method="compose")
            audio = AudioFileClip(audio_path)
            final_clip = final_clip.set_audio(audio)

            output_video_path = fr"C:\Users\FTT\Desktop\parul imp\static\Final_Integration\Videos\{lang_folder}.mp4"
            final_clip.write_videofile(output_video_path, codec='libx264', fps=24)
            print(f"Video '{lang_folder}.mp4' has been generated.")

    # Utilize ThreadPoolExecutor to concurrently process each language folder
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
        executor.map(process_language_folder, language_folders)
    # video_folder = 'static/Final_Integration/Videos'
    # videos = [video for video in os.listdir(video_folder) if video.endswith('.mp4')]
    # # list_videos(videos)

    # return jsonify(videos=videos)
    response_data = {'success': True}
    return jsonify(response_data)
    
@app.route('/videos')
def list_videos():
    global title
    title_head=title
    print(title_head)
    video_folder = 'static/Final_Integration/Videos'
    videos = [video for video in os.listdir(video_folder) if video.endswith('.mp4')]
    return jsonify(videos=videos,title=title_head)

VIDEO_FOLDER = 'static/Final_Integration/Videos'

@app.route('/gallery', methods=['GET'])
def gallery():
    videos = os.listdir(VIDEO_FOLDER)
    return render_template('gallery.html', videos=videos)
if __name__ == '__main__':
    app.run(debug=True)
