# 测试文档

## 测试结构

```
tests/
├── test_utils.py          # 工具函数单元测试
├── test_config.py         # 配置管理测试
├── test_api_client.py     # API客户端集成测试
├── test_workflows.py      # 工作流测试
└── conftest.py           # pytest配置

tests_exe/
├── test_exe_startup.py    # EXE启动测试
├── test_exe_login.py      # 登录流程测试
├── test_exe_navigation.py # 导航测试
└── conftest.py           # 端到端测试配置
```

## 运行测试

### 在Linux/WSL环境（无GUI）

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-mock

# 运行所有单元测试
cd client
pytest tests/ -v

# 运行特定测试
pytest tests/test_utils.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

### 在Windows环境（含GUI）

```bash
# 运行所有测试（包括GUI）
cd client
python -m pytest tests/ tests_exe/ -v

# 仅运行端到端测试
python -m pytest tests_exe/ -v
```

## 测试策略

### 1. 单元测试
- **目标**: 测试独立函数逻辑
- **覆盖**: 工具函数、数据处理、配置管理
- **环境**: Linux/Windows均可
- **文件**: `tests/test_*.py`

### 2. 集成测试
- **目标**: 测试模块间交互
- **覆盖**: API通信、配置加载、数据流转
- **环境**: Linux/Windows均可
- **文件**: `tests/test_api_client.py`

### 3. 端到端测试
- **目标**: 模拟真实用户操作
- **覆盖**: 完整用户流程、GUI交互
- **环境**: 仅Windows（需要CustomTkinter）
- **文件**: `tests_exe/test_*.py`

## 测试覆盖范围

### 已覆盖功能
- ✅ 配置文件读写
- ✅ 硬件ID生成
- ✅ 服务器地址解析
- ✅ 日志系统
- ✅ Excel导出

### 待完善功能
- ⏳ GUI组件测试
- ⏳ 登录流程测试
- ⏳ 选品功能测试
- ⏳ 截图显示测试

## CI/CD集成

GitHub Actions会在每次推送时自动运行测试：

1. **单元测试** - Ubuntu环境
2. **集成测试** - Ubuntu环境
3. **代码质量检查** - flake8
4. **打包测试** - Windows环境（build-windows-exe.yml）

## 添加新测试

1. 在 `tests/` 目录创建 `test_*.py` 文件
2. 使用pytest框架编写测试
3. 提交代码触发CI

示例：
```python
def test_example():
    assert 1 + 1 == 2
```

## 问题排查

### 测试失败
1. 查看GitHub Actions日志
2. 本地运行 `pytest tests/ -v`
3. 检查依赖是否完整

### 覆盖率低
1. 运行 `pytest --cov-report=html`
2. 查看 `htmlcov/index.html`
3. 针对性添加测试用例

