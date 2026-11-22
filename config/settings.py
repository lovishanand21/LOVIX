"""
LOVIX Assistant - Central Settings and Allowlist
All configurations are defined here for safety, clarity, and easy modification.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
VOSK_MODEL_PATH = MODELS_DIR / "vosk-model-small-en-us-0.15"

# Audio Settings
SAMPLE_RATE = 16000  # 16 kHz mono PCM required by Vosk
CHANNELS = 1         # Mono audio
BLOCK_SIZE = 4000    # Audio buffer block size (approx. 0.25 seconds per chunk)

# Wake Word Settings
WAKE_WORD = "lovix"
# Acoustic / phonetic variants captured when saying "Lovix" offline:
WAKE_WORD_VARIANTS = [
    "lovix",
    "lo vics",
    "lo vicks",
    "love icks",
    "love x",
    "lovis",
    "lo vits",
    "low vicks",
]

# Speech-to-Text Settings
SILENCE_TIMEOUT_SECONDS = 3.0  # Max silence before considering speech ended

# Text-to-Speech (pyttsx3 / Windows SAPI5) Settings
TTS_RATE = 175        # Words per minute (150-200 is natural)
TTS_VOLUME = 1.0      # Master volume (0.0 to 1.0)
TTS_VOICE_PREFERENCE = "Zira"  # "Zira" or "David" (built-in Windows 11 voices)

# Security & Safety Allowlist: Approved Windows Applications
# Maps friendly user-spoken names to safe Windows executable names
ALLOWED_APPLICATIONS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "task manager": "taskmgr.exe",
    "settings": "start ms-settings:",
}

# Critical Commands that REQUIRE explicit confirmation
CRITICAL_COMMANDS = {
    "shutdown": "Are you sure you want to shut down your computer? Please say yes to confirm or cancel.",
    "restart": "Are you sure you want to restart your computer? Please say yes to confirm or cancel.",
    "sleep computer": "Are you sure you want to put your computer to sleep? Please say yes to confirm or cancel.",
}
