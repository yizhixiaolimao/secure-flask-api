# Secure Flask REST API Lab

这是一个可直接用于课程作业的 Python/Flask 示例项目。它实现了 JWT 登录、受保护的数据接口、创建文章接口、SQLite 持久化、Argon2id 密码哈希、SQL 注入防护、XSS 输出编码、自动测试，以及 GitHub Actions 中的 SAST/SCA 扫描。

## 1. 三个作业接口

| 方法与路径 | 是否需要 JWT | 用途 |
| --- | --- | --- |
| `POST /auth/login` | 否 | 验证用户名/密码，成功后签发 15 分钟 JWT |
| `GET /api/data` | 是 | 返回最新的文章列表 |
| `POST /api/posts` | 是 | 自选的第三个接口：创建一篇文章 |

另外提供 `GET /health`，用于确认服务是否启动，不算作三个业务接口之一。

## 2. 项目结构

```text
secure-flask-api/
├── app/
│   ├── routes/
│   │   ├── auth.py             # 登录接口
│   │   └── api.py              # 受保护的数据/文章接口
│   ├── __init__.py             # 应用工厂、安全响应头、CLI 命令
│   ├── config.py               # 环境变量配置
│   ├── errors.py               # 统一 JSON/JWT 错误处理
│   ├── extensions.py           # SQLAlchemy、JWT、限流器
│   ├── models.py               # User 和 Post 模型
│   ├── security.py             # Argon2、JWT 中间件、XSS 输出编码
│   └── validation.py           # 输入类型、长度和格式验证
├── tests/                      # pytest 自动测试
├── postman/                    # 可直接导入的 Postman Collection
├── docs/                       # Vulhub/CVE 分析记录模板
├── .github/workflows/ci.yml    # 测试、Bandit、pip-audit、OWASP SCA
├── .env.example                # 非敏感配置模板
├── requirements.txt            # 运行依赖
├── requirements-dev.txt        # 测试和安全工具
├── pyproject.toml              # pytest/coverage/Bandit 配置
└── wsgi.py                     # Flask 入口
```

## 3. 在 Ubuntu/虚拟机中运行

如果没有 Python 环境，先安装：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

进入项目并创建独立虚拟环境：

```bash
cd secure-flask-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

复制配置文件并生成随机 JWT 密钥：

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
```

将第二条命令输出的随机值写入 `.env` 的 `JWT_SECRET_KEY=` 后面。`.env` 已被 `.gitignore` 排除，不能提交到 GitHub。

初始化数据库并创建登录用户：

```bash
flask --app wsgi init-db
flask --app wsgi create-user --username alice
```

第二条命令会安全地提示输入并确认密码；密码至少 12 个字符，而且不会出现在 shell 历史中。

启动服务：

```bash
flask --app wsgi run --debug
```

开发地址为 `http://127.0.0.1:5000`。`--debug` 只能用于本地开发，不能用于公网部署。

## 4. 使用 curl 测试

### 4.1 无 Token 访问必须被拒绝

```bash
curl -i http://127.0.0.1:5000/api/data
```

应返回 `HTTP/1.1 401 UNAUTHORIZED` 和 `authorization_required`。

### 4.2 登录并取得 JWT

```bash
curl -i -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"alice","password":"你创建用户时输入的密码"}'
```

复制响应中的 `access_token`。之后设置一个临时 shell 变量：

```bash
TOKEN='把 access_token 粘贴到这里'
```

### 4.3 携带 Token 访问数据

```bash
curl -i http://127.0.0.1:5000/api/data \
  -H "Authorization: Bearer $TOKEN"
```

### 4.4 创建文章（第三个接口）

```bash
curl -i -X POST http://127.0.0.1:5000/api/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My first post","content":"Hello secure API"}'
```

也可以把 `postman/Secure-Flask-API.postman_collection.json` 导入 Postman，在 Collection Variables 中填写 `login` 和 `password`。先运行 Login，请求后的脚本会自动保存 JWT。

## 5. 自动测试与本地扫描

```bash
python -m pytest --cov=app --cov-report=term-missing
```

运行 Bandit SAST，并生成可截图的 HTML 报告：

```bash
mkdir -p reports
bandit -r app -f html -o reports/bandit-report.html
```

运行 Python 依赖审计：

```bash
pip-audit -r requirements.txt \
  --format=json \
  --output=reports/pip-audit.json
```

OWASP Dependency-Check 已配置在 GitHub Actions 中，因此不要求本机安装 Java 或成功拉取 Docker 镜像。

## 6. Git 与 GitHub

在项目根目录执行（先在 GitHub 创建一个空仓库）：

```bash
git init
git add .
git commit -m "Build secure Flask REST API"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/secure-flask-api.git
git push -u origin main
```

每次 `push` 或创建 Pull Request 时，`.github/workflows/ci.yml` 自动执行：

1. pytest 功能/安全测试和覆盖率门槛；
2. Bandit 静态代码安全测试（SAST）；
3. pip-audit Python 依赖审计；
4. OWASP Dependency-Check 软件成分分析（SCA）；
5. 上传 Bandit HTML、pip-audit JSON 和 Dependency-Check HTML 报告。

## 7. 作业要求与代码对应关系

| 作业要求 | 本项目实现 |
| --- | --- |
| SQL 注入防护 | `select(...).where(...)` 和 SQLAlchemy ORM 参数绑定；没有拼接 SQL |
| XSS 防护 | `escape_text()` 对所有用户可控输出进行 HTML 实体编码；JSON-only API 以及 CSP/nosniff 响应头作为额外防线 |
| 密码不能明文存储 | `argon2-cffi` 的 Argon2id；每个密码自动使用随机 salt |
| JWT | 登录成功后签发 15 分钟 HS256 Token；密钥只从 `.env` 读取 |
| JWT 中间件 | `@auth_required` 内部统一执行 `verify_jwt_in_request()` |
| 认证失败保护 | 相同的错误消息、未知用户 dummy hash 校验、登录接口每 IP 每分钟 5 次限流 |
| 输入安全 | JSON 类型、允许字符、字段长度、请求总大小和允许字段白名单 |
| SAST | Bandit 扫描全部严重度；发现问题即使构建失败，并保存 HTML 报告 |
| SCA | OWASP Dependency-Check（作业要求）和 pip-audit（Python 补充），CVSS >= 7 时失败 |

### 为什么 ORM 能防 SQLi？

登录查询把 `username` 作为参数绑定到 SQL 语句，而不是把用户输入拼接到 SQL 文本中。即使输入包含 `' OR '1'='1`，数据库也只会把它当成普通字符串值。测试 `test_sql_injection_string_cannot_bypass_login` 会自动验证这一点。

### 为什么 API 仍然处理 XSS？

正确的 `application/json` 响应本身不会作为 HTML 执行，但前端可能错误地把 API 字段传给 `innerHTML`。因此本项目在序列化文章时把 `<`、`>`、引号等转成 HTML 实体，并同时返回严格 CSP 和 `nosniff`。测试中包含 `<script>` 与 `<img onerror>` 样例。

### JWT 不等于加密

JWT 的负载通常只是 Base64URL 编码，客户端能够读取，因此 Token 内只放用户 ID 和用户名，不放密码或隐私数据。JWT 的签名用于防篡改；15 分钟过期时间用于缩短泄漏后的风险窗口。

## 8. 建议截图

提交作业时建议保留以下截图：

1. Postman 登录成功并获得 JWT；
2. 不带 Token 请求 `/api/data` 返回 401；
3. 带 Token 请求 `/api/data` 返回 200；
4. GitHub Actions 的两个 job 均为绿色；
5. Bandit HTML 报告显示无中高风险问题；
6. Dependency-Check HTML 报告或 pip-audit 日志显示没有达到失败阈值的漏洞。

## 9. 教学项目与生产系统的边界

SQLite 和 `memory://` 限流适合单机实验。生产环境应使用 PostgreSQL、数据库迁移工具、Redis 共享限流、HTTPS、正式 WSGI 服务、集中日志、密钥管理和 JWT 吊销/刷新机制。不要把 Flask debug server 直接暴露到公网。

Vulhub 的 CVE 复现属于独立的受控实验，不应与这个安全 API 在同一个公开网络运行。`docs/CVE-ANALYSIS-TEMPLATE.md` 提供了报告结构；具体复现命令要依据老师指定的 CVE/Vulhub 场景填写。

