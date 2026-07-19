/**
 * 上传区域 — 拖拽/点击/Ctrl+V 粘贴图片，校验格式和大小后传给父组件
 * 负责：文件选择、格式校验、粘贴事件监听
 * Config: 允许的文件格式、大小上限
 * （页面左上角拖拽上传框）
 * Skill：Ant Design Dragger、Clipboard API
 */


import { useCallback, useEffect } from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

interface Props {
  onFileAdded: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ onFileAdded, disabled }: Props) {
  const beforeUpload = useCallback((file: File) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp'];
    if (!allowedTypes.includes(file.type)) {
      message.error(`${file.name}: 不支持该格式`);
      return Upload.LIST_IGNORE;
    }
    if (file.size > 20 * 1024 * 1024) {
      message.error(`${file.name}: 超过 20MB 限制`);
      return Upload.LIST_IGNORE;
    }
    onFileAdded(file);
    return false;
  }, [onFileAdded]);

  // Ctrl+V 粘贴截图
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (disabled) return;
      const items = e.clipboardData?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          const blob = items[i].getAsFile();
          if (blob) {
            const file = new File([blob], `clipboard_${Date.now()}.png`, { type: blob.type });
            beforeUpload(file);
          }
          break;
        }
      }
    };
    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, [disabled, beforeUpload]);

  return (
    <div style={{ height: 260, overflow: 'hidden' }}>
      <Dragger
        multiple
        showUploadList={false}
        accept=".jpg,.jpeg,.png,.webp,.bmp"
        beforeUpload={beforeUpload}
        disabled={disabled}
        style={{ padding: 16 }}
      >
        <p className="ant-upload-drag-icon"><InboxOutlined /></p>
        <p style={{ fontSize: 16, marginTop: 8 }}>点击选择图片 或 拖拽图片到此处</p>
        <p style={{ color: '#999', fontSize: 13 }}>支持 JPG、PNG、WebP、BMP，单张不超过 20MB</p>
        <p style={{ color: '#999', fontSize: 13 }}>也可使用 Ctrl+V 粘贴截图</p>
      </Dragger>
    </div>
  );
}
