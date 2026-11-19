import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 1. 读取第一步生成的布局 JSON
with open("layout.json", "r", encoding="utf-8") as f:
    layout_data = json.load(f)

# ==============================================================
# 🎨 选择你的视觉风格（每次运行前，修改这里的值即可）
# 可选值："赛博朋克", "极简白", "玻璃拟态", "像素复古"
# ==============================================================
STYLE = "玻璃拟态"  
# ==============================================================

STYLE_PROMPTS = {
    "赛博朋克": "使用极暗的黑色背景，加入高饱和度的霓虹粉、荧光蓝作为点缀。使用等宽字体，增加发光（box-shadow）效果，线条要锐利。",
    "极简白": "使用纯白背景，浅灰色边框，黑色文字。去除所有多余的装饰，使用大量留白（padding），圆角要小，呈现类似 Apple 的高级冷淡风。",
    "玻璃拟态": "使用鲜艳的渐变色背景，组件本身使用半透明白色（rgba），加上 backdrop-filter: blur 模糊效果，以及细白色的半透明边框。",
    "像素复古": "背景使用深绿色或深棕色，文字使用亮绿色或亮黄色，字体设置为 monospace，边框全部使用粗实线，不要圆角。"
}

style_instruction = STYLE_PROMPTS.get(STYLE, "保持现代简洁风格")

# 2. 构造发给大模型的 Prompt
prompt = f"""
你是一个资深前端工程师。请根据下面提供的 UI 结构化 JSON，还原一个单文件 HTML。

核心要求：
1. 所有 CSS 写在 <style> 标签里，不要使用外部 CSS 文件。
2. 灵活使用 Flexbox 或 CSS Grid 来布局。
3. 页面要撑满全屏（100vh）。
4. **强制视觉风格指令：{style_instruction}**
5. 只输出 HTML 代码，不要输出任何解释文字，不要使用 ```html 代码块包裹。

UI 结构 JSON：
{json.dumps(layout_data, ensure_ascii=False, indent=2)}
"""

print(f"正在生成 [{STYLE}] 风格的 HTML 代码，请稍候...\n")

# 3. 调用 API 生成代码
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个只输出纯 HTML 代码的机器，绝对不输出任何多余的解释。"},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3, # 温度调低，保证代码结构的稳定性
)

html_code = response.choices[0].message.content

# 4. 清洗模型可能多输出的代码块标记
cleaned_html = html_code.strip()
if cleaned_html.startswith("```html"):
    cleaned_html = cleaned_html.removeprefix("```html").removesuffix("```").strip()
elif cleaned_html.startswith("```"):
    cleaned_html = cleaned_html.removeprefix("```").removesuffix("```").strip()

# 5. 保存为 HTML 文件
with open("output.html", "w", encoding="utf-8") as f:
    f.write(cleaned_html)

print(f"✅ [{STYLE}] 风格代码生成成功！")
print("👉 请在左侧文件列表中双击打开 output.html 查看效果。")