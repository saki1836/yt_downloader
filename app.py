from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import time

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ইউটিউব ব্লক এড়ানোর জন্য কনফিগারেশন
YDL_COMMON_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'extractor_args': {'youtube': {'player_client': ['android', 'web'], 'po_token': ['web+guest']}}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    if not url: return jsonify({"error": "URL missing"}), 400
    with yt_dlp.YoutubeDL(YDL_COMMON_OPTS) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            play_url = next((f.get('url') for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4'), info.get('url'))
            return jsonify({"title": info.get('title'), "video_url": play_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    video_url = request.args.get('url')
    quality = request.args.get('quality')
    file_id = str(int(time.time()))
    ydl_opts = YDL_COMMON_OPTS.copy()
    
    # এটি মার্জিং ছাড়াই সরাসরি সেরা MP4 ফাইল ডাউনলোড করবে
    q_map = {
        'fullhd': 'best[height<=1080][ext=mp4]/best[height<=1080]/best',
        'medium': 'best[height<=720][ext=mp4]/best[height<=720]/best',
        'low': 'worst'
    }
    
    out_tmpl = f'{DOWNLOAD_FOLDER}/video_{file_id}.%(ext)s'
    ydl_opts.update({'format': q_map.get(quality, 'best'), 'outtmpl': out_tmpl})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

