from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
load_dotenv(Path(__file__).resolve().parent / ".env")

from agents.orchestrator_agent import OrchestratorAgent
from models.trip_models import TripRequest
from services.provider_clients import AMapClient, MeituanClient

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

drafts_db = []

# 后端使用 Web服务 Key（用于坐标查询、POI 查询、服务端路线计算）
amap_api_key = os.getenv("AMAP_API_KEY", "你的key")
amap_security_code = os.getenv("AMAP_SECURITY_CODE", "")

amap_client = AMapClient(api_key=amap_api_key, security_code=amap_security_code)
meituan_client = MeituanClient()
orchestrator = OrchestratorAgent(amap_client, meituan_client)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': '服务运行正常'})


@app.route('/api/drafts', methods=['GET'])
def get_drafts():
    return jsonify({'code': 0, 'data': drafts_db, 'message': '获取成功'})


@app.route('/api/drafts', methods=['POST'])
def create_draft():
    data = request.json
    draft = {
        'id': str(int(datetime.now().timestamp() * 1000)),
        'departure': data.get('departure'),
        'destination': data.get('destination'),
        'departureTime': data.get('departureTime'),
        'returnTime': data.get('returnTime'),
        'days': data.get('days'),
        'createdAt': datetime.now().isoformat(),
        'content': []
    }
    drafts_db.append(draft)
    return jsonify({'code': 0, 'data': draft, 'message': '创建成功'}), 201


@app.route('/api/drafts/<draft_id>', methods=['DELETE'])
def delete_draft(draft_id):
    global drafts_db
    drafts_db = [d for d in drafts_db if d['id'] != draft_id]
    return jsonify({'code': 0, 'message': '删除成功'})


@app.route('/api/locations/search', methods=['GET'])
def search_locations():
    query = request.args.get('q', '')
    return jsonify({'code': 0, 'data': [], 'message': '搜索成功'})


@app.route('/api/planner/generate', methods=['POST'])
def generate_itinerary():
    """
    生成完整旅行规划。
    
    请求体：
    {
        "departure": "深圳",
        "destination": "桂林",
        "departureTime": "2026-04-03T17:00:00",
        "returnTime": "2026-04-05T20:00:00",
        "departureCoords": {"lat": 22.5, "lng": 114.0},
        "destinationCoords": {"lat": 25.3, "lng": 110.3},
        "transportModes": ["高铁", "飞机"],
        "hotelAnchor": "桂林市中心",
        "interests": ["风景", "美食"],
        "foodPreferences": ["本地特色"],
        "budget": 3000,
        "adults": 1
    }
    """
    try:
        print('[Backend] 收到规划请求')
        data = request.json
        trip_request = TripRequest.from_dict(data)
        print(f'[Backend] 开始规划: {trip_request.departure} -> {trip_request.destination}')
        result = orchestrator.plan(trip_request)
        print(f'[Backend] 规划完成，code: {result.get("code")}')
        return jsonify(result)
    except Exception as e:
        print(f'[Backend] 规划异常: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'data': None,
            'message': f'规划失败: {str(e)}'
        }), 500


@app.route('/api/planner/replan-hotel', methods=['POST'])
def replan_with_hotel_change():
    """
    用户更换住宿地点后的重规划。
    
    请求体：
    {
        "trip": {...},  # 原始 trip 数据
        "newHotelAnchor": "新的住宿地点"
    }
    """
    try:
        data = request.json
        trip_data = data.get('trip', {})
        new_hotel_anchor = data.get('newHotelAnchor', '')
        
        trip_request = TripRequest.from_dict(trip_data)
        result = orchestrator.replan_with_hotel_change(trip_request, new_hotel_anchor)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'message': f'重规划失败: {str(e)}'
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'code': 404, 'message': '资源不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'code': 500, 'message': '服务器错误'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
