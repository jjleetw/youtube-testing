from flask import Flask, request, jsonify
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

app = Flask(__name__)

def extract_video_id(url):
    """提取 YouTube 影片 ID"""
    if not url: 
        return None
    patterns = [r'(?:v=|be/|embed/|shorts/)([^&\n?#]+)']
    for p in patterns:
        m = re.search(p, url)
        if m: 
            return m.group(1)
    return url if len(url) == 11 else None

@app.route('/', methods=['GET'])
def home():
    """首頁驗證"""
    return jsonify({
        'status': 'Online',
        'message': 'YouTube Transcript API 已正確運行',
        'mode': 'Original Language'
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    """獲取原頻道語言逐字稿"""
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': '請提供 url 參數'}), 200
            
        video_id = extract_video_id(data['url'])
        if not video_id:
            return jsonify({'success': False, 'error': '無效的影片連結'}), 200

        try:
            # 正確的用法：YouTubeTranscriptApi().fetch()
            # 預設語言為英文，如果沒有英文字幕會自動嘗試其他語言
            api = YouTubeTranscriptApi()
            transcript_list = api.fetch(video_id, languages=['en', 'zh-TW', 'zh-CN', 'ja', 'ko'])
            
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            return jsonify({
                'success': False, 
                'error': f'影片確實無字幕軌道',
                'video_id': video_id
            }), 200
        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f'無法獲取字幕: {str(e)}',
                'video_id': video_id
            }), 200

        # 將字幕片段串接為長文字
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript': full_text,
            'count': len(transcript_list)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'伺服器錯誤: {str(e)}'
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
