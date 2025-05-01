
from pathlib import Path

# Base paths
BASE_DIR    = Path(__file__).resolve().parent.parent
MODELS_DIR  = BASE_DIR / "models"

# ↳ SBERT model for similarity
HF_MODEL_EMBED = "sentence-transformers/all-MiniLM-L6-v2"

# ↳ Seq2Seq model for resume rewriting (either local or HF Hub)
HF_MODEL_GENERATION = "models/fast-flant5"

# Generation & gap settings
MAX_NEW_TOKENS = 1200

TOP_N_GAPS      = 20
