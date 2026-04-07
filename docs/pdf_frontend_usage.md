# PDF 文件前端使用指南

## 概述

当上传 Office 文档（.doc, .docx, .xls, .xlsx, .ppt, .pptx）到系统时，系统会自动将其转换为 PDF。前端可以通过 API 返回的数据直接访问转换后的 PDF 文件。

## API 返回格式

### 教学计划 (TeachingPlan)

```json
{
  "id": 8,
  "title": "测试教学计划",
  "content": "这是一个测试教学计划的内容描述。",
  "file_id": 117,
  "file_url": "/api/v2/files/serve/117",
  "image_file_id": 116,
  "imgurl": "/api/v2/files/serve/116",
  "uploader": "admin",
  "time": "2026-04-03 09:18:55",
  "like": false,
  "pdf_file_id": 118,
  "pdf_url": "/api/v2/files/serve/118"
}
```

### 教案课件 (Courseware)

```json
{
  "id": 1,
  "title": "教案课件标题",
  "content": "教案课件详细内容",
  "document_file_id": 100,
  "file_url": "/api/v2/files/serve/100",
  "image_file_id": 101,
  "imgurl": "/api/v2/files/serve/101",
  "uploader": "teacher",
  "time": "2024-03-22",
  "like": true,
  "pdf_file_id": 102,
  "pdf_url": "/api/v2/files/serve/102"
}
```

### 教材 (Textbook)

```json
{
  "id": 1,
  "title": "教材标题",
  "content": "教材详细内容",
  "document_file_id": 200,
  "file_url": "/api/v2/files/serve/200",
  "image_file_id": 201,
  "imgurl": "/api/v2/files/serve/201",
  "uploader": "teacher",
  "time": "2024-03-22",
  "like": false,
  "pdf_file_id": 202,
  "pdf_url": "/api/v2/files/serve/202"
}
```

## 字段说明

### 新增字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `file_id` | integer | 原始文档文件ID | 117 |
| `image_file_id` | integer | 图片文件ID | 116 |
| `pdf_file_id` | integer | PDF文件ID（仅Office文档有此字段） | 118 |
| `pdf_url` | string | PDF文件访问URL（仅Office文档有此字段） | `/api/v2/files/serve/118` |

### 注意事项

- **pdf_file_id** 和 **pdf_url** 字段仅存在于上传了 Office 文档的记录中
- 上传 PDF、图片、视频等格式的文件不会有这些字段
- 如果转换失败，也不会有这些字段

## 前端使用方法

### 方法 1：在新窗口打开 PDF

```javascript
// 1. 获取教学计划数据
const response = await fetch('/api/v2/teaching_plans/8', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
});

const data = await response.json();
const teachingPlan = data.data.teaching_plan;

// 2. 检查是否有 PDF 文件
if (teachingPlan.pdf_file_id) {
  console.log('PDF文件ID:', teachingPlan.pdf_file_id);
  console.log('PDF访问URL:', teachingPlan.pdf_url);

  // 3. 在新窗口打开 PDF
  window.open(teachingPlan.pdf_url, '_blank');
} else {
  console.log('该文档没有PDF版本');
  // 使用原始文档URL
  window.open(teachingPlan.file_url, '_blank');
}
```

### 方法 2：在 iframe 中嵌入 PDF

```html
<!-- 创建 iframe 容器 -->
<div id="pdf-container">
  <iframe
    id="pdf-frame"
    width="100%"
    height="600px"
    style="border: none;">
  </iframe>
</div>

<script>
// 设置 iframe 的 src
if (teachingPlan.pdf_file_id) {
  document.getElementById('pdf-frame').src = teachingPlan.pdf_url;
} else {
  // 如果没有PDF，显示其他内容或提示
  document.getElementById('pdf-frame').src = teachingPlan.file_url;
}
</script>
```

### 方法 3：使用 PDF.js 自定义渲染

```javascript
// 引入 PDF.js
import * as pdfjsLib from 'pdfjs-dist';

// 设置 PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// 加载并渲染 PDF
async function renderPDF(pdfUrl, canvasId) {
  try {
    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    const pdf = await loadingTask.promise;
    console.log('PDF加载成功，页数:', pdf.numPages);

    // 渲染第一页
    const page = await pdf.getPage(1);
    const canvas = document.getElementById(canvasId);
    const context = canvas.getContext('2d');

    // 设置 canvas 尺寸
    const viewport = page.getViewport({ scale: 1.5 });
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    // 渲染页面
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    };
    await page.render(renderContext).promise;
    console.log('PDF页面渲染完成');
  } catch (error) {
    console.error('PDF渲染失败:', error);
  }
}

// 使用示例
if (teachingPlan.pdf_file_id) {
  renderPDF(teachingPlan.pdf_url, 'pdf-canvas');
} else {
  console.log('该文档没有PDF版本');
}
```

### 方法 4：使用 react-pdf 库（React）

```jsx
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

function PDFViewer({ teachingPlan }) {
  if (!teachingPlan.pdf_file_id) {
    return <div>该文档没有PDF版本</div>;
  }

  return (
    <div className="pdf-viewer">
      <Document
        file={teachingPlan.pdf_url}
        onLoadSuccess={({ numPages }) => console.log(`加载 ${numPages} 页`)}
        onError={(error) => console.error('PDF加载失败:', error)}
      >
        <Page pageNumber={1} />
      </Document>
    </div>
  );
}

// 使用示例
<PDFViewer teachingPlan={teachingPlan} />
```

### 方法 5：条件显示不同预览方式

```javascript
function renderDocumentPreview(item) {
  // 检查是否有 PDF
  if (item.pdf_file_id) {
    return (
      <div>
        <h3>PDF 预览</h3>
        <div className="pdf-options">
          <button onClick={() => window.open(item.pdf_url, '_blank')}>
            新窗口打开
          </button>
          <button onClick={() => showInIframe(item.pdf_url)}>
            iframe 嵌入
          </button>
          <button onClick={() => renderWithPDFJS(item.pdf_url)}>
            自定义渲染
          </button>
        </div>
      </div>
    );
  }

  // 检查文档类型
  if (item.file_url) {
    const fileExtension = item.file_url.split('.').pop().toLowerCase();

    // 图片文件
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension)) {
      return <img src={item.file_url} alt="文档预览" />;
    }

    // PDF 文件
    if (fileExtension === 'pdf') {
      return <iframe src={item.file_url} width="100%" height="600px" />;
    }

    // 其他文件类型
    return (
      <div>
        <p>该文件类型不支持预览</p>
        <button onClick={() => window.open(item.file_url, '_blank')}>
          下载文件
        </button>
      </div>
    );
  }

  return <div>无文档预览</div>;
}

// 使用示例
renderDocumentPreview(teachingPlan);
```

## 错误处理

### PDF 文件不存在

```javascript
if (teachingPlan.pdf_file_id) {
  try {
    const response = await fetch(teachingPlan.pdf_url);
    if (!response.ok) {
      throw new Error('PDF文件加载失败');
    }
    // 处理PDF...
  } catch (error) {
    console.error('PDF加载错误:', error);
    // 回退到原始文档
    window.open(teachingPlan.file_url, '_blank');
  }
}
```

### 转换失败

```javascript
// 如果没有 pdf_file_id，说明转换失败或不是Office文档
if (!teachingPlan.pdf_file_id) {
  if (isOfficeDocument(teachingPlan.file_url)) {
    console.warn('Office文档转换失败');
    // 可以提示用户重新上传或联系管理员
  } else {
    console.log('该文件不是Office文档，无需转换');
  }
  // 使用原始文档
  window.open(teachingPlan.file_url, '_blank');
}

function isOfficeDocument(url) {
  const officeExtensions = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'];
  return officeExtensions.some(ext => url.includes(ext));
}
```

## 最佳实践

1. **优先使用 PDF**: 如果有 PDF 文件，优先使用 PDF 进行预览
2. **错误处理**: 始终添加错误处理，避免 PDF 加载失败影响用户体验
3. **用户提示**: 明确告知用户是否可以预览，以及预览方式
4. **性能考虑**: 对于大文件，考虑使用分页加载或流式加载
5. **兼容性**: 使用标准的 PDF.js 库确保跨浏览器兼容性

## 常见问题

**Q: 为什么有些数据没有 pdf_file_id？**
A: 只有上传了 Office 文档（.doc, .docx, .xls, .xlsx, .ppt, .pptx）的记录才有 PDF 文件。如果上传的是 PDF、图片等格式，或者转换失败，就不会有此字段。

**Q: PDF 文件下载速度很慢怎么办？**
A: 可以考虑使用 CDN 加速，或者实现 PDF 的分页加载。

**Q: 如何检测 PDF 是否加载成功？**
A: 使用 try-catch 包裹 PDF 加载逻辑，或者监听 iframe 的 load 事件。

**Q: 可以在前端直接编辑 PDF 吗？**
A: 不能直接编辑。如果需要编辑功能，需要使用专门的 PDF 编辑库或后端服务。
