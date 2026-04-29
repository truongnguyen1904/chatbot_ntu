from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

_tokenizer: Optional[object] = None
_model: Optional[object] = None

_faq_matrix: Optional[np.ndarray] = None
_faq_intents: Optional[np.ndarray] = None
_faq_map_cache: Optional[Dict[str, List[str]]] = None


_MODEL_LOADED = False

def _ensure_model_loaded():
    global _model, _tokenizer, _MODEL_LOADED

    if _MODEL_LOADED:
        return

    print("Loading PhoBERT model...")

    try:
        from transformers import AutoTokenizer, AutoModel
        import torch

        device = torch.device("cpu")

        _tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
        _model = AutoModel.from_pretrained("vinai/phobert-base").to(device)

        _MODEL_LOADED = True

    except Exception as e:
        print("PhoBERT ERROR:", e)
        _model = None
        _tokenizer = None
        _MODEL_LOADED = True  # ❗ tránh load lại liên tục


def _encode_text(text: str) -> np.ndarray:
    text = (text or "").strip()
    _ensure_model_loaded()
    if not text:
        # type: ignore[union-attr]
        return np.zeros(_model.config.hidden_size, dtype=np.float32)

    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256,
    )

    import torch  # type: ignore

    with torch.no_grad():
        outputs = _model(**inputs)

    # [1, seq, hidden] -> mean pool -> [hidden]
    emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    return np.asarray(emb, dtype=np.float32)


def preload_faq(faq_map: Dict[str, List[str]]) -> None:
    """Precompute embeddings for all FAQ phrases (can be called lazily)."""
    global _faq_matrix, _faq_intents, _faq_map_cache
    _faq_map_cache = faq_map

    intents: list[str] = []
    rows: list[np.ndarray] = []

    for intent, phrases in faq_map.items():
        for phrase in phrases:
            phrase = (phrase or "").strip()
            if not phrase:
                continue
            intents.append(intent)
            rows.append(_encode_text(phrase))

    if not rows:
        _faq_matrix = None
        _faq_intents = None
        return

    _faq_matrix = np.vstack(rows)
    _faq_intents = np.array(intents, dtype=object)
    print(f"PhoBERT FAQ index: {_faq_matrix.shape[0]} phrases, {len(faq_map)} intents.")


def find_best_intent(user_input: str) -> Tuple[Optional[str], float]:
    """
    Return (intent_name, cosine_similarity) against preloaded FAQ phrases.
    Must call preload_faq() first.
    """
    if _faq_matrix is None or _faq_intents is None or len(_faq_intents) == 0:
        return None, 0.0

    user_emb = _encode_text(user_input).reshape(1, -1)
    sims = cosine_similarity(user_emb, _faq_matrix)[0]
    idx = int(np.argmax(sims))
    return str(_faq_intents[idx]), float(sims[idx])


def ensure_faq_loaded(faq_map: Dict[str, List[str]]) -> None:
    """Build FAQ index once, on first fallback call."""
    global _faq_matrix, _faq_intents, _faq_map_cache
    if _faq_matrix is not None and _faq_intents is not None and len(_faq_intents) > 0:
        return
    if _faq_map_cache is faq_map and _faq_matrix is not None:
        return
    preload_faq(faq_map)
