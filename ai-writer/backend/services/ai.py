"""DeepSeek AI 调用服务"""
import asyncio
import json
from typing import Optional

import httpx

from ..config import get_deepseek_key, DEEPSEEK_API_URL


async def call_deepseek(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> Optional[str]:
    """调用 DeepSeek API，返回 text content（不含 reasoning）"""
    key = get_deepseek_key()
    if not key:
        return None

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(1, 4):
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = 4 * attempt
            elif e.response.status_code >= 500:
                wait = 2 * attempt
            else:
                print(f"[AI] Http error: {e}")
                return None
            print(f"[AI] Retry {attempt}/3 after {wait}s: {e}")
        except httpx.TimeoutException:
            wait = 2 ** attempt * 3
        except Exception as e:
            print(f"[AI] Unexpected error: {e}")
            return None
        if attempt < 3:
            print(f"[AI] Retry {attempt}/3 after {wait}s")
            await asyncio.sleep(wait)


async def generate_agent_config(description: str) -> dict:
    """根据自然语言描述，让 AI 生成 system_prompt + capabilities"""
    system = """你是言灵创作引擎的 Agent 配置助理。
根据用户的描述，生成结构化的 Agent 配置。
必须以 JSON 格式返回，包含以下字段：
- agent_type: "creator" | "supervisor" | "reader"（自动判断）
- name: 建议的名称
- system_prompt: 详细的系统提示词（包含人设、能力、行为规则）
- capabilities: 能力列表（数组）
- temperature: float (0~1)，建议值
只返回 JSON，不要解释。"""

    result = await call_deepseek(system, description)
    if result:
        try:
            # 尝试提取 JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            parsed = json.loads(result)
            # 确保字段存在
            return {
                "agent_type": parsed.get("agent_type", "creator"),
                "name": parsed.get("name", ""),
                "system_prompt": parsed.get("system_prompt", result),
                "capabilities": parsed.get("capabilities", []),
                "temperature": parsed.get("temperature", 0.3),
            }
        except json.JSONDecodeError:
            # 如果解析失败，把原始内容作为 system_prompt
            return {
                "agent_type": _guess_type(description),
                "name": "",
                "system_prompt": result,
                "capabilities": [],
                "temperature": 0.3,
            }

    # AI 不可用时返回模拟数据
    return _mock_config(description)


def _guess_type(desc: str) -> str:
    d = desc.lower()
    if any(k in d for k in ["写作", "创作", "写文", "码字", "写小说"]):
        return "creator"
    if any(k in d for k in ["检查", "审校", "编辑", "批评", "修改", "把关"]):
        return "supervisor"
    if any(k in d for k in ["读者", "阅读", "体验", "反馈"]):
        return "reader"
    return "creator"


def _mock_config(desc: str) -> dict:
    """AI 不可用时的模拟生成"""
    agent_type = _guess_type(desc)
    names = {"creator": "创作者", "supervisor": "督查者", "reader": "读者"}
    return {
        "agent_type": agent_type,
        "name": f"智能{names[agent_type]}",
        "system_prompt": f"你是言灵创作引擎的{names[agent_type]}。\n\n{desc}\n\n请根据以上描述，以专业、细致的态度完成你的工作。",
        "capabilities": ["自然语言理解", "结构化输出"],
        "temperature": 0.3,
    }
