"""
LOVIX Wake-Word Detector
Detects the spoken wake-word "Lovix" offline using Vosk recognition
and normalized phonetic matching without relying on external or cloud models.
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Optional
import vosk
from config.settings import WAKE_WORD, WAKE_WORD_VARIANTS, SAMPLE_RATE

logger = logging.getLogger("LOVIX.WakeWord")


class WakeWordDetector:
    """
    Offline wake-word detector for "Lovix".
    Attempts grammar-constrained recognition first, with safe fallback to
    open-vocabulary recognition if out-of-vocabulary words are rejected.
    """

    # Only approved, phonetically reasonable spellings for "Lovix"
    APPROVED_VARIANTS: List[str] = [
        "lovix",
        "lo vix",
        "low vix",
        "low vicks",
    ]

    def __init__(
        self,
        model=None,
        variants: Optional[List[str]] = None,
        sample_rate: int = SAMPLE_RATE,
    ):
        """
        Args:
            model: An initialized vosk.Model instance or path to the model directory.
            variants: Optional list of variants. Filtered against APPROVED_VARIANTS.
            sample_rate: Audio sampling frequency in Hz (default: 16000).
        """
        self.model = model
        self.sample_rate = sample_rate
        self.target_word = WAKE_WORD.lower() if WAKE_WORD else "lovix"

        # Restrict strictly to approved, reasonable wake-word spellings
        if variants is not None:
            filtered = [
                v.strip().lower()
                for v in variants
                if v.strip().lower() in self.APPROVED_VARIANTS
            ]
            self.variants = filtered if filtered else list(self.APPROVED_VARIANTS)
        else:
            self.variants = list(self.APPROVED_VARIANTS)

        self._recognizer: Optional[vosk.KaldiRecognizer] = None
        self._grammar_enabled: bool = False

    def initialize(self) -> bool:
        """
        Initializes the Vosk KaldiRecognizer.
        Attempts grammar-constrained recognition first. If the small English model
        rejects out-of-vocabulary words (e.g. 'lovix'), safely falls back to
        open-vocabulary recognition.

        Returns:
            bool: True if initialization succeeded, False otherwise.
        """
        logger.info("Initializing offline 'Lovix' wake-word detector...")
        if self.model is None:
            logger.error("Cannot initialize WakeWordDetector: No Vosk model provided.")
            return False

        try:
            # Load model instance if path string was provided
            if isinstance(self.model, (str, Path)):
                logger.info(f"Loading Vosk model from path: {self.model}")
                self.model = vosk.Model(str(self.model))

            # Attempt 1: Grammar-constrained recognition
            grammar_list = list(self.variants)
            if "[unk]" not in grammar_list:
                grammar_list.append("[unk]")
            grammar_json = json.dumps(grammar_list)

            try:
                logger.info("Attempting grammar-constrained recognizer for wake word...")
                self._recognizer = vosk.KaldiRecognizer(
                    self.model, float(self.sample_rate), grammar_json
                )
                self._grammar_enabled = True
                logger.info("Grammar-constrained wake-word recognizer initialized successfully.")
                return True
            except Exception as grammar_err:
                # The word "lovix" is an invented word not in the standard Vosk dictionary (words.txt).
                # Kaldi rejects grammars containing words missing from its pronunciation lexicon.
                logger.warning(
                    "Grammar-constrained recognition rejected target words: %s. "
                    "The word 'lovix' is likely missing from the Vosk model lexicon (words.txt). "
                    "Falling back safely to open-vocabulary recognizer with approved variant matching.",
                    grammar_err,
                )

            # Attempt 2: Fallback to open-vocabulary recognizer
            self._recognizer = vosk.KaldiRecognizer(self.model, float(self.sample_rate))
            self._grammar_enabled = False
            logger.info(
                "Open-vocabulary wake-word recognizer initialized as fallback. "
                "Listening for approved variants: %s",
                self.variants,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WakeWordDetector recognizer: {e}", exc_info=True)
            self._recognizer = None
            return False

    def process_audio(self, pcm_data: bytes) -> bool:
        """
        Processes an incoming block of raw PCM audio data.
        Returns True only when an approved wake-word spelling is detected.

        Args:
            pcm_data: Raw 16-bit mono PCM bytes from microphone stream.

        Returns:
            bool: True if wake word detected, False otherwise.
        """
        if not pcm_data:
            return False

        if self._recognizer is None:
            if not self.initialize():
                return False

        try:
            if self._recognizer.AcceptWaveform(pcm_data):
                res = json.loads(self._recognizer.Result())
                text = res.get("text", "").strip()
                if text and self.matches_wake_word(text):
                    logger.info(f"Wake word detected (completed utterance): '{text}'")
                    self.reset()
                    return True
            else:
                # Check partial result for low-latency wake-word triggering
                partial_res = json.loads(self._recognizer.PartialResult())
                partial_text = partial_res.get("partial", "").strip()
                if partial_text and self.matches_wake_word(partial_text):
                    logger.info(f"Wake word detected (streaming partial): '{partial_text}'")
                    self.reset()
                    return True

        except Exception as e:
            logger.error(f"Error processing audio in WakeWordDetector: {e}")

        return False

    def _normalize_text(self, text: str) -> str:
        """Removes punctuation and normalizes whitespace."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return " ".join(cleaned.split())

    def matches_wake_word(self, detected_text: str) -> bool:
        """
        Checks whether detected spoken text matches 'Lovix' or an approved spelling.
        Uses normalized, case-insensitive word-boundary matching.

        Args:
            detected_text: Text returned by speech recognizer.

        Returns:
            bool: True if an approved wake-word variant is found, False otherwise.
        """
        if not detected_text:
            return False

        norm_text = self._normalize_text(detected_text)
        if not norm_text:
            return False

        for variant in self.variants:
            norm_variant = self._normalize_text(variant)
            if not norm_variant:
                continue

            # Word-boundary regex ensures distinct word/phrase match
            pattern = rf"\b{re.escape(norm_variant)}\b"
            if re.search(pattern, norm_text):
                logger.debug(f"Wake-word matched: '{variant}' in '{detected_text}'")
                return True

        return False

    def reset(self):
        """Resets the recognizer state to avoid duplicate triggers on the same audio."""
        if self._recognizer is not None:
            try:
                if hasattr(self._recognizer, "Reset"):
                    self._recognizer.Reset()
                else:
                    _ = self._recognizer.FinalResult()
            except Exception as e:
                logger.warning(f"Error resetting wake-word recognizer state: {e}")

    @property
    def is_grammar_enabled(self) -> bool:
        """Returns True if running in grammar-constrained mode, False if open-vocabulary."""
        return self._grammar_enabled
