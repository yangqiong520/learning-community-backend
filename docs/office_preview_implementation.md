# Office文档预览功能实现完成

## 已完成的功能

### 1. 后端转换功能
- ✅ 创建Office文档转PDF转换器 (`app/utils/office_converter.py`)
- ✅ 修改File模型，添加pdf_file_id字段 (`app/models/file.py`)
- ✅ 添加转换API端点 (`app/routers/files.py`)
- ✅ 添加预览URL获取端点 (`app/routers/files.py`)
- ✅ 执行数据库迁移，添加pdf_file_id字段

### 2. 数据库变更
- ✅ 添加 `pdf_file_id` 字段到 `files` 表
- ✅ 添加外键约束关联PDF文件
- ✅ 添加索引优化查询性能

### 3. 新增API端点

#### 转换Office文档为PDF
```
POST /api/v2/files/<file_id>/convert-to-pdf
```
- 将Office文档（.doc, .docx, .xls, .xlsx, .ppt, .pptx）转换为PDF
- 转换后的PDF会保存到 `storage/pdfs` 目录
- 支持缓存机制，避免重复转换

#### 获取文件预览URL
```
GET /api/v2/files/<file_id>/preview
```
- 返回文件的预览URL
- 对于Office文档，返回PDF预览URL
- 智能判断是否需要转换

## 使用步骤

### 1. 安装LibreOffice（必需）

**Windows:**
1. 下载 LibreOffice: https://www.libreoffice.org/download/
2. 安装到默认路径

**macOS:**
1. 下载 LibreOffice: https://www.libreoffice.org/download/
2. 拖拽到Applications文件夹

**Linux:**
```bash
sudo apt-get install libreoffice  # Ubuntu/Debian
sudo yum install libreoffice      # CentOS/RHEL
```

### 2. 前端集成

#### 方式1：直接获取预览URL（推荐）
```javascript
// 获取预览URL
const response = await fetch(`/api/v2/files/${fileId}/preview`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

if (data.data.preview_type === 'pdf') {
  // 显示PDF
  <embed src={data.data.preview_url} type="application/pdf" />
} else if (data.data.needs_conversion) {
  // 需要先转换
  await convertToPdf(fileId);
}
```

#### 方式2：手动转换
```javascript
// 转换为PDF
const response = await fetch(`/api/v2/files/${fileId}/convert-to-pdf`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// 使用PDF URL
<embed src={data.data.pdf_url} type="application/pdf" />
```

### 3. 测试转换功能

运行以下脚本测试转换功能：

```bash
python test_pdf_conversion.py
```

## 注意事项

1. **LibreOffice必须安装**：转换功能依赖LibreOffice
2. **首次转换时间**：约30秒，后续使用缓存
3. **文件大小限制**：建议小于10MB
4. **支持格式**：.doc, .docx, .xls, .xlsx, .ppt, .pptx
5. **无需网络**：完全本地转换

## 文件清单

### 新增文件
- `app/utils/office_converter.py` - Office文档转换器
- `docs/office_preview_guide.md` - 前端使用指南
- `docs/add_pdf_conversion.sql` - 数据库迁移脚本

### 修改文件
- `app/models/file.py` - 添加pdf_file_id字段
- `app/routers/files.py` - 添加转换和预览端点
- `docs/office_preview_guide.md` - 详细使用文档

## 下一步

1. 前端集成预览功能
2. 测试各种Office文档格式的转换
3. 添加转换进度显示（可选）
4. 优化大文件转换性能（可选）

## 支持与帮助

详细使用指南请查看：`docs/office_preview_guide.md`

如有问题，请检查：
1. LibreOffice是否正确安装
2. 后端日志中的错误信息
3. 文件格式是否支持
