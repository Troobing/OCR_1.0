/**
 * 结果渲染 — 将 LLM 提取的混合文字+LaTeX 公式文本渲染为可视化内容
 * 负责：公式渲染、表格渲染、HTML 转义
 * Config: KaTeX 参数、正则匹配规则
 * （提取结果显示区，含公式 + Markdown 表格渲染）
 * Skill：KaTeX、dangerouslySetInnerHTML、正则
 */


import { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import './ResultViewer.css';
import { extractFormulas, blockPlaceholder, inlinePlaceholder } from '../services/formula';
import { extractTables, tablePlaceholder, markdownTableToHtml } from '../services/markdownTable';

interface Props {
  content: string;
}

function renderFormula(formula: string, displayMode: boolean): string {
  // throwOnError:false 保证 KaTeX 不会抛异常；出错时它返回红色错误节点，无需 try/catch
  return katex.renderToString(formula, { displayMode, throwOnError: false });
}

export default function ResultViewer({ content }: Props) {
  const html = useMemo(() => {
    if (!content) return '';

    // 抽取顺序：先公式后表格——这样表格单元格里的 $...$ 公式会被先占位，
    // 表格 HTML 里保留占位符，最后回填公式时能正确替换（天然支持表格嵌公式）
    const { text: text1, blocks, inlines } = extractFormulas(content);
    const { text: text2, tables } = extractTables(text1);

    let escaped = text2
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br/>');

    blocks.forEach((f, i) => {
      escaped = escaped.replace(blockPlaceholder(i), renderFormula(f, true));
    });
    inlines.forEach((f, i) => {
      escaped = escaped.replace(inlinePlaceholder(i), renderFormula(f, false));
    });
    tables.forEach((t, i) => {
      escaped = escaped.replace(tablePlaceholder(i), markdownTableToHtml(t));
    });

    return escaped;
  }, [content]);

  return (
    <div
      className="result-viewer"
      dangerouslySetInnerHTML={{ __html: html }}
      style={{ fontSize: 15, lineHeight: 1.8, wordBreak: 'break-word', padding: '12px 0' }}
    />
  );
}
