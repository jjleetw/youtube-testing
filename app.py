from flask import Flask, request, jsonify
import re
# 核心修正：僅導入整個模組，避免名稱衝突導致的 AttributeError
import youtube_transcript_api

app = Flask(__name__)

def extract_video_id(url):
    """提取 YouTube 影片 ID"""
    if not url: return None
    patterns = [r'(?:v=|be/|embed/|shorts/)([^&\n?#]+)']
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return url if len(url) == 11 else None

@app.route('/', methods=['GET'])
def home():
    """驗證路由：若看到此訊息，代表 API 已經成功啟動且代碼已更新"""
    return jsonify({
        'status': 'Online',
        'message': 'API 已採用全路徑防禦模式運行 (Original Language)',
        'check': '如果您看到這個 JSON，代表路由已正確對接'
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': '請提供 url 參數'}), 200
            
        video_id = extract_video_id(data['url'])
        if not video_id:
            return jsonify({'success': False, 'error': '無效的影片 ID 或連結'}), 200

        transcript_list = None
        
        # --- 核心修正：採用「全路徑」調用，徹底解決 "no attribute" 報錯 ---
        try:
            # 優先嘗試：直接抓取影片原語系字幕 (不指定語言則抓取預設語系)
            # 格式：模組名.類別名.方法名
            transcript_list = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e1:
            # 備援策略：如果基礎方法失敗，嘗試獲取字幕清單
            try:
                transcript_metadata = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
                transcript_list = next(iter(transcript_metadata)).fetch()
            except Exception as e2:
                return jsonify({
                    'success': False, 
                    'error': f'此影片確實找不到任何字幕: {str(e2)}',
                    'video_id': video_id
                }), 200

        # 將字幕片段串接為長文字段落
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text
        })

    except Exception as e:
        # 將技術報錯包裝在 JSON 中回傳
        return jsonify({'success': False, 'error': f'程式執行錯誤: {str(e)}'}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 部署必須使用 8080 Port
    app.run(host='0.0.0.0', port=8080)
