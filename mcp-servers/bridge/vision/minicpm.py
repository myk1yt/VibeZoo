"""MiniCPM-V-4.6 GGUF Wrapper (using llama-cpp-python)"""
import os, base64, logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_vision_model = None

def _get_model_dir():
    return Path(__file__).parent.parent.parent.parent / "models"

def _get_model_path():
    # 우선적으로 4.6 오리지널 파일명 확인, 없으면 리네임된 파일명
    original_name = _get_model_dir() / "ggml-model-Q5_K_M.gguf"
    if original_name.exists():
        return original_name
    return _get_model_dir() / "MiniCPM-V-4_6-Q5_K_M.gguf"

def _get_mmproj_path():
    return _get_model_dir() / "mmproj-model-f16.gguf"

def is_available() -> bool:
    """MiniCPM-V 모델 사용 가능 여부 (GGUF + mmproj 존재 확인)"""
    if _vision_model is not None:
        return True
    try:
        import llama_cpp
        return _get_model_path().exists() and _get_mmproj_path().exists()
    except ImportError:
        return False

def load_model(model_path: Optional[str] = None, mmproj_path: Optional[str] = None):
    """MiniCPM-V 모델 로드 (llama-cpp-python)"""
    global _vision_model
    if _vision_model is not None:
        return _vision_model
    try:
        from llama_cpp import Llama
        
        if model_path is None:
            model_path = str(_get_model_path())
        if mmproj_path is None:
            mmproj_path = str(_get_mmproj_path())
        
        if not os.path.exists(model_path):
            logger.warning(f"Model not found: {model_path}")
            return None
        if not os.path.exists(mmproj_path):
            logger.warning(f"MMProj not found: {mmproj_path}")
            return None
        
        _vision_model = Llama(
            model_path=model_path,
            mmproj=mmproj_path,
            n_ctx=4096,
            n_threads=4,
            n_gpu_layers=0,
            verbose=False,
        )
        logger.info(f"Vision model loaded: {os.path.basename(model_path)}")
        return _vision_model
    except Exception as e:
        logger.error(f"Failed to load vision model: {e}")
        return None

def unload_model():
    global _vision_model
    _vision_model = None

def describe_image(image_path: str, question: Optional[str] = None) -> str:
    """이미지 설명 생성
    
    Args:
        image_path: 이미지 파일 경로
        question: 옵션 질문
    Returns:
        텍스트 설명
    """
    model = load_model()
    if model is None:
        return "⚠️ Vision model not loaded. Check model files."
    
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        prompt = question or "Describe this image in detail in Korean."
        
        response = model.create_chat_completion(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": prompt}
                ]
            }],
            max_tokens=512,
            temperature=0.7,
        )
        
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Vision inference failed: {e}")
        return f"⚠️ Analysis failed: {e}"
