#!/usr/bin/env python3
"""
商品价格对比系统 - 服务器端
功能：
1. IP 授权验证
2. 硬件绑定验证
3. 淘宝商品爬取
4. 拼多多价格对比
5. 数据导出
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from functools import wraps
import inspect
import hashlib
import json
import time
from datetime import datetime, timedelta
import sqlite3
import os
import ipaddress
import logging

# 配置日志 - 使用轮转
import logging.handlers
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

file_handler = logging.handlers.RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=7,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)
CORS(app)

# 配置
DB_PATH = 'authorization.db'
SECRET_KEY = 'your-secret-key-change-this'  # 修改为你的密钥
# 管理员登录口令（可用环境变量 ADMIN_PASSWORD 覆盖）
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# 获取北京时间
def get_beijing_time():
    """返回北京时间字符串 (UTC+8)"""
    return (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

# 用于Flask会话
app.secret_key = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ==================== 数据库初始化 ====================

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 授权表（总开关）
    c.execute('''
        CREATE TABLE IF NOT EXISTS authorizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE NOT NULL,
            client_name TEXT,
            ip_address TEXT,
            hardware_id TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            request_count INTEGER DEFAULT 0,
            last_request_at TIMESTAMP
        )
    ''')
    
    # 指纹访问与试用（后端为唯一真相）
    c.execute('''
        CREATE TABLE IF NOT EXISTS client_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            hardware_id TEXT,
            ip_address TEXT,
            first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trial_started_at TIMESTAMP,
            trial_expires_at TIMESTAMP,
            last_trial_granted_at DATE,
            approved INTEGER DEFAULT 0
        )
    ''')

    # 请求日志表（保留）
    c.execute('''
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            ip_address TEXT,
            request_type TEXT,
            success INTEGER,
            error_msg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 事件埋点表（前端重要操作上报）
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            hardware_id TEXT,
            ip_address TEXT,
            action TEXT,
            detail_json TEXT,
            success INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # IP 白名单表（一个客户端可配置多个网段/IP）
    c.execute('''
        CREATE TABLE IF NOT EXISTS ip_whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            ip_cidr TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 选品规则表（全局或可被客户端引用）
    c.execute('''
        CREATE TABLE IF NOT EXISTS selection_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_diff_threshold REAL DEFAULT 0.30, -- 低价比例阈值
            prefer_platform TEXT DEFAULT 'pinduoduo',
            time_window_days INTEGER DEFAULT 1,
            min_exposure INTEGER DEFAULT 10,
            min_clicks INTEGER DEFAULT 1,
            min_growth_percent REAL DEFAULT 0.20,
            allow_official INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # 客户端设置（绑定规则等）
    c.execute('''
        CREATE TABLE IF NOT EXISTS client_settings (
            client_id TEXT PRIMARY KEY,
            rule_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_auth_client_id ON authorizations(client_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_logs_client_time ON request_logs(client_id, created_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_access_client_hw_ip ON client_access(client_id, hardware_id, ip_address)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_access_trial_expires ON client_access(trial_expires_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_event_client_time ON event_logs(client_id, created_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_ipwl_client ON ip_whitelist(client_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_rules_active ON selection_rules(is_active, updated_at)')
    
    conn.commit()
    conn.close()

init_db()

# ==================== 授权验证装饰器 ====================

TRIAL_SECONDS = 3600  # 后端统一控制：1小时

def _grant_or_validate_trial(c, client_id: str, hardware_id: str, ip_address: str):
    """授予或校验试用资格：同一hardware每天仅发一次。返回(authorized, trial_remaining_seconds, reason)。"""
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')

    # 查询指纹记录
    c.execute('''SELECT id, trial_started_at, trial_expires_at, last_trial_granted_at, approved
                 FROM client_access WHERE client_id=? AND hardware_id=? AND ip_address=? LIMIT 1''',
              (client_id, hardware_id, ip_address))
    row = c.fetchone()

    # 已显式批准
    if row and row[4] == 1:
        return True, None, None

    # 试用有效
    if row and row[2]:
        try:
            exp = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
            if now < exp:
                return True, int((exp - now).total_seconds()), None
        except Exception:
            pass

    # 是否当天已发放
    if row and row[3] == today:
        return False, 0, 'daily_quota_exhausted'

    # 发放试用
    start = now
    exp = now + timedelta(seconds=TRIAL_SECONDS)
    if row:
        c.execute('''UPDATE client_access SET trial_started_at=?, trial_expires_at=?, last_seen_at=?, last_trial_granted_at=?
                     WHERE id=?''',
                  (start.strftime('%Y-%m-%d %H:%M:%S'), exp.strftime('%Y-%m-%d %H:%M:%S'),
                   get_beijing_time(), today, row[0]))
    else:
        c.execute('''INSERT INTO client_access (client_id, hardware_id, ip_address, trial_started_at, trial_expires_at, last_trial_granted_at)
                     VALUES (?,?,?,?,?,?)''',
                  (client_id, hardware_id, ip_address, start.strftime('%Y-%m-%d %H:%M:%S'),
                   exp.strftime('%Y-%m-%d %H:%M:%S'), today))
    return True, TRIAL_SECONDS, None


def require_auth(f):
    """授权验证装饰器（后端唯一判定：批准/试用/拒绝，并可指示前端弹窗）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端信息
        client_id = request.headers.get('X-Client-ID')
        hardware_id = request.headers.get('X-Hardware-ID')
        ip_address = request.remote_addr
        
        if not client_id or not hardware_id:
            return jsonify({
                'success': False,
                'error_code': 101,
                'error': '功能升级中，请联系QQ: 123456789'
            }), 401
        
        # 验证授权（后端唯一判定）
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.row_factory = None
        
        # 放开IP校验，优先按client_id / hardware_id识别（你要求先用机器码识别）
        auth = None
        if client_id:
            c.execute('SELECT * FROM authorizations WHERE client_id = ? LIMIT 1', (client_id,))
            auth = c.fetchone()
        if not auth and hardware_id:
            c.execute('SELECT * FROM authorizations WHERE hardware_id = ? LIMIT 1', (hardware_id,))
            auth = c.fetchone()
        # 最后兜底：若仍未匹配，再按IP已批准记录尝试一次（兼容老客户）
        if not auth:
            c.execute('SELECT * FROM authorizations WHERE ip_address = ? AND is_active = 1 LIMIT 1', (ip_address,))
        auth = c.fetchone()
        
        if not auth:
            # 首次出现client_id也给予试用（按 hardware 限日）
            authorized, left, reason = _grant_or_validate_trial(c, client_id or 'UNKNOWN', hardware_id or 'UNKNOWN', ip_address)
            conn.commit()
            conn.close()
            if authorized:
                # 允许通过（试用）
                response = f(auth, *args, **kwargs)
                return response
            # 拒绝并指示前端弹窗
            return jsonify({'success': False, 'show_popup': True, 'reason': reason or 'not_found'}), 403
        
        # 检查状态
        is_active = auth[5]
        
        # 已拒绝
        if is_active == -1:
            conn.close()
            return jsonify({'success': False, 'show_popup': True, 'reason': 'rejected'}), 403
        
        # 待审核（is_active=0）和已批准（is_active=1）都允许通过
        # 试用期由客户端自己控制
        
        # 已批准：直接放行；未批准：进入试用逻辑
        if is_active != 1:
            authorized, left, reason = _grant_or_validate_trial(c, client_id, hardware_id, ip_address)
            conn.commit()
            if not authorized:
                conn.close()
                return jsonify({'success': False, 'show_popup': True, 'reason': reason or 'trial_expired'}), 403
        
        # 过期时间（如配置）
        expires_at = auth[7]
        if expires_at:
            try:
                expire_time = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
                if datetime.now() > expire_time:
                    conn.close()
                    return jsonify({'success': False, 'show_popup': True, 'reason': 'auth_expired'}), 403
            except Exception:
                pass
        
        # 若绑定规则，读取规则（预留：可用于限流/策略）
        c.execute('SELECT rule_id FROM client_settings WHERE client_id=?', (client_id,))
        row = c.fetchone()
        if row and row[0]:
            c.execute('SELECT * FROM selection_rules WHERE id=? AND is_active=1', (row[0],))
            active_rule = c.fetchone()  # 当前未强制校验，仅用于业务策略

        # 更新请求统计（使用北京时间）；不强制覆盖管理员清空的IP
        # 只在首次为空时写入IP，避免管理员清空后被自动回填
        c.execute('''
            UPDATE authorizations 
            SET request_count = request_count + 1,
                last_request_at = ?,
                ip_address = CASE WHEN (ip_address IS NULL OR ip_address = '') THEN ? ELSE ip_address END
            WHERE client_id = ?
        ''', (get_beijing_time(), ip_address, client_id))
        
        conn.commit()
        conn.close()
        
        # 传递 auth 参数给被装饰的函数（兼容老签名）
        sig = inspect.signature(f)
        if 'auth' in sig.parameters:
            return f(auth, *args, **kwargs)
        else:
            return f(*args, **kwargs)
    
    return decorated_function

# ==================== 管理后台鉴权 ====================

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return wrapped

def log_request(client_id, ip_address, request_type, success, error_msg=None):
    """记录请求日志"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO request_logs (client_id, ip_address, request_type, success, error_msg)
        VALUES (?, ?, ?, ?, ?)
    ''', (client_id, ip_address, request_type, 1 if success else 0, error_msg))
    conn.commit()
    conn.close()


@app.route('/api/event', methods=['POST'])
def track_event():
    """前端埋点：记录关键操作事件。"""
    client_id = request.headers.get('X-Client-ID')
    hardware_id = request.headers.get('X-Hardware-ID')
    ip_address = request.remote_addr
    data = request.json or {}
    action = data.get('action') or 'unknown'
    detail_json = json.dumps(data.get('detail') or {}, ensure_ascii=False)
    success = 1 if data.get('success', True) else 0

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO event_logs (client_id, hardware_id, ip_address, action, detail_json, success)
                 VALUES (?,?,?,?,?,?)''', (client_id, hardware_id, ip_address, action, detail_json, success))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ==================== API 接口 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': '服务正常运行',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/rules/active', methods=['GET'])
@require_auth
def api_active_rules():
    """返回启用中的选品规则列表（客户端可读取）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, price_diff_threshold, prefer_platform, time_window_days, min_exposure, min_clicks, min_growth_percent, allow_official FROM selection_rules WHERE is_active=1 ORDER BY updated_at DESC')
    rows = c.fetchall()
    conn.close()
    rules = []
    for r in rows:
        rules.append({
            'id': r[0],
            'name': r[1],
            'price_diff_threshold': r[2],
            'prefer_platform': r[3],
            'time_window_days': r[4],
            'min_exposure': r[5],
            'min_clicks': r[6],
            'min_growth_percent': r[7],
            'allow_official': bool(r[8])
        })
    return jsonify({'success': True, 'data': rules})

@app.route('/api/register', methods=['POST'])
def register_client():
    """客户端自动注册（首次启动时调用）"""
    data = request.json
    hardware_id = data.get('hardware_id')
    ip_address = request.remote_addr
    
    if not hardware_id:
        return jsonify({
            'success': False,
            'error': '缺少硬件ID'
        }), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 检查是否已注册
        c.execute('SELECT * FROM authorizations WHERE hardware_id=?', (hardware_id,))
        existing = c.fetchone()
        
        if existing:
            # 已注册，返回现有信息
            client_id = existing[1]
            is_active = existing[5]
            expires_at = existing[7]
            
            # 更新最后请求时间和IP
            c.execute('UPDATE authorizations SET ip_address=? WHERE hardware_id=?', 
                     (ip_address, hardware_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'client_id': client_id,
                'is_active': is_active,
            'expires_at': expires_at,
                'message': '已找到现有授权' if is_active == 1 else '等待管理员审核'
            })
        
        # 新注册：生成客户端ID
        client_id = hashlib.md5(f"{hardware_id}{ip_address}{time.time()}".encode()).hexdigest()
        client_name = f"客户端_{hardware_id[:8]}"
        
        # 插入待审核记录（is_active=0）
        c.execute('''
            INSERT INTO authorizations (client_id, client_name, ip_address, hardware_id, is_active)
            VALUES (?, ?, ?, ?, 0)
        ''', (client_id, client_name, ip_address, hardware_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'client_id': client_id,
            'is_active': 0,
            'expires_at': None,
            'message': '注册成功，等待管理员审核（可试用1小时）'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/compare-prices', methods=['POST'])
@require_auth
def compare_prices():
    """
    价格对比核心功能
    输入：淘宝商品数据
    输出：拼多多低价商品列表
    """
    client_id = request.headers.get('X-Client-ID')
    ip_address = request.remote_addr
    
    try:
        data = request.json
        taobao_products = data.get('products', [])
        discount_threshold = data.get('discount_threshold', 0.3)  # 默认30%折扣
        
        log_request(client_id, ip_address, 'COMPARE_PRICES', True)
        
        # 调用价格对比逻辑
        results = process_price_comparison(taobao_products, discount_threshold)
        
        return jsonify({
            'success': True,
            'data': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        log_request(client_id, ip_address, 'COMPARE_PRICES', False, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape-taobao', methods=['POST'])
@require_auth
def scrape_taobao():
    """淘宝商品爬取"""
    client_id = request.headers.get('X-Client-ID')
    ip_address = request.remote_addr
    
    try:
        data = request.json
        keyword = data.get('keyword')
        max_count = data.get('max_count', 50)
        
        log_request(client_id, ip_address, 'SCRAPE_TAOBAO', True)
        
        # 调用淘宝爬虫（这里需要集成你的爬虫代码）
        products = scrape_taobao_products(keyword, max_count)
        
        return jsonify({
            'success': True,
            'data': products,
            'count': len(products)
        })
    
    except Exception as e:
        log_request(client_id, ip_address, 'SCRAPE_TAOBAO', False, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape-pinduoduo', methods=['POST'])
@require_auth
def scrape_pinduoduo():
    """拼多多商品爬取"""
    client_id = request.headers.get('X-Client-ID')
    ip_address = request.remote_addr
    
    try:
        data = request.json
        keyword = data.get('keyword')
        max_count = data.get('max_count', 50)
        
        log_request(client_id, ip_address, 'SCRAPE_PINDUODUO', True)
        
        # 调用拼多多爬虫
        products = scrape_pinduoduo_products(keyword, max_count)
        
        return jsonify({
            'success': True,
            'data': products,
            'count': len(products)
        })
    
    except Exception as e:
        log_request(client_id, ip_address, 'SCRAPE_PINDUODUO', False, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 核心业务逻辑 ====================

def scrape_taobao_products(keyword, max_count):
    """
    淘宝商品爬取逻辑
    TODO: 集成你之前的 Selenium 爬虫代码
    """
    # 这里集成你的淘宝爬虫代码
    # 返回格式示例：
    return [
        {
            'title': '示例商品',
            'price': 999.00,
            'sales': '1000+',
            'shop_name': '示例店铺',
            'url': 'https://item.taobao.com/...'
        }
    ]

def scrape_pinduoduo_products(keyword, max_count):
    """
    拼多多商品爬取逻辑
    TODO: 开发拼多多爬虫
    """
    # 这里添加拼多多爬虫代码
    return [
        {
            'title': '示例商品',
            'price': 699.00,
            'sales': '2000+',
            'shop_name': '拼多多店铺',
            'url': 'https://mobile.yangkeduo.com/...'
        }
    ]

def process_price_comparison(taobao_products, discount_threshold):
    """
    价格对比核心算法
    输入：淘宝商品列表
    输出：拼多多低价商品列表
    """
    results = []
    
    for tb_product in taobao_products:
        keyword = tb_product.get('title', '')[:20]  # 使用商品标题前20字搜索
        
        # 在拼多多搜索相同商品
        pdd_products = scrape_pinduoduo_products(keyword, 10)
        
        # 对比价格
        tb_price = float(tb_product.get('price', 0))
        
        for pdd_product in pdd_products:
            pdd_price = float(pdd_product.get('price', 0))
            
            # 计算折扣
            if tb_price > 0:
                discount = (tb_price - pdd_price) / tb_price
                
                # 如果折扣超过阈值
                if discount >= discount_threshold:
                    results.append({
                        'taobao_product': tb_product,
                        'pinduoduo_product': pdd_product,
                        'discount_rate': f"{discount * 100:.1f}%",
                        'price_diff': tb_price - pdd_price,
                        'taobao_price': tb_price,
                        'pinduoduo_price': pdd_price
                    })
    
    # 按折扣率排序
    results.sort(key=lambda x: float(x['discount_rate'].rstrip('%')), reverse=True)
    
    return results

# ==================== 管理员接口 ====================

@app.route('/api/admin/clients', methods=['GET'])
def list_clients():
    """列出所有客户端"""
    admin_key = request.args.get('admin_key')
    
    if admin_key != SECRET_KEY:
        return jsonify({
            'success': False,
            'error': '管理员密钥错误'
        }), 403
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM authorizations ORDER BY created_at DESC')
    clients = c.fetchall()
    conn.close()
    
    clients_list = []
    for client in clients:
        clients_list.append({
            'id': client[0],
            'client_id': client[1],
            'client_name': client[2],
            'ip_address': client[3],
            'hardware_id': client[4],
            'is_active': client[5],
            'created_at': client[6],
            'expires_at': client[7],
            'request_count': client[8],
            'last_request_at': client[9]
        })
    
    return jsonify({
        'success': True,
        'data': clients_list,
        'count': len(clients_list)
    })

@app.route('/api/admin/toggle-client', methods=['POST'])
def toggle_client():
    """启用/禁用客户端"""
    admin_key = request.json.get('admin_key')
    
    if admin_key != SECRET_KEY:
        return jsonify({
            'success': False,
            'error': '管理员密钥错误'
        }), 403
    
    client_id = request.json.get('client_id')
    is_active = request.json.get('is_active', 1)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE authorizations SET is_active = ? WHERE client_id = ?', 
              (is_active, client_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'客户端已{"启用" if is_active else "禁用"}'
    })

# ==================== 管理后台页面 ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(request.args.get('next') or url_for('admin_clients_page'))
        flash('密码错误', 'danger')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_home():
    return redirect(url_for('admin_clients_page'))

@app.route('/admin/clients')
@admin_required
def admin_clients_page():
    q = request.args.get('q', '').strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if q:
        like = f"%{q}%"
        c.execute('''SELECT * FROM authorizations 
                     WHERE client_name LIKE ? OR client_id LIKE ? OR ip_address LIKE ?
                     ORDER BY created_at DESC''', (like, like, like))
    else:
        c.execute('SELECT * FROM authorizations ORDER BY created_at DESC')
    clients = c.fetchall()
    conn.close()
    return render_template('clients.html', clients=clients, q=q)

@app.route('/admin/clients/new', methods=['GET', 'POST'])
@admin_required
def admin_client_new():
    if request.method == 'POST':
        name = request.form.get('client_name')
        ip = request.form.get('ip_address') or None
        hardware_id = request.form.get('hardware_id') or None
        expires_days = int(request.form.get('expires_days') or 365)
        from datetime import timedelta
        client_id = hashlib.md5(f"{name}{hardware_id}{time.time()}".encode()).hexdigest()
        expires_at = (datetime.now() + timedelta(days=expires_days)).strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO authorizations (client_id, client_name, ip_address, hardware_id, expires_at) VALUES (?,?,?,?,?)',
                  (client_id, name, ip, hardware_id, expires_at))
        conn.commit()
        conn.close()
        flash('已创建客户端', 'success')
        return redirect(url_for('admin_clients_page'))
    return render_template('client_form.html', client=None)

@app.route('/admin/clients/<int:cid>/edit', methods=['GET', 'POST'])
@admin_required
def admin_client_edit(cid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM authorizations WHERE id = ?', (cid,))
    client = c.fetchone()
    if not client:
        conn.close()
        flash('未找到客户端', 'danger')
        return redirect(url_for('admin_clients_page'))
    if request.method == 'POST':
        name = request.form.get('client_name')
        ip = request.form.get('ip_address') or None
        hardware_id = request.form.get('hardware_id') or None
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        expires_at = request.form.get('expires_at') or None
        c.execute('''UPDATE authorizations SET client_name=?, ip_address=?, hardware_id=?, is_active=?, expires_at=? WHERE id=?''',
                  (name, ip, hardware_id, is_active, expires_at, cid))
        conn.commit()
        conn.close()
        flash('已保存', 'success')
        return redirect(url_for('admin_clients_page'))
    conn.close()
    return render_template('client_form.html', client=client)

@app.route('/admin/clients/<int:cid>/approve')
@admin_required
def admin_client_approve(cid):
    """批准客户端"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    from datetime import timedelta
    expires_at = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('UPDATE authorizations SET is_active=1, expires_at=? WHERE id=?', (expires_at, cid))
    conn.commit()
    conn.close()
    flash('✓ 已批准客户端，有效期1年', 'success')
    return redirect(url_for('admin_clients_page'))

@app.route('/admin/clients/<int:cid>/reject')
@admin_required
def admin_client_reject(cid):
    """拒绝客户端"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE authorizations SET is_active=-1 WHERE id=?', (cid,))
    conn.commit()
    conn.close()
    flash('✗ 已拒绝客户端', 'warning')
    return redirect(url_for('admin_clients_page'))

@app.route('/admin/clients/<int:cid>/set-status/<int:status>')
@admin_required
def admin_client_set_status(cid, status):
    """设置客户端状态"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE authorizations SET is_active=? WHERE id=?', (status, cid))
    conn.commit()
    conn.close()
    
    status_text = {0: '待审核', 1: '已批准', -1: '已拒绝'}.get(status, '未知')
    flash(f'已更新状态为：{status_text}', 'success')
    return redirect(url_for('admin_clients_page'))

@app.route('/admin/logs')
@admin_required
def admin_logs():
    client_id = request.args.get('client_id', '').strip()
    ip = request.args.get('ip', '').strip()
    action = request.args.get('action', '').strip()
    success = request.args.get('success', '')
    delete_before = request.args.get('delete_before')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 可选：删除7天前日志
    if delete_before:
        c.execute("DELETE FROM request_logs WHERE created_at < datetime('now','-7 days')")
        conn.commit()

    # 构建查询
    sql = 'SELECT * FROM request_logs WHERE 1=1'
    params = []
    if client_id:
        sql += ' AND client_id LIKE ?'
        params.append(f"%{client_id}%")
    if ip:
        sql += ' AND ip_address LIKE ?'
        params.append(f"%{ip}%")
    if action:
        sql += ' AND request_type LIKE ?'
        params.append(f"%{action}%")
    if success in ('0','1'):
        sql += ' AND success = ?'
        params.append(int(success))
    sql += ' ORDER BY created_at DESC LIMIT 500'

    c.execute(sql, tuple(params))
    logs = c.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs, client_id=client_id, ip=ip, action=action, success=success)


@app.route('/admin/events')
@admin_required
def admin_events():
    client_id = request.args.get('client_id', '').strip()
    action = request.args.get('action', '').strip()
    ip = request.args.get('ip', '').strip()
    success = request.args.get('success', '')
    delete_before = request.args.get('delete_before')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if delete_before:
        c.execute("DELETE FROM event_logs WHERE created_at < datetime('now','-30 days')")
        conn.commit()

    sql = 'SELECT id, client_id, hardware_id, ip_address, action, detail_json, success, created_at FROM event_logs WHERE 1=1'
    params = []
    if client_id:
        sql += ' AND client_id LIKE ?'
        params.append(f"%{client_id}%")
    if action:
        sql += ' AND action LIKE ?'
        params.append(f"%{action}%")
    if ip:
        sql += ' AND ip_address LIKE ?'
        params.append(f"%{ip}%")
    if success in ('0','1'):
        sql += ' AND success = ?'
        params.append(int(success))
    sql += ' ORDER BY created_at DESC LIMIT 500'

    c.execute(sql, tuple(params))
    rows = c.fetchall()
    conn.close()
    return render_template('events.html', rows=rows, client_id=client_id, action=action, ip=ip, success=success)

@app.route('/admin/rules', methods=['GET', 'POST'])
@admin_required
def admin_rules():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form.get('name') or '默认规则'
        price_diff_threshold = float(request.form.get('price_diff_threshold') or 0.30)
        prefer_platform = request.form.get('prefer_platform') or 'pinduoduo'
        time_window_days = int(request.form.get('time_window_days') or 1)
        min_exposure = int(request.form.get('min_exposure') or 10)
        min_clicks = int(request.form.get('min_clicks') or 1)
        min_growth_percent = float(request.form.get('min_growth_percent') or 0.20)
        allow_official = 1 if request.form.get('allow_official') == 'on' else 0
        c.execute('''INSERT INTO selection_rules 
                     (name, price_diff_threshold, prefer_platform, time_window_days, min_exposure, min_clicks, min_growth_percent, allow_official)
                     VALUES (?,?,?,?,?,?,?,?)''',
                  (name, price_diff_threshold, prefer_platform, time_window_days, min_exposure, min_clicks, min_growth_percent, allow_official))
        conn.commit()
    c.execute('SELECT * FROM selection_rules WHERE is_active=1 ORDER BY updated_at DESC')
    rules = c.fetchall()
    conn.close()
    return render_template('rules.html', rules=rules)

@app.route('/admin/ipwl/<client_id>', methods=['GET', 'POST'])
@admin_required
def admin_ip_whitelist(client_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        ip_cidr = request.form.get('ip_cidr')
        if ip_cidr:
            c.execute('INSERT INTO ip_whitelist (client_id, ip_cidr) VALUES (?,?)', (client_id, ip_cidr))
            conn.commit()
    c.execute('SELECT * FROM ip_whitelist WHERE client_id=? ORDER BY created_at DESC', (client_id,))
    ips = c.fetchall()
    conn.close()
    return render_template('ipwl.html', client_id=client_id, ips=ips)

# ==================== 智能选品API ====================

@app.route('/api/intelligent-selection', methods=['POST'])
@require_auth
def intelligent_selection():
    """
    智能选品API（核心逻辑全在服务器）
    客户端只传参数，服务器返回结果
    """
    try:
        data = request.json
        client_id = request.headers.get('X-Client-ID')
        
        # 获取参数
        category = data.get('category')  # 类目
        timerange = data.get('timerange', '近7天')  # 时间段
        count = int(data.get('count', 50))  # 数量
        discount_threshold = float(data.get('discount_threshold', 0.30))  # 价差阈值
        growth_threshold = float(data.get('growth_threshold', 0.20))  # 增长阈值
        allow_official = data.get('allow_official', True)  # 是否包含官方
        
        log_request(client_id, request.remote_addr, 'intelligent_selection', True)
        
        # 1. 从抖音/淘宝爬取商品（服务器端执行）
        source_products = scrape_source_platform(
            category=category,
            timerange=timerange,
            count=count,
            growth_threshold=growth_threshold,
            allow_official=allow_official
        )
        
        if not source_products:
            return jsonify({
                'success': False,
                'error': '未找到符合条件的源商品'
            })
        
        # 2. 逐个从拼多多搜索匹配商品（服务器端执行）
        matched_results = []
        
        for idx, source_prod in enumerate(source_products):
            # 搜索拼多多
            pdd_candidates = search_pinduoduo(source_prod['title'])
            
            if not pdd_candidates:
                continue
            
            # 使用AI匹配器找出最相似的商品
            from ai_matcher import ProductMatcher
            matcher = ProductMatcher()
            
            matched = matcher.match_products(source_prod, pdd_candidates)
            
            # 筛选价格符合条件的
            for pdd_prod, similarity in matched:
                if similarity < 0.6:  # 相似度阈值
                    continue
                
                # 计算价差
                price_diff = (source_prod['price'] - pdd_prod['price']) / source_prod['price']
                
                if price_diff >= discount_threshold:
                    matched_results.append({
                        'title': source_prod['title'],
                        'douyin_price': source_prod['price'],
                        'douyin_url': source_prod['url'],
                        'douyin_sales': source_prod.get('sales', 0),
                        'growth_rate': source_prod.get('growth_rate', ''),
                        'pdd_price': pdd_prod['price'],
                        'pdd_urls': [pdd_prod['url']],  # 可以有多个
                        'discount_rate': f"{price_diff:.1%}",
                        'similarity': f"{similarity:.1%}",
                        'image_url': source_prod.get('image_url', '')
                    })
                    break  # 找到一个就够了
        
        return jsonify({
            'success': True,
            'data': matched_results,
            'total': len(matched_results)
        })
    
    except Exception as e:
        log_request(client_id, request.remote_addr, 'intelligent_selection', False, str(e))
        return jsonify({'success': False, 'error': str(e)}), 500


def scrape_source_platform(category, timerange, count, growth_threshold, allow_official):
    """
    从源平台（抖音/淘宝）爬取商品
    这里是服务器端的核心爬虫逻辑
    """
    # TODO: 实现真实的爬虫逻辑
    # 1. 使用Selenium打开抖音/淘宝
    # 2. 输入类目搜索
    # 3. 根据时间段筛选
    # 4. 获取销量数据，计算增长率
    # 5. 过滤官方/自营（如果需要）
    
    # 示例返回（实际应该是爬取的真实数据）
    return [
        {
            'title': '夏季新款连衣裙女2024流行宽松显瘦气质长裙',
            'price': 128.00,
            'url': 'https://xxx.douyin.com/product/123',
            'sales': 5000,
            'growth_rate': '35%',
            'image_url': 'https://xxx.com/img1.jpg'
        }
    ]


def search_pinduoduo(keyword):
    """
    在拼多多搜索商品
    服务器端执行
    """
    # TODO: 实现拼多多搜索爬虫
    # 1. 使用Selenium打开拼多多
    # 2. 搜索关键词
    # 3. 获取前20个商品
    
    return [
        {
            'title': '连衣裙女2024新款夏季显瘦气质长裙',
            'price': 59.00,
            'url': 'https://xxx.pinduoduo.com/goods/456',
            'image_url': 'https://xxx.com/pdd1.jpg'
        }
    ]

# ==================== 授权状态同步API ====================

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """
    检查客户端授权状态（用于启动时同步）
    不使用 @require_auth 装饰器，避免403拦截
    """
    client_id = request.headers.get('X-Client-ID')
    
    if not client_id:
        return jsonify({'success': False, 'error': '缺少客户端ID'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT is_active FROM authorizations WHERE client_id = ? LIMIT 1', (client_id,))
    row = c.fetchone()

    if not row:
        # 未注册也尝试按试用规则判断（不发试用，仅返回未授权）
        conn.close()
        return jsonify({'success': True, 'authorized': False, 'is_active': 0, 'trial_remaining_seconds': 0})

    is_active = row[0]
    trial_left = 0
    if is_active != 1:
        # 查是否有有效试用（取最近一条）
        c.execute('''SELECT trial_expires_at FROM client_access WHERE client_id=? ORDER BY trial_expires_at DESC LIMIT 1''', (client_id,))
        r = c.fetchone()
        if r and r[0]:
            try:
                exp = datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
                left = (exp - datetime.now()).total_seconds()
                trial_left = int(left) if left > 0 else 0
            except Exception:
                pass
    conn.close()
    return jsonify({'success': True, 'authorized': bool(is_active == 1 or trial_left > 0), 'is_active': is_active, 'trial_remaining_seconds': trial_left})


# ==================== 抖店爬虫API（支持验证码交互） ====================

# 全局爬虫实例池（key: client_id, value: scraper_instance）
scraper_pool = {}

from douyin_scraper_v2 import DouyinScraperV2, LoginRequiredException, ElementNotFoundException, NetworkException

# 定时任务：清理超时的爬虫实例
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

def cleanup_stale_scrapers():
    """清理超时的爬虫实例（30分钟无活动）"""
    now = time.time()
    stale_clients = []
    
    for client_id, scraper in scraper_pool.items():
        if hasattr(scraper, 'last_activity'):
            if now - scraper.last_activity > 1800:  # 30分钟
                stale_clients.append(client_id)
    
    for client_id in stale_clients:
        try:
            scraper_pool[client_id].close()
            del scraper_pool[client_id]
            logger.info(f"🧹 清理超时爬虫实例：{client_id}")
        except Exception as e:
            logger.error(f"❌ 清理爬虫实例失败 {client_id}: {e}")

def backup_database():
    """备份数据库"""
    try:
        import shutil
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        backup_file = f"{backup_dir}/authorization_{timestamp}.db"
        
        # 只备份今天的（避免重复备份）
        if not os.path.exists(backup_file):
            shutil.copy2(DB_PATH, backup_file)
            logger.info(f"💾 数据库备份成功: {backup_file}")
            
            # 删除7天前的备份
            for f in os.listdir(backup_dir):
                if f.startswith("authorization_") and f.endswith(".db"):
                    file_path = os.path.join(backup_dir, f)
                    if os.path.getmtime(file_path) < time.time() - 7*86400:
                        os.remove(file_path)
                        logger.info(f"🗑️ 删除旧备份: {f}")
    except Exception as e:
        logger.error(f"❌ 数据库备份失败: {e}")

# 启动定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_stale_scrapers, 'interval', minutes=10)  # 每10分钟清理一次
scheduler.add_job(backup_database, 'cron', hour=3, minute=0)  # 每天凌晨3点备份
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/api/douyin-login-start', methods=['POST'])
@require_auth
def douyin_login_start(auth=None):
    """
    步骤1：开始登录
    客户端发送：邮箱、密码
    服务器返回：需要验证码 / 登录成功 / 出错
    """
    client_id = request.headers.get('X-Client-ID')
    data = request.json
    
    email = data.get('email', 'doudianpuhuo3@163.com')
    password = data.get('password', 'Ping99re.com')
    
    logger.info(f"[抖店登录] 客户端 {client_id} 开始登录，邮箱: {email}")
    
    try:
        logger.info(f"[抖店登录] 正在创建爬虫实例...")
        # 为该客户创建爬虫实例
        scraper = DouyinScraperV2(headless=True)
        
        logger.info(f"[抖店登录] 正在初始化浏览器...")
        scraper.init_driver()
        
        logger.info(f"[抖店登录] 正在执行登录...")
        # 开始登录
        status, message = scraper.start_login(email, password)
        
        logger.info(f"[抖店登录] 登录结果: status={status}, message={message}")
        
        # 保存爬虫实例到池中
        scraper_pool[client_id] = scraper
        
        return jsonify({
            'success': True,
            'status': status,  # 'need_code' / 'success' / 'error'
            'message': message
        })
    
    except Exception as e:
        logger.error(f"[抖店登录] 登录失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'登录失败: {str(e)}'
        }), 500


@app.route('/api/douyin-submit-code', methods=['POST'])
@require_auth
def douyin_submit_code(auth=None):
    """
    步骤2：提交验证码
    客户端发送：验证码
    服务器返回：登录成功 / 验证码错误
    """
    client_id = request.headers.get('X-Client-ID')
    data = request.json
    code = data.get('code')
    
    if not code:
        return jsonify({
            'success': False,
            'error': '验证码不能为空'
        }), 400
    
    # 从池中获取爬虫实例
    scraper = scraper_pool.get(client_id)
    if not scraper:
        return jsonify({
            'success': False,
            'error': '会话已过期，请重新登录'
        }), 400
    
    try:
        success, message = scraper.submit_verification_code(code)
        
        if success:
            # 登录成功后跳转到榜单页
            scraper.goto_product_rank()
        
        return jsonify({
            'success': success,
            'message': message
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/douyin-get-options', methods=['POST'])
@require_auth
def douyin_get_options(auth=None):
    """
    步骤3：获取所有可选的榜单选项（用于前端显示）
    注意：必须先登录成功
    """
    client_id = request.headers.get('X-Client-ID')
    
    scraper = scraper_pool.get(client_id)
    if not scraper or scraper.login_status != 'logged_in':
        return jsonify({
            'success': False,
            'error': '请先登录'
        }), 400
    
    try:
        # 确保在榜单页面
        scraper.goto_product_rank()
        
        # 获取所有选项
        options = scraper.get_all_rank_options()
        
        return jsonify({
            'success': True,
            'options': options
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/douyin-scrape', methods=['POST'])
@require_auth
def douyin_scrape(auth=None):
    """
    步骤4：根据客户选择的参数爬取商品 - 优化版
    """
    client_id = request.headers.get('X-Client-ID')
    data = request.json
    
    rank_type = data.get('rank_type', '搜索榜')
    time_range = data.get('time_range', '近1天')
    category = data.get('category')
    brand_type = data.get('brand_type')
    limit = int(data.get('limit', 50))
    first_time_only = data.get('first_time_only', False)
    top_n = int(data.get('top_n', 0))
    
    scraper = scraper_pool.get(client_id)
    if not scraper:
        return jsonify({
            'success': False,
            'error_type': 'auth',
            'error': '会话已过期，请重新登录'
        }), 400
    
    if scraper.login_status != 'logged_in':
        return jsonify({
            'success': False,
            'error_type': 'auth',
            'error': '请先完成登录'
        }), 400
    
    try:
        # 选择选项
        scraper.select_options(
            rank_type=rank_type,
            time_range=time_range,
            category=category,
            brand_type=brand_type
        )
        
        # 获取商品
        products = scraper.get_products(limit=limit, first_time_only=first_time_only)
        
        # 如果指定了前N名，则截取
        if top_n > 0:
            products = products[:top_n]
        
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })
    
    except LoginRequiredException as e:
        logger.warning(f"❌ 需要登录: {client_id}")
        return jsonify({
            'success': False,
            'error_type': 'auth',
            'error': '登录已过期，请重新登录'
        }), 401
    
    except ElementNotFoundException as e:
        logger.error(f"❌ 元素定位失败: {client_id}, {e}")
        return jsonify({
            'success': False,
            'error_type': 'scraper',
            'error': '页面结构已变化，请联系客服更新程序'
        }), 500
    
    except NetworkException as e:
        logger.error(f"❌ 网络错误: {client_id}, {e}")
        return jsonify({
            'success': False,
            'error_type': 'network',
            'error': '网络连接失败，请检查网络后重试'
        }), 500
    
    except Exception as e:
        logger.error(f"❌ 爬取异常: {client_id}, {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error_type': 'unknown',
            'error': f'系统错误：{str(e)}'
        }), 500


@app.route('/api/douyin-screenshot', methods=['POST'])
@require_auth
def douyin_screenshot(auth=None):
    """
    获取当前页面截图（用于前端实时显示）
    前端可以每2-3秒轮询一次
    """
    client_id = request.headers.get('X-Client-ID')
    
    scraper = scraper_pool.get(client_id)
    if not scraper:
        return jsonify({
            'success': False,
            'error': '未找到会话，请先登录'
        }), 400
    
    try:
        status_info = scraper.get_current_status()
        
        return jsonify({
            'success': True,
            'login_status': status_info['status'],
            'current_url': status_info['current_url'],
            'screenshot': status_info['screenshot']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/douyin-cleanup', methods=['POST'])
@require_auth
def douyin_cleanup(auth=None):
    """清理爬虫实例（客户端关闭时调用）"""
    client_id = request.headers.get('X-Client-ID')
    
    scraper = scraper_pool.get(client_id)
    if scraper:
        scraper.close()
        del scraper_pool[client_id]
    
    return jsonify({'success': True})


if __name__ == '__main__':
    init_db()
    logger.info("============================================================")
    logger.info("智能选品系统 - 服务器端")
    logger.info("============================================================")
    logger.info(f"数据库路径: {os.path.abspath(DB_PATH)}")
    logger.info(f"启动时间: {get_beijing_time()}")
    logger.info(f"管理后台: http://127.0.0.1:5000/admin/login")
    logger.info("============================================================")
    app.run(host='0.0.0.0', port=5000, debug=False)

