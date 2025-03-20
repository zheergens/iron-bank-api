# 用户中心接入指南

## 概述

本文档介绍如何将您的应用接入到用户中心认证系统，实现统一的用户认证和授权管理。用户中心提供基于 OAuth 2.0 的认证流程，支持单点登录(SSO)功能。

## 接入流程

### 1. 在用户中心注册您的应用

1. 登录用户中心管理后台
2. 导航至「平台授权」菜单
3. 点击「添加平台」按钮
4. 填写平台信息：
   - 平台名称：您的应用名称
   - 重定向 URL：您应用的回调地址，例如 `https://yourapplication.com/auth/callback`
   - 应用描述：简要描述您的应用功能
5. 提交后，系统将生成以下信息：
   - 客户端 ID (client_id)
   - 客户端密钥 (client_secret)

**请妥善保管客户端密钥，不要泄露给第三方。**

### 2. 实现认证流程

#### 2.1 引导用户到认证页面

当用户需要登录时，将其重定向到用户中心的授权页面： 

```
https://<用户中心域名>/auth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_CALLBACK_URL&response_type=code&scope=profile&state=RANDOM_STATE
```

参数说明：
- `client_id`: 您的客户端 ID
- `redirect_uri`: 必须与您注册时提供的重定向 URL 完全匹配
- `response_type`: 固定值 `code`
- `scope`: 请求的权限范围，可选值包括 `profile`、`email` 等
- `state`: 随机字符串，用于防止 CSRF 攻击，回调时会原样返回

#### 2.2 处理回调请求

用户授权后，系统会将用户重定向到您指定的回调 URL，并附带授权码：

```
https://yourapplication.com/auth/callback?code=AUTHORIZATION_CODE&state=RANDOM_STATE
```

您需要：
1. 验证 `state` 参数是否与发送时一致
2. 使用授权码获取访问令牌

#### 2.3 获取访问令牌

向用户中心的令牌端点发送 POST 请求：

```http
POST /auth/token HTTP/1.1
Host: <用户中心域名>
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=AUTHORIZATION_CODE&redirect_uri=YOUR_CALLBACK_URL&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

成功后，您将收到包含访问令牌的 JSON 响应：

```json
{
  "access_token": "ACCESS_TOKEN",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN"
}
```

#### 2.4 获取用户信息

使用访问令牌获取用户信息：

```http
GET /api/user/profile HTTP/1.1
Host: <用户中心域名>
Authorization: Bearer ACCESS_TOKEN
```

响应示例：

```json
{
  "id": "user_id",
  "username": "example_user",
  "email": "user@example.com",
  "name": "用户姓名"
}
```

### 3. 刷新访问令牌

访问令牌过期时，可使用刷新令牌获取新的访问令牌：

```http
POST /auth/token HTTP/1.1
Host: <用户中心域名>
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=REFRESH_TOKEN&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

## 本地开发环境配置

本地开发环境使用以下配置：

- 用户中心地址：`http://localhost:5000`
- 回调 URL 示例：`http://localhost:5001/auth/callback`

## 示例代码

### Python (Flask) 实现示例

```python
from flask import Flask, redirect, request, session, url_for
import requests
import os
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 配置信息
AUTH_SERVER = 'http://localhost:5000'
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'http://localhost:5001/auth/callback'

@app.route('/login')
def login():
    # 生成随机state并存储在会话中
    state = secrets.token_hex(16)
    session['oauth_state'] = state
    
    # 构建授权URL
    auth_url = f"{AUTH_SERVER}/auth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=profile&state={state}"
    return redirect(auth_url)

@app.route('/auth/callback')
def callback():
    # 验证state参数
    if request.args.get('state') != session.get('oauth_state'):
        return '状态验证失败，可能存在CSRF攻击', 403
    
    # 获取授权码
    code = request.args.get('code')
    
    # 交换访问令牌
    token_response = requests.post(f"{AUTH_SERVER}/auth/token", data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    
    if token_response.status_code != 200:
        return '获取访问令牌失败', 400
        
    token_data = token_response.json()
    access_token = token_data['access_token']
    
    # 获取用户信息
    user_response = requests.get(f"{AUTH_SERVER}/api/user/profile", headers={
        'Authorization': f"Bearer {access_token}"
    })
    
    if user_response.status_code != 200:
        return '获取用户信息失败', 400
        
    user_data = user_response.json()
    
    # 在这里处理用户登录逻辑
    session['user'] = user_data
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return f"欢迎, {session['user']['username']}!"

if __name__ == '__main__':
    app.run(port=5001, debug=True)
```

## 常见问题

1. **重定向 URL 不匹配**：确保注册应用时填写的重定向 URL 与实际使用时完全一致，包括 http/https 前缀和任何尾部斜杠。

2. **授权失败**：检查客户端 ID 和客户端密钥是否正确。

3. **无法获取用户信息**：确认访问令牌有效且未过期，并检查授权请求中的权限范围是否包含所需信息。

4. **令牌过期**：实现令牌刷新逻辑，及时刷新过期的访问令牌。

## 联系支持

如遇到接入问题，请联系系统管理员获取支持。 