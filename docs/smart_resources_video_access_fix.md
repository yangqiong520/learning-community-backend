# 智能资源区视频访问权限修改说明

## 修改内容

### 1. 新增公开视频服务接口

**文件**: `app/routers/files.py`

**新增接口**: `GET /api/v2/files/serve-video/<file_id>`

**功能**: 提供无需认证的视频文件访问接口

**特点**:
- ✅ 无需JWT认证，任何人都可以访问
- ✅ 验证文件类型，只允许视频文件
- ✅ 验证文件存在性和活跃状态
- ✅ 支持视频的流式播放

### 2. 修改SmartResource模型

**文件**: `app/models/smart_resource.py`

**修改内容**: 将 `video_url` 从 `/api/v2/files/serve/` 改为 `/api/v2/files/serve-video/`

**修改前**:
```python
'video_url': f'/api/v2/files/serve/{self.video_file_id}'
```

**修改后**:
```python
'video_url': f'/api/v2/files/serve-video/{self.video_file_id}'
```

### 3. 更新OpenAPI文档

**文件**: `docs/smart_resources_api.yaml`

**修改内容**: 更新SmartResource schema中的video_url示例

**修改前**:
```yaml
video_url:
  type: string
  description: 视频URL
  example: /api/v2/files/serve/123
```

**修改后**:
```yaml
video_url:
  type: string
  description: 视频URL（公开访问，无需认证）
  example: /api/v2/files/serve-video/123
```

## 权限控制总结

### 上传权限（需要认证）
- ✅ **超级管理员** (role=1): 可以上传
- ✅ **管理员** (role=2): 可以上传
- ✅ **教师** (role=3): 可以上传
- ❌ **学生** (role=4): 无法上传

### 访问权限
- ✅ **视频播放**: 任何人都可以访问（无需认证）
- ✅ **缩略图**: 任何人都可以访问（无需认证）
- ❌ **上传操作**: 需要认证且只有特定角色可以操作

## API接口对比

| 功能 | 旧接口 | 新接口 | 认证要求 |
|------|--------|--------|----------|
| 视频服务 | `/api/v2/files/serve/158` | `/api/v2/files/serve-video/158` | 无需认证 |
| 缩略图服务 | `/api/v2/files/serve-image/159` | `/api/v2/files/serve-image/159` | 无需认证 |
| 资源上传 | `/api/v2/smart-resources` | `/api/v2/smart-resources` | 需要认证 + 权限检查 |

## 测试验证

### 1. 视频访问测试
```bash
# 无需认证直接访问视频
curl -I "http://localhost:5000/api/v2/files/serve-video/158"
# 返回: HTTP/1.1 200 OK
```

### 2. 资源上传测试
```bash
# 超级管理员上传成功
POST /api/v2/smart-resources
Authorization: Bearer <admin_token>
# 返回: 201 Created
```

### 3. 权限控制测试
```bash
# 学生账号尝试上传
POST /api/v2/smart-resources
Authorization: Bearer <student_token>
# 返回: 403 Forbidden
```

## 安全考虑

### 实施的安全措施
1. **文件类型验证**: 只允许访问视频类型的文件
2. **文件存在性检查**: 防止路径遍历攻击
3. **文件活跃状态检查**: 只返回未删除的文件
4. **上传权限控制**: 严格限制上传操作的角色权限

### 安全风险评估
- **视频公开访问**: 按照设计要求，视频应该是公开的
- **上传权限控制**: 已正确实现，只有授权用户可以上传
- **文件路径安全**: 使用文件ID而非路径，防止路径遍历

## 使用说明

### 前端集成
前端现在可以直接使用返回的 `video_url` 播放视频：

```javascript
// 获取智能资源列表
const response = await fetch('/api/v2/smart-resources', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const resources = await response.json();
const videoUrl = resources.data.resources[0].video_url;
// videoUrl = "/api/v2/files/serve-video/158"

// 直接在video标签中使用
<video src={videoUrl} controls />
```

### 错误处理
如果视频无法播放，可能的原因：
1. 文件不存在 (404)
2. 文件已删除 (403)
3. 文件类型不是视频 (400)

## 后续建议

1. **视频CDN**: 考虑将视频文件迁移到CDN，提高访问速度
2. **视频转码**: 添加视频转码功能，统一视频格式
3. **视频水印**: 为上传的视频添加水印，保护版权
4. **访问日志**: 记录视频访问日志，分析播放数据
5. **缓存策略**: 添加视频缓存策略，减少服务器负载

## 修改文件列表

1. `app/routers/files.py` - 新增公开视频服务接口
2. `app/models/smart_resource.py` - 修改视频URL生成逻辑
3. `docs/smart_resources_api.yaml` - 更新API文档

## 总结

✅ 问题已解决：视频现在可以正常播放
✅ 权限已实现：只有教师、管理员、超级管理员可以上传
✅ 安全已保证：实施了必要的安全措施
✅ 文档已更新：OpenAPI文档已同步更新
