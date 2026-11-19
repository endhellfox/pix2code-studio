import base64
import json
import os
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 提示词配置
VISION_PROMPT = """
你是一个 UI 结构解析器。请分析这张 UI 截图，输出严格合法的 JSON，不要输出任何其他文字。
你的任务只有一件事：提取布局结构和组件层级。不要描述颜色，不要描述具体的视觉样式。

JSON 结构必须严格如下：
{
  "layout": "一句话描述整体布局",
  "sections": [
    {
      "name": "区域名称，例如：navbar / sidebar / main-content",
      "children": [
        {"type": "组件类型，例如：logo / button / text", "text": "组件上的文字", "children": []}
      ]
    }
  ]
}
规则：只输出 JSON，不要包裹在 ```json 代码块里。
"""

STYLE_PROMPTS = {
    "赛博朋克": "使用极暗的黑色背景，加入高饱和度的霓虹粉、荧光蓝作为点缀。使用等宽字体，增加发光（box-shadow）效果，线条要锐利。",
    "极简白": "使用纯白背景，浅灰色边框，黑色文字。去除所有多余的装饰，使用大量留白（padding），圆角要小，呈现类似 Apple 的高级冷淡风。",
    "玻璃拟态": "使用鲜艳的渐变色背景，组件本身使用半透明白色（rgba），加上 backdrop-filter: blur 模糊效果，以及细白色的半透明边框。",
    "像素复古": "背景使用深绿色或深棕色，文字使用亮绿色或亮黄色，字体设置为 monospace，边框全部使用粗实线，不要圆角。"
}

# 核心生成函数
def process_image(image_path, style_choice):
    if image_path is None:
        return "请先上传图片", "", None

    try:
        # 1. 读图并 Base64 编码
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        # 2. Vision 阶段：提取结构
        vision_resp = client.chat.completions.create(
            model="deepseek-flash",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
        )
        
        raw_json = vision_resp.choices[0].message.content.strip()
        # 清洗可能存在的代码块标记
        if raw_json.startswith("```"):
            raw_json = raw_json.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        
        layout_data = json.loads(raw_json)

        # 3. Codegen 阶段：风格化生成 HTML
        style_instruction = STYLE_PROMPTS.get(style_choice, "保持现代简洁风格")
        codegen_prompt = f"""
        你是一个资深前端工程师。请根据提供的 UI 结构化 JSON，还原一个单文件 HTML。
        核心要求：
        1. 所有 CSS 写在 <style> 标签里。
        2. 页面撑满全屏（100vh）。
        3. 强制视觉风格指令：{style_instruction}
        4. 只输出 HTML 代码，不要输出任何解释文字，不要用代码块包裹。

        JSON:
        {json.dumps(layout_data, ensure_ascii=False)}
        """

        codegen_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个只输出纯 HTML 代码的机器。"},
                {"role": "user", "content": codegen_prompt}
            ],
            temperature=0.3,
        )
        
        html_code = codegen_resp.choices[0].message.content.strip()
        if html_code.startswith("```html"):
            html_code = html_code.removeprefix("```html").removesuffix("```").strip()

        # 返回三个结果：HTML用于预览，JSON用于展示中间态，HTML用于下载
        return html_code, layout_data, html_code

    except Exception as e:
        return f"生成失败：{str(e)}", {}, None


# 构建 Gradio UI 界面
with gr.Blocks(title="Pix2Code Studio") as demo:
    gr.Markdown("# 🎨 Pix2Code Studio")
    gr.Markdown("上传 UI 截图，提取结构并生成不同视觉风格的前端代码。")
    
    with gr.Row():
        # 左侧：输入区
        with gr.Column(scale=1):
            image_input = gr.Image(type="filepath", label="1. 上传 UI 截图")
            style_input = gr.Dropdown(
                choices=list(STYLE_PROMPTS.keys()), 
                value="极简白", 
                label="2. 选择视觉风格"
            )
            generate_btn = gr.Button("🚀 开始生成", variant="primary")
            
            # 用于展示提取出的 JSON 中间态
            json_display = gr.JSON(label="🔍 提取的中间层结构 (JSON)")

        # 右侧：输出区
        with gr.Column(scale=2):
            html_display = gr.HTML(label="🖥️ 实时预览")
            download_file = gr.File(label="📥 下载 HTML 代码")

    # 绑定按钮点击事件
    generate_btn.click(
        fn=process_image,
        inputs=[image_input, style_input],
        outputs=[html_display, json_display, download_file]
    )

if __name__ == "__main__":
    demo.launch()