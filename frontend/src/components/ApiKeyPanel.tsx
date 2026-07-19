/**
 * API 设置面板 — 配置 LLM 服务端地址、Key、模型，保存到浏览器本地 + 后端磁盘
 * 负责：表单验证、本地存储、后端同步
 * Config: 默认值、占位符、模型选项
 * （右上角 API 设置弹窗）
 * Skill：Ant Design Modal、Form 表单、AutoComplete
 */


import { useState } from 'react';
import { Modal, Form, Input, AutoComplete, Button, message } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { saveConfigToDisk, type ApiConfig } from '../services/api';

interface Props {
  config: ApiConfig;
  onSave: (config: ApiConfig) => void;
}

// 常用模型建议项（仅作输入提示，用户可输入任意值）
const MODEL_SUGGESTIONS = [
  'gpt-4o',
  'gpt-4o-mini',
  'claude-3-5-sonnet-20241022',
  'gemini-1.5-pro',
  'deepseek-chat',
];

export default function ApiKeyPanel({ config, onSave }: Props) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const handleOpen = () => {
    form.setFieldsValue({
      base_url: config.base_url,
      // 不预填 api_key（可能是掩码），避免误导用户保存时把掩码当真值写回
      api_key: '',
      model: config.model,
    });
    setOpen(true);
  };

  const handleSave = () => {
    form.validateFields().then(async (values) => {
      // 若用户没输入 api_key，保留原 config 的 api_key（让后端不覆盖）
      // saveConfigToDisk 内部会判断空/掩码，不发送该字段
      const newConfig: ApiConfig = {
        base_url: values.base_url,
        api_key: values.api_key || config.api_key,
        model: values.model,
        has_key: config.has_key || !!values.api_key,
      };
      onSave(newConfig);
      try { await saveConfigToDisk(newConfig); } catch { /* ignore */ }
      message.success('已保存');
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
          <Form.Item
            name="api_key"
            label="API Key"
            extra={config.has_key
              ? '已配置（留空保持不变，如需更换请输入新值）'
              : '请输入 API Key'}
          >
            <Input.Password placeholder={config.has_key ? '（留空保持不变）' : 'sk-xxxx'} />
          </Form.Item>
          <Form.Item name="model" label="模型" rules={[{ required: true }]}>
            <AutoComplete
              placeholder="选择或输入模型名"
              filterOption={(input, option) =>
                (option?.value ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={MODEL_SUGGESTIONS.map((v) => ({ value: v }))}
            />
          </Form.Item>
        </Form>
        <div style={{ color: '#999', fontSize: 12 }}>
          保存后同时存储到浏览器本地和后端磁盘（API Key 加密保存），无需每次填写。
        </div>
      </Modal>
    </>
  );
}
