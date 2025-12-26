from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
import traceback

app = Flask(__name__)

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'YouTube Transcript API is running',
        'endpoints': {
            '/transcript': 'POST - Get YouTube transcript',
            '/health': 'GET - Health check'
        }
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    """Get YouTube transcript"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        video_id = extract_video_id(url)
        if not video_id:
            # 如果傳入的已經是 ID 而非 URL，直接使用
            video_id = url if len(url) == 11 else None
            
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL or ID'}), 400
        
        # 嘗試獲取字幕，優先順序：繁體中文 > 簡體 > 英文
        transcript_list = None
        languages_to_try = [
            ['zh-Hant'],
            ['zh-Hans'],
            ['zh'],
            ['en'],
            None  # 任何可用的語言
        ]
        
        for languages in languages_to_try:
            try:
                if languages:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                else:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                break
            except Exception as lang_error:
                continue
        
        if not transcript_list:
            return jsonify({'error': 'No transcript found for this video'}), 404
        
        # 轉換為純文本格式
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text,
            'raw_transcript': transcript_list
        })

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        print(traceback.format_exc())
        
        # 針對常見錯誤提供更友善的訊息
        if "Subtitles are disabled" in error_msg:
            return jsonify({'error': '此影片已關閉字幕功能'}), 404
        elif "No transcript found" in error_msg:
            return jsonify({'error': '找不到符合語言要求的字幕'}), 404
        
        return jsonify({'error': error_msg}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
