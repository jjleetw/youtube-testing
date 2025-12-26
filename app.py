from flask import Flask, request, jsonify
import re
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

def extract_video_id(url):
    """提取影片 ID"""
    if not url: return None
    patterns = [r'(?:v=|be/|embed/|shorts/)([^&\n?#]+)']
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return url if len(url) == 11 else None

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.json
        url = data.get('url')
        video_id = extract_video_id(url)
        
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid URL'}), 400

        transcript_list = None
        
        # --- 策略 1：使用最基礎的方法 (相容所有版本) ---
        try:
            # 不帶 languages 參數，由套件自行決定抓取哪種語言 (通常是預設語言)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e1:
            # --- 策略 2：如果基礎方法失敗，嘗試偵測是否有新版 list_transcripts 屬性 ---
            if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
                try:
                    proxy = YouTubeTranscriptApi.list_transcripts(video_id)
                    transcript_list = next(iter(proxy)).fetch()
                except Exception as e2:
                    return jsonify({'success': False, 'error': f'找不到任何字幕: {str(e2)}'}), 404
            else:
                return jsonify({'success': False, 'error': f'基礎抓取失敗且套件版本過舊: {str(e1)}'}), 404

        # 串接文字
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'系統錯誤: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
