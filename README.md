# Iron Bank API 管理系统

一个基于 Flask 的现代化 API 管理系统，提供完整的用户认证、权限管理和平台管理功能。

## 功能特性

### 1. 用户认证系统
- 支持用户名/邮箱登录
- 安全的密码加密存储
- 用户状态管理（活跃/禁用）
- 记住登录状态
- 最后登录时间记录

### 2. 权限管理系统
- 多级权限控制
  - 管理员权限
  - 普通用户权限
  - 应用权限
  - 菜单权限
- 灵活的权限分配机制
- 基于角色的访问控制

### 3. 平台管理功能
- 平台信息管理
  - 平台基本信息配置
  - 平台状态控制
  - 平台密钥管理
- 平台菜单配置
  - 自定义菜单项
  - 菜单权限分配
  - 菜单状态控制

### 4. 用户管理功能
- 用户信息管理
  - 基本信息维护
  - 状态控制
  - 角色分配
- 权限管理
  - 应用权限分配
  - 菜单权限配置
  - 权限继承关系

### 5. 系统功能
- 响应式界面设计
- 现代化 UI 组件
- 用户友好的交互体验
- 合理的导航结构
- 完善的错误处理

## 技术栈

- 后端框架：Flask
- 数据库：MongoDB
- 前端框架：Bootstrap 5
- 认证：Flask-Login
- 表单处理：Flask-WTF
- 密码加密：Werkzeug Security

## 安装说明

1. 克隆项目
```bash
git clone [项目地址]
cd iron-bank-api
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量
```

5. 初始化数据库
```bash
flask db init
flask db migrate
flask db upgrade
```

6. 运行项目
```bash
flask run
```

## 项目结构

```
iron-bank-api/
├── app/
│   ├── models/         # 数据模型
│   ├── services/       # 业务逻辑
│   ├── templates/      # 页面模板
│   ├── static/         # 静态资源
│   └── utils/          # 工具函数
├── config/             # 配置文件
├── tests/              # 测试用例
├── venv/               # 虚拟环境
├── .env                # 环境变量
├── .gitignore          # Git 忽略文件
├── requirements.txt    # 项目依赖
└── README.md           # 项目说明
```

## 使用说明

1. 管理员账号
   - 默认管理员账号：admin
   - 默认密码：admin123
   - 首次登录后请立即修改密码

2. 用户管理
   - 创建新用户
   - 分配用户权限
   - 管理用户状态

3. 平台管理
   - 创建新平台
   - 配置平台信息
   - 管理平台密钥
   - 设置平台菜单

4. 权限配置
   - 设置角色权限
   - 分配菜单权限
   - 配置应用权限

## 开发团队

- 开发者：[您的名字]
- 联系方式：[您的邮箱]

## 许可证

本项目采用 MIT 许可证 