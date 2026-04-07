# Office文档预览功能使用指南

## 功能说明

后端已实现Office文档转PDF功能，支持在无网络环境下预览Office文档。

## 前端使用方法

### 方法1：直接获取预览URL（推荐）

```javascript
// 1. 获取预览URL
async function getPreviewUrl(fileId) {
  const response = await fetch(`/api/v2/files/${fileId}/preview`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();

  if (data.code === 200) {
    return data.data;
  }

  return null;
}

// 2. 使用预览URL
const previewInfo = await getPreviewUrl(fileId);

if (previewInfo.preview_type === 'pdf') {
  // 直接显示PDF
  <embed src={previewInfo.preview_url} width="100%" height="600px" type="application/pdf" />
} else if (previewInfo.preview_type === 'office') {
  // 需要转换
  if (previewInfo.needs_conversion) {
    // 调用转换接口
    await convertToPdf(fileId);
    // 重新获取预览URL
    const newPreviewInfo = await getPreviewUrl(fileId);
    <embed src={newPreviewInfo.preview_url} width="100%" height="600px" type="application/pdf" />
  }
}
```

### 方法2：手动转换后预览

```javascript
// 1. 转换Office文档为PDF
async function convertToPdf(fileId) {
  const response = await fetch(`/api/v2/files/${fileId}/convert-to-pdf`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();

  if (data.code === 200) {
    return data.data.pdf_url;
  }

  throw new Error(data.message);
}

// 2. 使用转换后的PDF预览
const pdfUrl = await convertToPdf(fileId);

<embed src={pdfUrl} width="100%" height="600px" type="application/pdf" />
```

### 方法3：使用react-pdf组件

```javascript
import { Document, Page, pdfjs } from 'react-pdf';

// 配置worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

function PDFViewer({ url }) {
  const [numPages, setNumPages] = useState(null);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  return (
    <div>
      <Document file={url} onLoadSuccess={onDocumentLoadSuccess}>
        {Array.from(new Array(numPages), (el, index) => (
          <Page key={`page_${index + 1}`} pageNumber={index + 1} />
        ))}
      </Document>
    </div>
  );
}

// 使用
const previewInfo = await getPreviewUrl(fileId);
<PDFViewer url={previewInfo.preview_url} />
```

## API端点

### 1. 获取预览URL
```
GET /api/v2/files/<file_id>/preview
```

**响应示例：**
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "file_id": 100,
    "preview_url": "http://127.0.0.1:5000/api/v2/files/serve/101",
    "preview_type": "pdf",
    "needs_conversion": false
  }
}
```

### 2. 转换Office文档为PDF
```
POST /api/v2/files/<file_id>/convert-to-pdf
```

**请求：**
```json
// 需要Authorization header
```

**响应示例：**
```json
{
  "code": 200,
  "message": "转换成功",
  "data": {
    "pdf_file_id": 101,
    "pdf_url": "http://127.0.0.1:5000/api/v2/files/serve/101"
  }
}
```

## 环境要求

### Windows系统
1. 下载并安装 LibreOffice: https://www.libreoffice.org/download/
2. 安装后无需额外配置，系统会自动找到LibreOffice路径

### macOS系统
1. 安装LibreOffice: https://www.libreoffice.org/download/
2. 系统会自动找到LibreOffice路径

### Linux系统
```bash
# Ubuntu/Debian
sudo apt-get install libreoffice

# CentOS/RHEL
sudo yum install libreoffice
```

## 注意事项

1. **首次转换时间**：首次转换需要30秒左右，后续直接使用缓存的PDF
2. **文件大小限制**：建议小于10MB的Office文档
3. **支持的格式**：.doc, .docx, .xls, .xlsx, .ppt, .pptx
4. **网络要求**：此方案无需网络，完全本地转换
5. **PDF存储**：转换后的PDF会保存在`storage/pdfs`目录

## 故障排除

### 转换失败
- 确认LibreOffice已正确安装
- 检查Office文档是否损坏
- 查看后端日志获取详细错误信息

### PDF预览空白
- 确认PDF文件存在且可访问
- 检查PDF格式是否正确
- 尝试直接下载PDF文件验证

### LibreOffice找不到
- Windows: 检查安装路径是否在 `C:\Program Files\LibreOffice\`
- macOS: 检查是否在 `/Applications/LibreOffice.app/`
- Linux: 运行 `which libreoffice` 检查是否安装
