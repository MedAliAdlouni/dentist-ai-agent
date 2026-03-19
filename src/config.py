"""Configuration centralisée du projet receptai."""

# --- Modèles ---
AGENT_MODEL = "gemini-2.5-flash"
AGENT_TEMPERATURE = 0.3

JUDGE_MODEL = "gemini-2.5-pro"
JUDGE_TEMPERATURE = 0.1

TTS_MODEL = "gemini-2.5-flash-preview-tts"
TTS_VOICE = "Kore"
TTS_SAMPLE_RATE = 24000

WHISPER_MODEL = "medium"
WHISPER_COMPUTE_TYPE = "int8"

# --- Audio ---
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 2.0
MAX_RECORD_DURATION = 30

# --- Évaluation ---
DETERMINISTIC_WEIGHT = 0.4
LLM_WEIGHT = 0.6

# --- Splits dev / eval ---
# D2, D9, D14 moved to dev (used as few-shot examples in the prompt)
DEV_IDS = [1, 2, 3, 8, 9, 12, 14, 15]
EVAL_IDS = [4, 5, 6, 7, 10, 11, 13]
