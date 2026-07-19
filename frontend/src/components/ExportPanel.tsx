/**
 * 导出面板 — 复制 Markdown / 复制纯文本 / 下载 Word（分开） / 下载 Word（合并）
 * 负责：剪贴板操作、触发下载
 * Config: 按钮文案与顺序
 * （提取结果下方的操作按钮）
 * Skill：Clipboard API、Blob 下载
 */


import { Button, Space, message } from 'antd';
import { CopyOutlined, FileTextOutlined, DownloadOutlined, FileWordOutlined } from '@ant-design/icons';

interface Props {
  rawText: string;        // 原始 Markdown（含 LaTeX 源码）
  plainText: string;      // 纯文本（公式已转 Unicode）
  loading?: boolean;
  onDownload: (merge: boolean) => void;
}

export default function ExportPanel({ rawText, plainText, onDownload, loading }: Props) {
  const handleCopyMarkdown = async () => {
    try {
      await navigator.clipboard.writeText(rawText);
      message.success('已复制 Markdown 到剪贴板');
    } catch {
      message.error('复制失败，请手动选择文字复制');
    }
  };

  const handleCopyPlain = async () => {
    try {
      await navigator.clipboard.writeText(plainText);
      message.success('已复制纯文本到剪贴板');
    } catch {
      message.error('复制失败，请手动选择文字复制');
    }
  };

  return (
    <div style={{ marginTop: 12, padding: '12px 0', borderTop: '1px solid #f0f0f0' }}>
      <Space wrap>
        <Button icon={<CopyOutlined />} onClick={handleCopyMarkdown}>复制 Markdown</Button>
        <Button icon={<FileTextOutlined />} onClick={handleCopyPlain}>复制纯文本</Button>
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
