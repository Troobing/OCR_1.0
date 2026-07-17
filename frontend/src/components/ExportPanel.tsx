/**
 * 导出面板 — 复制全文 / 下载 Word（分开） / 下载 Word（合并）
 * Config: 按钮文案与顺序、剪贴板逻辑
（提取结果下方的操作按钮）
 */
 * Skill：Clipboard API、Blob 下载

import { Button, Space, message } from 'antd';
import { CopyOutlined, DownloadOutlined, FileWordOutlined } from '@ant-design/icons';

interface Props {
  rawText: string;
  loading?: boolean;
  onDownload: (merge: boolean) => void;
}

export default function ExportPanel({ rawText, onDownload, loading }: Props) {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(rawText);
      message.success('已复制到剪贴板');
    } catch {
      message.error('复制失败，请手动选择文字复制');
    }
  };

  return (
    <div style={{ marginTop: 12, padding: '12px 0', borderTop: '1px solid #f0f0f0' }}>
      <Space wrap>
        <Button icon={<CopyOutlined />} onClick={handleCopy}>复制全文</Button>
        <Button icon={<DownloadOutlined />} onClick={() => onDownload(false)} loading={loading}>
          下载 Word（分开）
        </Button>
        <Button type="primary" icon={<FileWordOutlined />} onClick={() => onDownload(true)} loading={loading}>
          下载 Word（合并）
        </Button>
      </Space>
    </div>
  );
}
