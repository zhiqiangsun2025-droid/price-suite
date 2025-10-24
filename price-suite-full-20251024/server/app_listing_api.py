#!/usr/bin/env python3
"""
服务器端上货API接口
供客户端调用，在服务器端执行网页自动上货
"""

from flask import Blueprint, request, jsonify
import base64
import tempfile
import os
from web_auto_listing import WebAutoListing

listing_bp = Blueprint('listing', __name__)

@listing_bp.route('/api/auto-listing-start', methods=['POST'])
def auto_listing_start():
    """
    开始自动上货
    
    请求参数：
    {
        "excel_base64": "Excel文件的base64编码",
        "listing_url": "上货系统网址",
        "username": "上货系统账号",  
        "password": "上货系统密码"
    }
    """
    try:
        data = request.json
        
        # 1. 接收Excel文件（base64编码）
        excel_base64 = data.get('excel_base64')
        if not excel_base64:
            return jsonify({'success': False, 'error': '缺少Excel文件'}), 400
        
        # 解码并保存到临时文件
        excel_data = base64.b64decode(excel_base64)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as f:
            f.write(excel_data)
            temp_excel_path = f.name
        
        # 2. 获取上货系统信息
        listing_url = data.get('listing_url')
        username = data.get('username')
        password = data.get('password')
        
        # 3. 启动自动上货
        auto_listing = WebAutoListing(headless=True)  # 服务器用无头模式
        
        if not auto_listing.start_browser():
            return jsonify({'success': False, 'error': '启动浏览器失败'}), 500
        
        # 4. 登录
        if not auto_listing.login(listing_url, username, password):
            auto_listing.close()
            return jsonify({'success': False, 'error': '登录失败'}), 401
        
        # 5. 批量上货
        result = auto_listing.batch_upload(temp_excel_path)
        
        # 6. 关闭浏览器
        auto_listing.close()
        
        # 7. 删除临时文件
        os.unlink(temp_excel_path)
        
        # 8. 返回结果
        return jsonify({
            'success': True,
            'result': result,
            'message': f"成功上货{result['success']}个，失败{result['failed']}个"
        })
        
    except Exception as e:
        logger.error(f"自动上货API失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@listing_bp.route('/api/auto-listing-progress', methods=['GET'])
def auto_listing_progress():
    """
    查询上货进度
    TODO: 使用后台任务队列（如Celery）实现实时进度
    """
    # 这里应该从任务队列查询进度
    # 当前返回模拟数据
    return jsonify({
        'success': True,
        'progress': {
            'current': 10,
            'total': 100,
            'status': 'running'
        }
    })


# ==================== 集成到主app ====================

def register_listing_routes(app):
    """注册上货相关路由"""
    app.register_blueprint(listing_bp)

