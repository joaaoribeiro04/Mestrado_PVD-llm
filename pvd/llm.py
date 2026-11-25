"""Fábrica de LLMs (LangChain) agnóstica ao fornecedor + helpers de parsing.

get_llm() devolve None quando LLM_PROVIDER=none -> todo o pipeline tem um
caminho offline determinístico (úteis para reprodutibilidade e testes).
"""
import base64
import io
import json
import os
import re


def provider() -> str:
    return os.getenv("LLM_PROVIDER", "none").lower()


def get_llm(vision: bool = False):
    p = provider()
    if p == "none":
        return None
    model = os.getenv("LLM_VISION_MODEL" if vision else "LLM_MODEL") or None
    if vision and (model or "").lower() == "none":  # crítico visual desligado -> crítico heurístico
        return None
    if p == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model or "gemini-2.0-flash", temperature=0)
    if p == "groq":
        from langchain_groq import ChatGroq
        default = "meta-llama/llama-4-scout-17b-16e-instruct" if vision else "llama-3.3-70b-versatile"
        return ChatGroq(model=model or default, temperature=0)
    if p == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model or "gpt-4o-mini", temperature=0)
    if p == "ollama":
        from langchain_ollama import ChatOllama
        # num_ctx: o defeito do Ollama (2048 tokens) truncaria os prompts com código; ver .env
        return ChatOllama(model=model or ("qwen2.5vl:3b" if vision else "qwen2.5:7b"), temperature=0,
                          num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),
                          num_predict=256 if vision else 4096,
                          base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    raise ValueError(f"LLM_PROVIDER desconhecido: {p}")


def ask(llm, system: str, user: str, image_path: str | None = None) -> str:
    """Invoca um chat model com (opcionalmente) uma imagem PNG."""
    from langchain_core.messages import HumanMessage, SystemMessage
    content = [{"type": "text", "text": user}]
    if image_path:
        # Reduce large chart images before multimodal inference; preserves labels
        # at useful resolution while keeping CPU inference time manageable.
        from PIL import Image
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            image.thumbnail((1024, 1024))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=88, optimize=True)
        b64 = base64.b64encode(buffer.getvalue()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    out = llm.invoke([SystemMessage(content=system), HumanMessage(content=content)]).content
    if isinstance(out, list):  # alguns fornecedores devolvem blocos
        out = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in out)
    return out


def extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def extract_code(text: str) -> str | None:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, flags=re.DOTALL)
    return m.group(1).strip() if m else None
