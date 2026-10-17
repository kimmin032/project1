"""OpenRouter에 질문을 보내고 답을 받아오는 파일.

API 키는 .env 파일에서만 읽고, 이 파일 밖으로 내보내지 않는다.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()  # MODEL을 읽기 전에 .env를 먼저 불러온다

# 사용할 모델. .env의 OPENROUTER_MODEL이 있으면 그걸, 비어 있으면 수업에서 쓴 무료 모델을 쓴다.
MODEL = os.getenv("OPENROUTER_MODEL") or "nvidia/nemotron-3-super-120b-a12b:free"

API_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_SECONDS = 60


class LLMError(Exception):
    """AI 호출이 실패했을 때 쓰는 에러. 메시지에는 키가 절대 들어가지 않는다."""


def ask_llm(prompt: str, system: str = "") -> str:
    """AI에게 질문(prompt)을 보내고 답변 글자(str)를 돌려준다."""
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise LLMError(".env 파일에 OPENROUTER_API_KEY가 없습니다.")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": MODEL, "messages": messages},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        raise LLMError("AI 서버에 연결하지 못했습니다. 인터넷 연결을 확인해 주세요.") from None

    if response.status_code != 200:
        raise LLMError(f"AI 호출 실패 (상태 코드 {response.status_code}). 키와 모델 이름을 확인해 주세요.")

    try:
        return response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError):
        raise LLMError("AI 응답 형식이 예상과 달랐습니다.") from None


if __name__ == "__main__":
    # 터미널에서 `python llm_client.py` 로 직접 실행했을 때만 도는 간단 테스트
    try:
        print(ask_llm("안녕! 한 문장으로 자기소개 해줘."))
    except LLMError as e:
        print(f"[오류] {e}")
