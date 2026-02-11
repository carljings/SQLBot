"""
Moonshot AI API 测试脚本
运行前请设置环境变量: export MOONSHOT_API_KEY=your_api_key
"""
import os
import sys
from openai import OpenAI

# 设置 UTF-8 编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_moonshot_api():
    """测试 Moonshot AI API 调用"""

    # 从环境变量获取 API Key
    api_key = os.environ.get("MOONSHOT_API_KEY")
    api_key = "sk-4cKvYZGyTFufrCG5Je3VPG4AHUKndYOtPF1b6daZ9dwT5OOc"

    if not api_key:
        print("❌ 错误: 请先设置 MOONSHOT_API_KEY 环境变量")
        print("   Windows: set MOONSHOT_API_KEY=your_key")
        print("   Linux/Mac: export MOONSHOT_API_KEY=your_key")
        return

    # 创建客户端
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1",
    )

    print("🚀 正在调用 Moonshot AI API...")

    try:
        # 发送聊天请求
        completion = client.chat.completions.create(
            model="kimi-k2-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。"
                },
                {
                    "role": "user",
                    "content": "你好，我叫李雷，1+1等于多少？"
                }
            ],
            temperature=0.6,
        )

        # 打印响应
        print("\n✅ API 调用成功!")
        print("-" * 50)
        print("📝 响应内容:")
        print(completion.choices[0].message.content)
        print("-" * 50)

        # 打印详细信息
        print(f"\n📊 详细信息:")
        print(f"   模型: {completion.model}")
        print(f"   Token 使用: {completion.usage.total_tokens} (输入: {completion.usage.prompt_tokens}, 输出: {completion.usage.completion_tokens})")
        print(f"   完成原因: {completion.choices[0].finish_reason}")

    except Exception as e:
        print(f"\n❌ API 调用失败: {e}")


def test_sqlbot_integration():
    """测试与 SQLBot 集成 (Text-to-SQL)"""
    api_key = os.environ.get("MOONSHOT_API_KEY")
    api_key = "sk-4cKvYZGyTFufrCG5Je3VPG4AHUKndYOtPF1b6daZ9dwT5OOc"

    if not api_key:
        print("错误: 请先设置 MOONSHOT_API_KEY 环境变量")
        return

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1",
    )

    print("\n🔍 测试 SQL 生成能力...")

    try:
        completion = client.chat.completions.create(
            model="kimi-k2-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个 SQL 专家，负责将自然语言转换为 SQL 查询语句。"
                },
                {
                    "role": "user",
                    "content": "帮我写一个 SQL 查询：查询所有销售额大于 1000 的订单，按日期降序排列。"
                }
            ],
            temperature=0.3,
        )

        print("\n✅ SQL 生成成功!")
        print("-" * 50)
        print(completion.choices[0].message.content)
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ SQL 生成失败: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("Moonshot AI API 测试")
    print("=" * 50)

    # 基础测试
    test_moonshot_api()

    # SQL 生成测试
    test_sqlbot_integration()

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
