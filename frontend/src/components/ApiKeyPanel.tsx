/**
 * API 设置面板 — 配置 LLM 服务端地址、Key、模型，保存到 localStorage + 同步后端
 * Config: 模型选项列表、默认值、表单字段
 */

import { useState } from 'react';
import { Modal, Form, Input, Select, Button, message } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { syncConfig, type ApiConfig } from '../services/api';

interface Props {
  config: ApiConfig;
  onSave: (config: ApiConfig) => void;
}

const MODEL_OPTIONS = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4-vision-preview', label: 'GPT-4 Vision' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
];

export default function ApiKeyPanel({ config, onSave }: Props) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const handleOpen = () => {
    form.setFieldsValue(config);
    setOpen(true);
  };

  const handleSave = () => {
    form.validateFields().then(async (values) => {
      onSave(values);
      try { await syncConfig(values); } catch {
        message.warning('配置已保存到本地，但未能同步到后端（后端可能未启动）');
      }
      setOpen(false);
    });
  };

  return (
    <>
      <Button icon={<SettingOutlined />} onClick={handleOpen} type="text" style={{ color: '#666' }}>
        API 设置
      </Button>
      <Modal title="API 设置" open={open} onOk={handleSave} onCancel={() => setOpen(false)}
        okText="保存" cancelText="取消">
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="base_url" label="API 地址" rules={[{ required: true }]}>
            <Input placeholder="https://api.uniapi.io/v1" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}>
            <Input.Password placeholder="sk-xxxx" />
          </Form.Item>
          <Form.Item name="model" label="模型" rules={[{ required: true }]}>
            <Select showSearch placeholder="选择或输入模型名" options={MODEL_OPTIONS}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
        </Form>
        <div style={{ color: '#999', fontSize: 12 }}>
          保存后同时存储到浏览器本地和后端内存中，无需每次填写。
        </div>
      </Modal>
    </>
  );
}
