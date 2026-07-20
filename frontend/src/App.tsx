/**
 * 主页面 — 全局状态管理、双栏布局、上传/提取/结果/导出拼接为完整页面
 * 负责：全局状态管理、组件拼装
 * Config: 页面布局、步骤条、左右栏比例、按钮交互
 * （页面主体：左栏传图+列表，右栏提取结果）
 * Skill：React 状态提升、useRef 防抖、Ant Design Layout
 */



import { useState, useCallback, useRef, useMemo } from 'react';
import {
  Layout, Row, Col, Steps, Button, message, Spin, Dropdown, Tag,
} from 'antd';
import {
  CloudUploadOutlined, ExperimentOutlined, FileDoneOutlined,
  DownOutlined, FileTextOutlined,
} from '@ant-design/icons';

import UploadZone from './components/UploadZone';
import ImageList from './components/ImageList';
import ResultViewer from './components/ResultViewer';
import ExportPanel from './components/ExportPanel';
import { uploadImages, extractContent, downloadWord, deleteImage } from './services/api';
import { contentToPlainText } from './services/plainText';
import type { ImageInfo, ExtractResult } from './services/api';

const { Header, Content } = Layout;

function getErrorMessage(e: any): string {
  return e?.response?.data?.detail || e?.message || '未知错误';
}

interface ImageItem {
  id: string;
  file: File;
  previewUrl: string;
  serverInfo?: ImageInfo;
}

export default function App() {
  const [images, setImages] = useState<ImageItem[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [extracting, setExtracting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [results, setResults] = useState<ExtractResult[]>([]);
  const [activeTab, setActiveTab] = useState('0');
  const [uploadKey, setUploadKey] = useState(0);
  const pendingFilesRef = useRef<ImageItem[]>([]);
  const uploadTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // ─── 文件上传管理 ───

  const handleFileAdded = useCallback((file: File) => {
    const newImg: ImageItem = {
      id: crypto.randomUUID(), file,
      previewUrl: URL.createObjectURL(file),
    };
    setImages((prev) => [...prev, newImg]);
    setResults([]);
    setCurrentStep(0);
    pendingFilesRef.current = [...pendingFilesRef.current, newImg];

    // 防抖攒批：150ms 内连续文件归为一批上传
    if (uploadTimerRef.current) clearTimeout(uploadTimerRef.current);
    uploadTimerRef.current = setTimeout(async () => {
      const batch = pendingFilesRef.current;
      pendingFilesRef.current = [];
      if (batch.length === 0) return;
      try {
        const res = await uploadImages(batch.map((img) => img.file));
        setImages((prev) => prev.map((img) => {
          const idx = batch.findIndex((b) => b.id === img.id);
          if (idx >= 0 && res.images[idx]) return { ...img, serverInfo: res.images[idx] };
          return img;
        }));
        message.success(`成功上传 ${res.images.length} 张图片`);
      } catch (e: any) {
        message.error(`上传失败：${getErrorMessage(e)}`);
      }
    }, 150);
  }, []);

  const handleRemoveImage = useCallback((id: string) => {
    // 找到 serverInfo.id 后通知后端清理
    let serverId: string | undefined;
    setImages((prev) => {
      const removed = prev.find((img) => img.id === id);
      if (removed) {
        URL.revokeObjectURL(removed.previewUrl);
        serverId = removed.serverInfo?.id;
      }
      return prev.filter((img) => img.id !== id);
    });
    setResults([]);
    setCurrentStep(0);
    pendingFilesRef.current = pendingFilesRef.current.filter((img) => img.id !== id);
    if (serverId) {
      deleteImage(serverId).catch(() => { /* 忽略后端清理失败 */ });
    }
  }, []);

  const handleClearAll = useCallback(() => {
    const serverIds: string[] = [];
    setImages((prev) => {
      prev.forEach((img) => {
        URL.revokeObjectURL(img.previewUrl);
        if (img.serverInfo?.id) serverIds.push(img.serverInfo.id);
      });
      return [];
    });
    setResults([]);
    setCurrentStep(0);
    pendingFilesRef.current = [];
    if (uploadTimerRef.current) clearTimeout(uploadTimerRef.current);
    setUploadKey((k) => k + 1);
    // 批量清理后端
    serverIds.forEach((sid) => deleteImage(sid).catch(() => { /* ignore */ }));
  }, []);

  // ─── AI 提取 ───

  const handleExtract = useCallback(async () => {
    // 前端不持有真 key，无法本地校验；直接发请求，后端无 key 时返回 400
    const uploaded = images.filter((img) => img.serverInfo);
    if (uploaded.length === 0) return;

    setExtracting(true);
    setCurrentStep(1);
    try {
      const res = await extractContent(uploaded.map((img) => img.serverInfo!.id));
      const ok = res.results.filter((r) => r.status === 'success').length;
      const fail = res.results.length - ok;
      if (fail > 0) message.warning(`${ok} 张成功，${fail} 张失败`);
      else message.success(`全部 ${ok} 张提取成功`);

      const nameMap = new Map(images.map((img) => [img.serverInfo?.id, img.file.name]));
      setResults(res.results.map((r) => ({
        ...r, filename: nameMap.get(r.image_id) || r.filename,
      })));
      setActiveTab('0');
      setCurrentStep(2);
    } catch (e: any) {
      const msg = getErrorMessage(e);
      message.error(`提取失败：${msg}`);
      // 后端返回 400 "未配置 API Key" 时，提示用户去设置
      if (msg.includes('API Key')) {
        message.warning('请点击右上角「API 设置」配置 API Key');
      }
      setCurrentStep(0);
    } finally {
      setExtracting(false);
    }
  }, [images]);

  // ─── 下载 ───

  const handleDownload = useCallback(async (merge: boolean) => {
    const okList = results.filter((r) => r.status === 'success');
    if (okList.length === 0) return;

    setDownloading(true);
    try {
      await downloadWord(
        okList.map((r) => r.image_id), okList.map((r) => r.content), merge,
      );
      message.success('下载完成');
    } catch (e: any) {
      message.error(`下载失败：${getErrorMessage(e)}`);
    } finally {
      setDownloading(false);
    }
  }, [results]);

  // ─── 派生状态 ───

  const allUploaded = images.length > 0 && images.every((img) => img.serverInfo);
  const hasResults = results.length > 0;
  const currentResult = hasResults ? results[Number(activeTab)] : null;
  const currentPlainText = useMemo(
    () => (currentResult?.content ? contentToPlainText(currentResult.content) : ''),
    [currentResult?.content],
  );

  // ─── UI 渲染 ───

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Header style={{
        background: '#fff', padding: '0 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0', height: 56,
      }}>
        <div style={{ fontSize: 18, fontWeight: 600 }}>
          <ExperimentOutlined style={{ marginRight: 8 }} />
          OCR Agent
        </div>
      </Header>

      <Content style={{ padding: '24px 48px', maxWidth: 1300, margin: '0 auto', width: '100%' }}>
        <Steps current={currentStep} size="small" style={{ marginBottom: 24 }}
          items={[
            { title: '上传图片', icon: <CloudUploadOutlined /> },
            { title: '提取', icon: <ExperimentOutlined /> },
            { title: '查看结果', icon: <FileDoneOutlined /> },
          ]}
        />

        <Row gutter={24}>
          {/* ─── 左栏 ─── */}
          <Col xs={24} lg={10}>
            <UploadZone key={uploadKey} onFileAdded={handleFileAdded} disabled={extracting} />
            <ImageList images={images} onRemove={handleRemoveImage}
              onClearAll={handleClearAll} disabled={extracting} />
            {images.length > 0 && (
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Button type="primary" size="large" onClick={handleExtract}
                  loading={extracting} disabled={!allUploaded || extracting}
                  icon={<ExperimentOutlined />}>
                  {extracting ? '提取中…' : '开始提取'}
                </Button>
              </div>
            )}
          </Col>

          {/* ─── 右栏 ─── */}
          <Col xs={24} lg={14}>
            {extracting && (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Spin size="large" tip="正在提取，请耐心等待..." />
              </div>
            )}

            {hasResults && !extracting && (
              <div style={{
                background: '#fff', borderRadius: 8, padding: 20,
                minHeight: 260, boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
              }}>
                <Dropdown trigger={['hover', 'click']}
                  menu={{
                    selectable: true, selectedKeys: [activeTab],
                    onClick: ({ key }) => setActiveTab(key),
                    style: { maxHeight: 300, overflowY: 'auto' },
                    items: results.map((result, i) => ({
                      key: String(i),
                      label: (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <FileTextOutlined style={{ fontSize: 13 }} />
                          <span style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {result.filename || `图片 ${i + 1}`}
                          </span>
                          <Tag color={result.status === 'success' ? 'green' : 'red'}
                            style={{ marginLeft: 'auto', fontSize: 11 }}>
                            {result.status === 'success' ? '成功' : '失败'}
                          </Tag>
                        </div>
                      ),
                    })),
                  }}>
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                    cursor: 'pointer', padding: '4px 12px',
                    border: '1px solid #e8e8e8', borderRadius: 6,
                    background: '#fafafa', marginBottom: 16,
                  }}>
                    <FileTextOutlined />
                    <span style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {currentResult?.filename || '图片 1'}
                    </span>
                    <Tag color={currentResult?.status === 'success' ? 'green' : 'red'} style={{ fontSize: 11 }}>
                      {currentResult?.status === 'success' ? '成功' : '失败'}
                    </Tag>
                    <DownOutlined style={{ fontSize: 10, color: '#999' }} />
                  </div>
                </Dropdown>

                {currentResult?.status === 'success' ? (
                  <>
                    <ResultViewer content={currentResult.content} />
                    <ExportPanel
                      rawText={currentResult.content}
                      plainText={currentPlainText}
                      loading={downloading}
                      onDownload={handleDownload}
                    />
                  </>
                ) : (
                  <div style={{ color: '#ff4d4f', padding: 16 }}>
                    {currentResult?.error || '提取失败'}
                  </div>
                )}
              </div>
            )}

            {!hasResults && !extracting && (
              <div style={{
                background: '#fff', borderRadius: 8, padding: 80,
                textAlign: 'center', color: '#ccc', minHeight: 260,
                boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
              }}>
                <FileDoneOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>上传图片后点击「开始提取」，结果将显示在这里</div>
              </div>
            )}
          </Col>
        </Row>
      </Content>
    </Layout>
  );
}
