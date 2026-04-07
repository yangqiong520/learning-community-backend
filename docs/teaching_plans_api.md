# 教学计划 API 文档

## 基本信息

- **接口名称**: 教学计划 API
- **版本**: v1.0
- **基础URL**: `/api/v2/teaching_plans`
- **认证方式**: Bearer Token

## 数据模型

### 教学计划对象 (TeachingPlan)

```json
{
  "id": 1,
  "title": "教学计划标题",
  "content": "教学计划内容",
  "file_url": "/api/v2/files/serve/123",
  "imgurl": "/api/v2/files/serve/124",
  "uploader": "用户名",
  "time": "2024-03-22 13:00:00",
  "like": true
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|--------|
| id | number | 教学计划唯一标识 |
| file_url | string | 返回文件链接 |
| imgurl | string | 图片链接 |
| title | string | 标题 |
| content | string | 内容 |
| uploader | string | 上传者用户名 |
| time | string | 上传时间，格式：YYYY-MM-DD HH:mm:ss |
| like | boolean | 点赞表示收藏 |

---

## 接口列表

### 1. 创建教学计划

**接口地址**: `POST /api/v2/teaching_plans/upload`

**请求头**:
```
Content-Type: multipart/form-data
Authorization: Bearer {token}
```

**请求参数**:
- `title` (string, 必填): 标题
- `content` (string, 可选): 内容（不提供时自动提取）
- `document` (file, 必填): 文档文件
- `image` (file, 必填): 图片文件

**响应示例**:
```json
{
  "code": 201,
  "message": "发布成功",
  "data": {
    "teaching_plan": {
      "id": 1,
      "title": "教学计划标题",
      "content": "教学计划内容",
      "file_url": "/api/v2/files/serve/123",
      "imgurl": "/api/v2/files/serve/124",
      "uploader": "用户名",
      "time": "2024-03-22 13:00:00",
      "like": false
    }
  }
}
```

---

### 2. 获取教学计划列表

**接口地址**: `GET /api/v2/teaching_plans`
**接口地址**: `GET /api/v2/teaching_plans/`

**请求参数**:
- `page` (number, 可选): 页码，默认1
- `per_page` (number, 可选): 每页数量，默认10
- `keyword` (string, 可选): 搜索关键词

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "teaching_plans": [
      {
        "id": 1,
        "title": "教学计划标题",
        "content": "教学计划内容",
        "file_url": "/api/v2/files/serve/123",
        "imgurl": "/api/v2/files/serve/124",
        "uploader": "用户名",
        "time": "2024-03-22 13:00:00",
        "like": true
      }
    ],
    "total": 10,
    "page": 1,
    "per_page": 10,
    "pages": 1
  }
}
```

---

### 3. 获取单个教学计划

**接口地址**: `GET /api/v2/teaching_plans/{id}`

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "teaching_plan": {
      "id": 1,
      "title": "教学计划标题",
      "content": "教学计划内容",
      "file_url": "/api/v2/files/serve/123",
      "imgurl": "/api/v2/files/serve/124",
      "uploader": "用户名",
      "time": "2024-03-22 13:00:00",
      "like": false
    }
  }
}
```

---

### 4. 更新教学计划

**接口地址**: `PUT /api/v2/teaching_plans/{id}`

**权限要求**: 教师或管理员

**请求头**:
```
Content-Type: application/json
Authorization: Bearer {token}
```

**请求参数**:
- `title` (string, 可选): 标题
- `content` (string, 可选): 内容

**响应示例**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "teaching_plan": {
      "id": 1,
      "title": "教学计划标题",
      "content": "教学计划内容",
      "file_url": "/api/v2/files/serve/123",
      "imgurl": "/api/v2/files/serve/124",
      "uploader": "用户名",
      "time": "2024-03-22 13:00:00",
      "like": false
    }
  }
}
```

---

### 5. 删除教学计划

**接口地址**: `DELETE /api/v2/teaching_plans/{id}`

**权限要求**: 教师或管理员

**响应示例**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

---

### 6. 点赞/取消点赞

**接口地址**: `POST /api/v2/teaching_plans/{id}/like`

**响应示例**:
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "teaching_plan": {
      "id": 1,
      "title": "教学计划标题",
      "content": "教学计划内容",
      "file_url": "/api/v2/files/serve/123",
      "imgurl": "/api/v2/files/serve/124",
      "uploader": "用户名",
      "time": "2024-03-22 13:00:00",
      "like": true
    },
    "is_liked": true
  }
}
```

---

## 状态码

| 状态码 | 说明 |
|--------|--------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 资源不存在 |
| 404 | 无权限 |
| 500 | 服务器错误 |

---

## 注意事项

1. 所有接口都需要认证token
2. 上传文件时使用 `multipart/form-data` 格式
3. 如果不提供content字段，系统会自动从文档中提取内容
4. 支持PDF和Word文档的自动内容提取
5. 点赞表示收藏功能
6. 更新和删除操作需要教师或管理员权限
7. 分页参数从1开始
