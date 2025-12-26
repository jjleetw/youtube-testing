from flask import Flask, request, jsonify
import re
import traceback
# 1. 採用最嚴謹的導入方式
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
            return jsonify({'success': False, 'error': '缺少 URL 參數'}), 400
            
        video_id = extract_video_id(data['url'])
        if not video_id:
            return jsonify({'success': False, 'error': '無效的 YouTube 連結或 ID'}), 400
        
        transcript_list = None
        
        try:
            # 2. 直接使用全路徑調用，徹底避開 "has no attribute" 報錯
            # 此方法需要 youtube-transcript-api 版本 >= 0.4.0
            proxy_list = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 3. 優先獲取原頻道語言 (不進行翻譯，以原汁原味為主)
            try:
                # 優先找「人工上傳」的原始字幕
                transcript_obj = proxy_list.find_manually_created_transcript()
                transcript_list = transcript_obj.fetch()
            except:
                # 若無人工字幕，則抓取該影片「預設的第一個」字幕 (通常是原語系的自動生成)
                transcript_obj = next(iter(proxy_list))
                transcript_list = transcript_obj.fetch()

        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f'字幕抓取失敗: {str(e)}',
                'video_id': video_id
            }), 404
        
        # 4. 串接為純文字，方便 n8n 的 Google Docs 節點使用
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text,
            'language_code': transcript_obj.language_code if 'transcript_obj' in locals() else 'unknown'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'系統異常: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 預設使用 8080 端口
    app.run(host='0.0.0.0', port=8080, debug=False)
