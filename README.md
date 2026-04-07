# Learning Community Backend

学习社区后端API服务 v2

## 项目结构

```
learning-community-backend/
├── app/                    # 主应用文件夹
│   ├── models/            # 数据库模型
│   │   ├── user.py        # 用户模型
│   │   ├── file.py        # 文件模型
│   │   ├── courseware.py  # 教案课件模型
│   │   ├── textbook.py    # 教材模型
│   │   └── ...           # 其他模型
│   ├── routers/           # 蓝图/API端点
│   │   ├── auth.py        # 认证相关API
│   │   ├── users.py       # 用户管理API
│   │   ├── files.py       # 文件存储API
│   │   ├── coursewares.py # 教案课件API
│   │   ├── textbooks.py   # 教材API
│   │   └── ...           # 其他API
│   └── utils/             # 工具类
│       └── office_converter.py  # Office转PDF工具
├── libs/                  # 工具/可复用库
│   ├── db.py             # 数据库连接
│   ├── jwt_auth.py       # JWT认证工具
│   └── response.py       # 统一返回格式
├── storage/               # 文件存储目录
│   ├── images/           # 图片文件
│   ├── videos/           # 视频文件
│   ├── documents/        # 文档文件
│   ├── pdfs/            # PDF文件（自动转换）
│   └── others/          # 其他文件
├── test/                  # 测试文件夹
│   └── test_auth.py      # 认证测试
├── docs/                  # 文档文件夹
│   ├── user.yaml        # OpenAPI文档
│   └── init_database.sql # 数据库初始化脚本
├── config.yaml           # 配置文件
├── app.py                # 主运行程序
└── requirements.txt      # 依赖包列表
```

## 功能特性

- 用户认证（注册、登录、登出）
- JWT Token认证
- 基于角色的权限控制
  - 超级管理员 (ROLE_SUPER_ADMIN = 1)
  - 管理员 (ROLE_ADMIN = 2)
  - 教师 (ROLE_TEACHER = 3)
  - 学生 (ROLE_STUDENT = 4)
- 用户管理（增删改查）
- 文件存储服务
    - 自动判断文件类型：图片、视频、文档、其他
    - 支持所有文件类型上传（最大100MB）
    - 支持图片上传（png, jpg, jpeg, gif, bmp, webp, ico, svg）
    - 支持视频上传（mp4, avi, mov, wmv, flv, mkv, webm, 3gp）
    - 支持文档上传（pdf, doc, docx, xls, xlsx, ppt, pptx, txt, rtf, md）
    - Office 文档自动转换为 PDF（doc, docx, xls, xlsx, ppt, pptx）
    - 文件在线预览（图片、PDF、Office 文档转 PDF 预览）
    - 文件下载、删除、列表查询
    - 文件索引存储在MySQL数据库
    - 支持按类型、关键词、上传者筛选
- 统一的API返回格式 `{code, message, data}`

## 环境要求

- Python 3.7+
- MySQL 5.7+
- LibreOffice（用于 Office 文档自动转 PDF）
  - Windows: C:\Program Files\LibreOffice\program\soffice.exe
  - macOS: /Applications/LibreOffice.app/Contents/MacOS/soffice
  - Linux: 通过包管理器安装 libreoffice
- Conda环境: `learning-community-backend`

## 快速开始

### 1. 激活Conda环境

```bash
conda activate learning-community-backend
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库

编辑 `config.yaml` 文件，修改数据库连接信息：

```yaml
database:
  host: localhost
  port: 3306
  user: your_username
  password: your_password
  database: learning_community
  charset: utf8mb4
```

### 4. 创建数据库

**方法1：使用命令行创建（推荐）**

```bash
# 创建数据库
mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS learning_community CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入表结构和测试数据
mysql -u root -p123456 --default-character-set=utf8mb4 learning_community < docs/init_database.sql
```

**注意：** 请将 `root` 和 `123456` 替换为你实际的MySQL用户名和密码。

**方法2：手动在MySQL客户端中执行**

打开MySQL客户端，执行 `docs/init_database.sql` 文件中的SQL语句。

测试账号（密码都是 `123456`）：
- 超级管理员：admin / 13800138000
- 教师：teacher / 13800138001  
- 学生：student / 13800138002

### 5. 配置数据库连接

编辑 `config.yaml` 文件，修改数据库连接信息：

```yaml
database:
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: learning_community
  charset: utf8mb4
```

### 6. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## API文档

完整的API文档请查看 `docs/user.yaml` 文件。

### API返回格式

所有API接口统一使用以下返回格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 响应数据
  }
}
```

- **code**: 状态码，200表示成功，其他表示失败（400, 401, 403, 404, 500等）
- **message**: 响应消息
- **data**: 响应数据，成功时包含数据，失败时为null

### 主要API端点

**认证相关：**
- `POST /api/v2/auth/register` - 用户注册（用户名、手机号、密码）
- `POST /api/v2/auth/login` - 用户登录（手机号、密码）
- `POST /api/v2/auth/logout` - 用户登出
- `GET /api/v2/auth/me` - 获取当前用户信息

**用户管理：**
- `GET /api/v2/users` - 获取用户列表
- `GET /api/v2/users/<id>` - 获取用户详情
- `POST /api/v2/users` - 创建用户（需要管理员权限）
- `PUT /api/v2/users/<id>` - 更新用户（需要管理员权限）
- `DELETE /api/v2/users/<id>` - 删除用户（需要管理员权限）
- `PUT /api/v2/users/<id>/status` - 切换用户状态（需要管理员权限）

**文件存储：**
- `POST /api/v2/files/upload` - 上传文件（需要登录，后端自动判断文件类型）
- `GET /api/v2/files/<id>` - 获取文件信息
- `GET /api/v2/files/download/<id>` - 下载文件
- `GET /api/v2/files/serve/<id>` - 访问文件（用于在线预览）
- `GET /api/v2/files/<id>/preview` - 获取文件预览 URL（Office 文档返回 PDF URL）
- `GET /api/v2/files/<id>/url` - 获取文件URL
- `GET /api/v2/files` - 获取文件列表（支持按类型、关键词、上传者筛选）
- `DELETE /api/v2/files/<id>` - 删除文件（只能删除自己上传的文件）

**教案课件：**
- `POST /api/v2/coursewares/upload` - 上传教案课件（文档+图片，Office 文档自动转 PDF）
- `GET /api/v2/coursewares` - 获取教案课件列表
- `GET /api/v2/coursewares/<id>` - 获取教案课件详情
- `PUT /api/v2/coursewares/<id>` - 更新教案课件
- `DELETE /api/v2/coursewares/<id>` - 删除教案课件
- `POST /api/v2/coursewares/<id>/like` - 点赞/取消点赞

**教材：**
- `POST /api/v2/textbooks/upload` - 上传教材（文档+图片，Office 文档自动转 PDF）
- `GET /api/v2/textbooks` - 获取教材列表
- `GET /api/v2/textbooks/<id>` - 获取教材详情
- `PUT /api/v2/textbooks/<id>` - 更新教材
- `DELETE /api/v2/textbooks/<id>` - 删除教材
- `POST /api/v2/textbooks/<id>/like` - 点赞/取消点赞

### 文件类型支持

系统支持以下文件类型的上传和预览：

| 类型 | 支持格式 | 最大大小 | 说明 |
|------|---------|---------|------|
| **图片** | png, jpg, jpeg, gif, bmp, webp, ico, svg | 100MB | 支持在线预览 |
| **视频** | mp4, avi, mov, wmv, flv, mkv, webm, 3gp | 100MB | 支持在线播放 |
| **文档** | pdf, doc, docx, xls, xlsx, ppt, pptx, txt, rtf, md | 100MB | Office 文档自动转 PDF |
| **其他** | 其他所有文件类型 | 100MB | 仅支持下载 |

### Office 文档自动转 PDF

- **自动转换**: 上传 Office 文档（doc, docx, xls, xlsx, ppt, pptx）时自动转换为 PDF
- **透明处理**: 转换过程对用户完全透明，无需额外操作
- **失败容错**: 转换失败不影响原文件上传，系统会记录日志
- **预览支持**: 转换后的 PDF 可用于前端在线预览

### 文件预览 API 使用示例

```javascript
// 获取文件预览 URL（Office 文档自动返回 PDF URL）
const response = await fetch('/api/v2/files/123/preview', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
});

const result = await response.json();
// 返回格式：
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "file_id": 123,
    "preview_url": "http://localhost:5000/api/v2/files/serve/456",
    "preview_type": "pdf"  // 或 "image"
  }
}

// 直接使用 preview_url 进行预览
window.open(result.data.preview_url, '_blank');
```

## 测试

运行测试：

```bash
python -m pytest test/
```

或运行单个测试文件：

```bash
python test/test_auth.py
```

## 配置说明

### config.yaml

```yaml
app:
  name: Learning Community Backend
  version: 2.0.0
  debug: true
  host: 0.0.0.0
  port: 5000

database:
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: learning_community
  charset: utf8mb4

jwt:
  secret_key: your_jwt_secret_key_change_this_in-production
  algorithm: HS256
  expiration: 86400

# 文件上传配置
upload:
  max_size: 104857600  # 100MB in bytes

# Office 转 PDF 配置（自动检测 LibreOffice）
# 系统会自动查找以下位置的 LibreOffice：
# - Windows: C:\Program Files\LibreOffice\program\soffice.exe
# - macOS: /Applications/LibreOffice.app/Contents/MacOS/soffice
# - Linux: 通过 which 命令查找
```

## 权限说明

- **超级管理员**: 拥有所有权限
- **管理员**: 管理用户、课程等
- **教师**: 管理课程、作业等
- **学生**: 查看课程、提交作业等

## 开发说明

### 添加新的API端点

1. 在 `app/routers/` 下创建新的蓝图文件
2. 在 `app.py` 中注册蓝图
3. 使用 `libs/response.py` 中的统一返回格式函数
4. 更新 `docs/user.yaml` 文档
5. 注意：API路径需要包含版本号，如 `/api/v2/xxx`

### 添加新的数据模型

1. 在 `app/models/` 下创建新的模型文件
2. 运行应用时会自动创建表结构

### 返回格式函数

在 `libs/response.py` 中提供了以下返回格式函数：

- `success_response(message, data)` - 成功响应（200）
- `created_response(message, data)` - 创建成功响应（201）
- `bad_request_response(message, code)` - 请求错误响应（400）
- `unauthorized_response(message, code)` - 未授权响应（401）
- `forbidden_response(message, code)` - 禁止访问响应（403）
- `not_found_response(message, code)` - 资源不存在响应（404）
- `error_response(message, code)` - 服务器错误响应（500）

### 文件处理统一方法

在 `app/models/file.py` 中提供了文件处理的统一方法：

- `File.detect_file_type(filename)` - 根据文件名自动检测文件类型
  - 返回值：'image', 'video', 'document', 'other'
  - 支持所有常见文件格式

- `File.is_office_document(file_path)` - 判断是否为 Office 文档
  - 支持的格式：.doc, .docx, .xls, .xlsx, .ppt, .pptx
  - 返回值：True/False

### Office 转 PDF 功能使用示例

```python
from app.models.file import File
from app.utils.office_converter import OfficeToPDFConverter

# 检测文件类型
file_type = File.detect_file_type('document.docx')
# 返回: 'document'

# 判断是否为 Office 文档
is_office = File.is_office_document('spreadsheet.xlsx')
# 返回: True

# 自动转换（推荐使用 upload_file_logic）
from app.routers.files import upload_file_logic
file_record = upload_file_logic(request.files['file'])
# 返回的 file_record 包含 pdf_file_id 字段（如果有 PDF）
```

## 注意事项

- 生产环境请修改 `config.yaml` 中的 `secret_key` 和数据库密码
- 建议使用环境变量管理敏感信息
- 定期备份数据库
- LibreOffice 是 Office 文档转 PDF 的必需组件，请确保正确安装
- v2版本登录方式已改为手机号+密码
- v2版本注册接口只需要用户名、手机号、密码三个参数
- v2版本所有API路径都包含版本号前缀 `/api/v2`
- 文件上传最大限制为 100MB
- Office 文档转 PDF 功能依赖于 LibreOffice，转换失败不影响文件上传

## License

MIT