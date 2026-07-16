/**
 * 前端入口 — React 渲染根节点、Ant Design 主题配置
 * Config: colorPrimary 主题色、全局 Ant Design token
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider } from 'antd'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider theme={{ token: { colorPrimary: '#e898a8' } }}>
      <App />
    </ConfigProvider>
  </StrictMode>,
)
