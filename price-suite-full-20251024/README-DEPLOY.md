# 云服务器部署说明

## 快速开始

### 1. 上传项目
```bash
# 本地执行
scp -r price-suite-full-20251024 root@服务器IP:/opt/
```

### 2. 部署
```bash
# 服务器执行
cd /opt/price-suite-full-20251024
./deploy.sh
```

### 3. 启动
```bash
cd server
python3 app.py
```

## 远程开发

### Cursor SSH连接
1. Cursor → Remote-SSH
2. 连接到服务器
3. 打开: /opt/price-suite-full-20251024
4. 开始开发！

## 项目结构
```
price-suite-full-20251024/
├── client/          # 客户端代码（可在服务器开发）
├── server/          # 服务器端代码
├── rpa/             # RPA模块
├── docs/            # 完整文档
├── scripts/         # 工具脚本
├── .github/         # CI/CD配置
└── deploy.sh        # 一键部署脚本
```

## 开发流程
1. Cursor远程编辑代码
2. 测试: python3 server/app.py
3. 客户端: GitHub Actions自动打包EXE
4. 提交: git commit && git push
