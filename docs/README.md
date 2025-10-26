# 📚 智能选品系统 - 文档中心

**版本**: v10.10.5  
**更新时间**: 2025-10-26

---

## 📖 文档导航

### 🚀 快速开始

| 文档 | 说明 | 位置 |
|------|------|------|
| [🎉部署完成-立即使用](./deployment/🎉部署完成-立即使用.md) | **新手必看！** 快速开始指南 | `docs/deployment/` |
| [系统访问验证报告](./deployment/系统访问验证报告.md) | 验证所有功能是否正常 | `docs/deployment/` |

### 🔧 部署指南

| 文档 | 适用场景 | 位置 |
|------|----------|------|
| [宝塔面板部署指南](./deployment/宝塔面板部署指南.md) | 使用宝塔面板部署 | `docs/deployment/` |
| [域名配置说明](./deployment/域名配置说明.md) | Cloudflare Tunnel配置 | `docs/deployment/` |
| [完整项目迁移指南](./deployment/完整项目迁移指南.md) | 项目迁移和备份 | `docs/deployment/` |

### 📝 开发文档

| 文档 | 说明 | 位置 |
|------|------|------|
| [API文档](./api/) | 后端API接口文档 | `docs/api/` |
| [前端开发指南](./guides/) | 客户端开发文档 | `docs/guides/` |

---

## 🌐 访问地址

### 生产环境（推荐）
```
https://price.deepopenai.store/admin/login
```

### 开发环境
```
http://localhost:5000/admin/login
```

**默认密码**: `admin123`

---

## 🔑 核心功能

- ✅ 商品智能爬取（抖音/淘宝）
- ✅ AI智能匹配
- ✅ 价格自动对比
- ✅ 数据分析报表
- ✅ 自动铺货（RPA）
- ✅ 授权验证管理

---

## 📂 文档目录结构

```
docs/
├── README.md                    # 本文档
├── deployment/                  # 部署相关文档
│   ├── 🎉部署完成-立即使用.md
│   ├── 系统访问验证报告.md
│   ├── 宝塔面板部署指南.md
│   ├── 域名配置说明.md
│   └── 完整项目迁移指南.md
├── api/                         # API文档
│   └── (待补充)
└── guides/                      # 开发指南
    └── (待补充)
```

---

## 🔗 相关链接

- **项目主页**: `/www/wwwroot/ price-suite`
- **客户端**: `/www/wwwroot/ price-suite/client`
- **服务器**: `/www/wwwroot/ price-suite/server`
- **GitHub**: (请配置)

---

## 💡 快速问答

### Q: 如何开始使用？
A: 查看 [🎉部署完成-立即使用](./deployment/🎉部署完成-立即使用.md)

### Q: 域名打不开怎么办？
A: 查看 [域名配置说明](./deployment/域名配置说明.md)

### Q: 如何配置客户端连接服务器？
A: 修改 `client/config_client.json` 中的 `server_url`

### Q: 忘记管理密码？
A: 默认密码是 `admin123`，登录后立即修改

---

## 📞 技术支持

如有问题，请查看相应文档或查看日志：
```bash
# 服务器日志
tail -f "/www/wwwroot/ price-suite/server/app.log"

# Tunnel日志
journalctl -u cloudflared -f
```

---

**更新日志**: 
- 2025-10-26: 创建文档中心，整理所有文档
- 2025-10-23: v10.10.5 版本发布

**维护者**: Price Suite Team
