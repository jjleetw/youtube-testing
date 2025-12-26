from flask import Flask, request, jsonify
import re
import traceback
# 1. 核心修正：僅導入整個模組，避免名稱衝突導致的 AttributeError
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
    """首頁測試路由：確認 API 在線 (解決日誌中的 GET / 404 問題)"""
    return jsonify({
        'status': 'Online',
        'message': 'API 已採用全路徑防禦模式運行',
        'target': 'Original Channel Language'
    })

@app.route('/transcript', methods=['POST'])
def get_transcript():
    """獲取原語系逐字稿"""
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': '未提供 URL'}), 200
            
        video_id = extract_video_id(data['url'])
        if not video_id:
            return jsonify({'success': False, 'error': '無效的影片 ID 或連結'}), 200

        transcript_list = None
        
        # --- 2. 【核心修正】採用全路徑調用：模組名.類別名.方法名 ---
        # 這種方式能徹底解決 "YouTubeTranscriptApi has no attribute" 的報錯
        try:
            # 優先嘗試：直接使用基礎方法抓取預設/原始字幕 (不帶語言參數)
            transcript_list = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e1:
            # 備援策略：如果基礎方法失敗，嘗試獲取字幕清單並抓取第一個可用版本
            try:
                transcript_metadata = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
                # 抓取原頻道預設的第一個字幕 (可能是手動也可能是自動生成)
                transcript_list = next(iter(transcript_metadata)).fetch()
            except Exception as e2:
                return jsonify({
                    'success': False, 
                    'error': f'此影片找不到字幕軌道: {str(e2)}',
                    'video_id': video_id
                }), 200

        # 串接逐字稿片段為長文字段落
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript_text': full_text,
            'count': len(transcript_list)
        })

    except Exception as e:
        # 將技術報錯包裝在 JSON 中回傳
        return jsonify({'success': False, 'error': f'系統全域異常: {str(e)}'}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Zeabur 建議使用 8080 Port
    app.run(host='0.0.0.0', port=8080)
