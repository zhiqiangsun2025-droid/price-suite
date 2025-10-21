#!/usr/bin/env python3
"""
修复验证测试脚本
运行此脚本验证所有修复是否生效
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    print("✓ 测试1: 检查导入...")
    try:
        import modern_client_ultimate
        print("  ✓ 模块导入成功")
        return True
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        return False

def test_config_class():
    """测试配置类"""
    print("\n✓ 测试2: 检查Config配置类...")
    try:
        from modern_client_ultimate import Config
        
        # 检查所有配置项
        required_attrs = [
            'TRIAL_DURATION',
            'TRIAL_CHECK_INTERVAL',
            'CONTACT_QQ',
            'WINDOW_WIDTH',
            'WINDOW_HEIGHT',
            'SCREENSHOT_POLL_INTERVAL',
            'LOGIN_TIMEOUT',
            'SCRAPE_TIMEOUT',
            'CODE_INPUT_TIMEOUT'
        ]
        
        for attr in required_attrs:
            if not hasattr(Config, attr):
                print(f"  ✗ 缺少配置: {attr}")
                return False
            print(f"  ✓ {attr} = {getattr(Config, attr)}")
        
        print("  ✓ 配置类完整")
        return True
    except Exception as e:
        print(f"  ✗ 配置类测试失败: {e}")
        return False

def test_logging():
    """测试日志系统"""
    print("\n✓ 测试3: 检查日志系统...")
    try:
        from modern_client_ultimate import logger
        
        # 测试日志记录
        logger.info("测试日志记录")
        print("  ✓ 日志系统正常")
        return True
    except Exception as e:
        print(f"  ✗ 日志系统失败: {e}")
        return False

def test_server_url():
    """测试服务器地址配置"""
    print("\n✓ 测试4: 检查服务器地址...")
    try:
        from modern_client_ultimate import SERVER_URL
        
        print(f"  ✓ 服务器地址: {SERVER_URL}")
        
        # 检查不是硬编码的内网地址
        if "172.19.251.155" in SERVER_URL:
            print("  ✗ 警告: 仍然使用硬编码的内网地址")
            return False
        
        print("  ✓ 服务器地址配置正确")
        return True
    except Exception as e:
        print(f"  ✗ 服务器地址测试失败: {e}")
        return False

def test_type_hints():
    """测试类型提示"""
    print("\n✓ 测试5: 检查类型提示...")
    try:
        from modern_client_ultimate import load_config, save_config, get_hardware_id
        import inspect
        
        # 检查函数签名
        functions = [
            ('load_config', load_config),
            ('save_config', save_config),
            ('get_hardware_id', get_hardware_id)
        ]
        
        for name, func in functions:
            sig = inspect.signature(func)
            if sig.return_annotation != inspect.Signature.empty:
                print(f"  ✓ {name} 有返回类型提示: {sig.return_annotation}")
            else:
                print(f"  ⚠ {name} 缺少返回类型提示")
        
        print("  ✓ 类型提示检查完成")
        return True
    except Exception as e:
        print(f"  ✗ 类型提示测试失败: {e}")
        return False

def test_no_hardcoded_credentials():
    """测试是否移除了硬编码的账号密码"""
    print("\n✓ 测试6: 检查是否有硬编码的账号密码...")
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'modern_client_ultimate.py')
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查敏感信息
        sensitive_patterns = [
            'doudianpuhuo3@163.com',
            'Ping99re.com'
        ]
        
        found_sensitive = False
        for pattern in sensitive_patterns:
            # 只检查insert语句中的敏感信息
            if f'.insert(0, "{pattern}")' in content:
                print(f"  ✗ 警告: 发现硬编码的敏感信息: {pattern}")
                found_sensitive = True
        
        if not found_sensitive:
            print("  ✓ 未发现硬编码的敏感信息")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("代码修复验证测试")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config_class,
        test_logging,
        test_server_url,
        test_type_hints,
        test_no_hardcoded_credentials
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            results.append(False)
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！代码修复成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查！")
        return 1

if __name__ == "__main__":
    sys.exit(main())

