
from pathlib import Path

# Base paths
BASE_DIR    = Path(__file__).resolve().parent.parent
MODELS_DIR  = BASE_DIR / "models"

# ↳ SBERT model for similarity
HF_MODEL_EMBED = "sentence-transformers/all-MiniLM-L6-v2"

# ↳ Seq2Seq model for resume rewriting (either local or HF Hub)
HF_MODEL_GENERATION = "models/fast-flant5"

# Generation & gap settings
MAX_NEW_TOKENS = 800 # reduce from 2000 --> 1000, because a resume is around 500 words/ tokens

TOP_N_GAPS      = 10 # reduce from 20 --> 10, prevent overwhelming the model
