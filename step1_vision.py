import base64
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ============================================================
# 你的截图文件路径，改成你自己的
IMAGE_PATH = r"C:\Users\25821\Pictures\ENDFIELD\ENDFIELD_SHARE_1785850691.png"
# ============================================================

# 读取图片并 Base64 编码
with open(IMAGE_PATH, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

# 关键 Prompt：只提取结构，不提取颜色和样式
# 这是为后面的“风格化生成”铺路
prompt = """
你是一个 UI 结构解析器。请分析这张 UI 截图，输出严格合法的 JSON，不要输出任何其他文字。

你的任务只有一件事：**提取布局结构和组件层级**。
不要描述颜色，不要描述字体大小，不要描述具体的视觉样式。只关心“有什么组件、它们怎么排列”。

JSON 结构必须严格如下：
{
  "layout": "一句话描述整体布局，例如：顶部导航栏 + 左侧侧边栏 + 右侧主内容区",
  "sections": [
    {
      "name": "区域名称，例如：navbar / sidebar / main-content / footer",
      "children": [
        {
          "type": "组件类型，例如：logo / nav-link / button / input / card / text / image",
          "text": "组件上的文字内容，如果没有则填空字符串",
          "children": []
        }
      ]
    }
  ]
}

规则：
- 只输出 JSON，不要包裹在 ```json 代码块里，不要加任何解释。
- 如果某个区域是嵌套的，用 children 递归表示。
- text 字段只填组件上可见的文字，不要自己编造。
"""

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64}"
                    },
                },
            ],
        }
    ],
)

raw = response.choices[0].message.content
print("=== 模型原始输出 ===")
print(raw)
print("\n")

# 清洗可能的代码块标记，然后解析
cleaned = raw.strip()
if cleaned.startswith("```"):
    cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    cleaned = cleaned.removesuffix("```").strip()

try:
    parsed = json.loads(cleaned)
    print("=== JSON 解析成功 ===")
    print(json.dumps(parsed, indent=2, ensure_ascii=False))

    # 保存到文件，下一步生成代码时要读它
    with open("layout.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    print("\n✅ 已保存到 layout.json")

except json.JSONDecodeError:
    print("=== JSON 解析失败 ===")
    print("模型没有返回纯 JSON。请检查上面的原始输出，把报错贴给我。")