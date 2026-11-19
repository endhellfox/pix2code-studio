# 🎨 Pix2Code Studio

基于 DeepSeek Vision API 的 UI 截图转代码与风格化重释工具。

## 💡 核心思路
现有截图转代码工具多追求“精准还原”，而本项目采用**结构解耦**的思路：
1. **结构提取**：利用 DeepSeek 的 `deepseek-flash` 提取纯粹的 UI 布局 JSON，剥离原图样式干扰。
2. **风格化生成**：将结构 JSON 和特定的“风格 Prompt”交给 `deepseek-chat`，生成不同视觉风格（极简白、赛博朋克、玻璃拟态等）的 HTML 代码。

## 🎬 演示
*(在这里放一张你截图或者录的GIF)*

## 🛠️ 本地运行
1. 安装依赖：`pip install -r requirements.txt`
2. 在根目录创建 `.env` 文件，写入 `DEEPSEEK_API_KEY=你的密钥`
3. 运行：`python app.py`

## 🔮 未来计划
- 支持导出 React / Vue 组件
- 引入“图生图”渲染，支持根据文字继续微调页面样式