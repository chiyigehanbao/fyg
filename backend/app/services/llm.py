"""本地 Ollama 对话与状态检测。"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings


class ModelError(Exception):
    """本地模型不可用、返回错误或响应结构异常。"""


async def chat_completion(
    settings: Settings,
    *,
    system: str,
    user: str,
    timeout_s: float = 180.0,
    num_predict: int = 2048,
) -> str:
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "think": False,
        "keep_alive": settings.ollama_keep_alive,
        "options": {
            "temperature": 0.15,
            "num_ctx": 16384,
            "num_predict": num_predict,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(url, json=payload)
    except httpx.ConnectError as exc:
        raise ModelError(
            f"无法连接本地 Ollama：{settings.ollama_base_url}",
        ) from exc
    except httpx.TimeoutException as exc:
        raise ModelError(
            f"本地模型 {settings.ollama_model} 响应超时",
        ) from exc

    if response.status_code >= 400:
        detail = response.text[:500]
        raise ModelError(
            f"Ollama HTTP {response.status_code}: {detail}",
        )

    try:
        data = response.json()
        content = str(data["message"]["content"]).strip()
    except (ValueError, KeyError, TypeError) as exc:
        raise ModelError("Ollama 返回了无法识别的响应结构") from exc
    if not content:
        raise ModelError("Ollama 返回内容为空")
    return content


async def model_status(settings: Settings, timeout_s: float = 1.5) -> dict[str, Any]:
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.ConnectError:
        return {
            "connected": False,
            "model": settings.ollama_model,
            "available": False,
            "provider": "ollama",
            "error": "connect_error",
        }
    except httpx.TimeoutException:
        return {
            "connected": False,
            "model": settings.ollama_model,
            "available": False,
            "provider": "ollama",
            "error": "timeout",
        }
    except httpx.HTTPStatusError as exc:
        return {
            "connected": False,
            "model": settings.ollama_model,
            "available": False,
            "provider": "ollama",
            "error": f"http_{exc.response.status_code}",
        }
    except (httpx.HTTPError, ValueError):
        return {
            "connected": False,
            "model": settings.ollama_model,
            "available": False,
            "provider": "ollama",
            "error": "invalid_response",
        }

    names = {
        str(item.get("name") or item.get("model") or "")
        for item in data.get("models", [])
        if isinstance(item, dict)
    }
    expected = settings.ollama_model
    available = expected in names or f"{expected}:latest" in names
    return {
        "connected": True,
        "model": expected,
        "available": available,
        "provider": "ollama",
        "models": sorted(name for name in names if name),
        "error": None if available else "model_not_found",
    }
