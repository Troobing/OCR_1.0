/**
 * 图片列表 — 已添加图片的紧凑列表：回形针图标 + 文件名 + 大小 + 删除按钮
 * Config: 列表样式、行高、删除确认文案
（上传框下方的图片清单）
 */

import { Button, Popconfirm } from 'antd';
import { DeleteOutlined, FileImageOutlined, PaperClipOutlined } from '@ant-design/icons';

interface ImageItem {
  id: string;
  file: File;
  previewUrl: string;
}

interface Props {
  images: ImageItem[];
  onRemove: (id: string) => void;
  onClearAll: () => void;
  disabled?: boolean;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ImageList({ images, onRemove, onClearAll, disabled }: Props) {
  if (images.length === 0) return null;

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 8, paddingBottom: 8, borderBottom: '1px solid #f0f0f0',
      }}>
        <span style={{ fontWeight: 500, fontSize: 14 }}>
          <FileImageOutlined style={{ marginRight: 6 }} />
          已添加 {images.length} 张图片
        </span>
        <Popconfirm title="确定清空全部图片？" onConfirm={onClearAll} okText="确定" cancelText="取消">
          <Button size="small" danger disabled={disabled}>全部清空</Button>
        </Popconfirm>
      </div>

      <div style={{ maxHeight: '50vh', overflowY: 'auto' }}>
        {images.map((img) => (
          <div key={img.id} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '6px 4px', borderBottom: '1px solid #fafafa',
          }}>
            <PaperClipOutlined style={{ color: '#999', fontSize: 13 }} />
            <span style={{
              flex: 1, minWidth: 0, fontSize: 13,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {img.file.name}
            </span>
            <span style={{ color: '#999', fontSize: 12, whiteSpace: 'nowrap', minWidth: 55 }}>
              {formatSize(img.file.size)}
            </span>
            <Popconfirm title="确定删除这张图片？" onConfirm={() => onRemove(img.id)} okText="确定" cancelText="取消">
              <Button size="small" type="text" danger icon={<DeleteOutlined />} disabled={disabled} />
            </Popconfirm>
          </div>
        ))}
      </div>
    </div>
  );
}
