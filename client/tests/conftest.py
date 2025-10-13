"""
pytest配置和共享fixtures
"""
import pytest
import os
import sys
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch

# 将父目录添加到路径，以便导入主程序模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope='session', autouse=True)
def mock_gui_modules():
    """全局Mock GUI模块，确保无GUI环境也能运行测试"""
    gui_mocks = {
        'tkinter': MagicMock(),
        'tkinter.ttk': MagicMock(),
        'tkinter.messagebox': MagicMock(),
        'tkinter.filedialog': MagicMock(),
        'customtkinter': MagicMock(),
    }
    
    # 保存原有模块引用
    original_modules = {name: sys.modules.get(name) for name in gui_mocks}
    
    # 注入Mock模块
    sys.modules.update(gui_mocks)
    
    yield
    
    # 测试结束后恢复
    for name, original_mod in original_modules.items():
        if original_mod is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original_mod


# 全局自动 Mock GUI 依赖，避免在无图形环境导入失败
@pytest.fixture(autouse=True)
def mock_gui_env():
    mocks = {
        'tkinter': MagicMock(),
        'tkinter.ttk': MagicMock(),
        'tkinter.messagebox': MagicMock(),
        'tkinter.filedialog': MagicMock(),
        'customtkinter': MagicMock(),
    }
    original = {name: sys.modules.get(name) for name in mocks}
    sys.modules.update(mocks)
    try:
        yield
    finally:
        for name, mod in original.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod


@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            'client_id': 'test_client_123',
            'is_active': 1,
            'douyin_logged_in': False
        }
        json.dump(config, f)
        temp_path = f.name
    
    yield temp_path
    
    # 清理
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def temp_config_client_json(tmp_path):
    """创建临时config_client.json文件"""
    config_file = tmp_path / "config_client.json"
    config_file.write_text(json.dumps({
        "server_url": "http://test.example.com:5000"
    }))
    return str(config_file)


@pytest.fixture
def mock_requests():
    """Mock requests模块"""
    with patch('requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_customtkinter():
    """Mock customtkinter避免创建真实GUI"""
    mock_ctk = MagicMock()
    with patch.dict('sys.modules', {'customtkinter': mock_ctk}):
        yield mock_ctk


@pytest.fixture
def sample_api_responses():
    """提供标准API响应样本"""
    return {
        'register_success': {
            'success': True,
            'client_id': 'test_client_123',
            'is_active': 0,
            'message': '注册成功'
        },
        'register_trial': {
            'success': True,
            'client_id': 'test_client_456',
            'is_active': 0,
            'trial_hours_left': 1
        },
        'auth_403': {
            'success': False,
            'show_popup': True,
            'reason': 'trial_expired'
        },
        'login_need_code': {
            'success': True,
            'status': 'need_code',
            'message': '需要验证码'
        },
        'login_success': {
            'success': True,
            'status': 'success',
            'message': '登录成功'
        },
        'scrape_success': {
            'success': True,
            'products': [
                {'title': '测试商品1', 'price': 99.9},
                {'title': '测试商品2', 'price': 199.9}
            ]
        }
    }


@pytest.fixture(autouse=True)
def reset_env_vars():
    """每个测试前后重置环境变量"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

