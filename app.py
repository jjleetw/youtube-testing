from flask import Flask, request, jsonify
import re
import traceback
# 導入整個模組以確保路徑完整
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

def extract_video_id(url):
    """從 URL 提取 YouTube 影片 ID"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if url and len(url) == 11 and "/" not in url:
        return url
    return None

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'Missing URL'}), 400
            
        video_id = extract_video_id(data['url'])
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid ID or URL'}), 400
        
        transcript_list = None
        
        try:
            # 核心修正：使用完整的類別路徑調用 list_transcripts
            # 這能避開 "has no attribute" 的錯誤
            transcript_list_object = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 優先抓取原頻道手動上傳的字幕
            try:
                transcript_list = transcript_list_object.find_manually_created_transcript().fetch()
            except:
                # 若無手動字幕，則抓取第一個可用的（通常是原語系的自動生成字幕）
                transcript_list = next(iter(transcript_list_object)).fetch()

        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f'字幕庫讀取失敗: {str(e)}',
                'video_id': video_id
            }), 404
        
        # 串接為純文字，方便 n8n 直接寫入 Google Docs
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text,
            'length': len(full_text)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'系統錯誤: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 部署預設使用 8080 端口
    app.run(host='0.0.0.0', port=8080, debug=False)
