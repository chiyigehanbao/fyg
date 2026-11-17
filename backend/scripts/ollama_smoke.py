"""手动验证本地 Ollama 配置与一次结构化推理。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import load_settings
from app.services.llm import ModelError, chat_completion


async def main() -> None:
    settings = load_settings()
    try:
        result = await chat_completion(
            settings,
            system="你只输出一个 JSON 对象。",
            user='请输出 {"status":"ok","message":"本地模型已接通"}',
            timeout_s=90.0,
        )
    except ModelError as exc:
        print(
            "Ollama smoke check failed.\n"
            f"base_url={settings.ollama_base_url}\n"
            f"model={settings.ollama_model}\n"
            "Please start Ollama and confirm the model is installed.",
        )
        raise SystemExit(1) from None
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
