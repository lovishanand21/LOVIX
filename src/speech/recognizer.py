"""
LOVIX Offline Speech Recognizer
Converts user spoken voice commands to text using the local Vosk model.
Completely offline, private, zero cost.
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional
import vosk

logger = logging.getLogger("LOVIX.SpeechRecognizer")


class SpeechRecognizer:
    """Handles full-vocabulary speech recognition for spoken commands."""

    def __init__(self, model=None, sample_rate: int = 16000):
        """
        Args:
            model: An initialized vosk.Model instance or path to the local model folder.
            sample_rate: Expected audio sample rate in Hz (default: 16000).
        """
        self.model = model
        self.sample_rate = sample_rate
        self._recognizer: Optional[vosk.KaldiRecognizer] = None

    def initialize(self) -> bool:
        """
        Initializes the Vosk command recognizer with full vocabulary using the loaded model.

        Returns:
            bool: True if initialization succeeded, False otherwise.
        """
        logger.info("Initializing offline speech-to-text recognizer...")
        if self.model is None:
            logger.error("Cannot initialize SpeechRecognizer: No Vosk model provided.")
            return False

        try:
            # If a model path was passed, load the vosk.Model instance
            if isinstance(self.model, (str, Path)):
                logger.info(f"Loading Vosk model from path: {self.model}")
                self.model = vosk.Model(str(self.model))

            self._recognizer = vosk.KaldiRecognizer(self.model, float(self.sample_rate))
            logger.info(f"Vosk KaldiRecognizer initialized successfully at {self.sample_rate} Hz.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Vosk KaldiRecognizer: {e}", exc_info=True)
            self._recognizer = None
            return False

    def listen_for_command(
        self, audio_source, timeout_seconds: float = 5.0
    ) -> Optional[str]:
        """
        Listens to the audio stream until a command is spoken, followed by a pause.
        Uses AcceptWaveform() to detect completed speech and PartialResult() to track activity.

        Args:
            audio_source: An AudioStreamManager instance with get_audio_chunk().
            timeout_seconds: Maximum seconds to wait before speech begins (default: 5.0).

        Returns:
            str: Recognized command text, or None if no speech was detected.
        """
        if self._recognizer is None:
            if not self.initialize():
                logger.error("SpeechRecognizer is not initialized; cannot listen.")
                return None

        # Reset recognizer state to ensure a clean buffer for the new command
        try:
            if hasattr(self._recognizer, "Reset"):
                self._recognizer.Reset()
            else:
                _ = self._recognizer.FinalResult()
        except Exception as e:
            logger.warning(f"Error resetting recognizer state: {e}")

        logger.info(f"Listening for spoken command (timeout: {timeout_seconds}s)...")

        start_time = time.time()
        has_started_speaking = False
        last_speech_time = start_time
        silence_timeout_after_speech = 1.2  # Seconds of silence after speech before finalizing
        max_duration = timeout_seconds + 5.0  # Safety upper bound for long utterances

        try:
            while True:
                current_time = time.time()

                # Timeout Case 1: Overall timeout if user never began speaking
                if not has_started_speaking and (current_time - start_time >= timeout_seconds):
                    logger.info("Command listening timed out: No speech detected.")
                    return None

                # Timeout Case 2: Silence detected after speech was already in progress
                if has_started_speaking and (current_time - last_speech_time >= silence_timeout_after_speech):
                    logger.debug("Silence endpoint reached after speech. Finalizing command...")
                    try:
                        final_res = json.loads(self._recognizer.FinalResult())
                        text = final_res.get("text", "").strip()
                        if text:
                            logger.info(f"Command recognized: '{text}'")
                            return text
                    except Exception as e:
                        logger.warning(f"Error finalizing speech result: {e}")
                    return None

                # Timeout Case 3: Safety cap to prevent indefinite speech buffer
                if has_started_speaking and (current_time - start_time >= max_duration):
                    logger.info("Maximum speaking duration reached. Finalizing command...")
                    try:
                        final_res = json.loads(self._recognizer.FinalResult())
                        text = final_res.get("text", "").strip()
                        if text:
                            logger.info(f"Command recognized: '{text}'")
                            return text
                    except Exception as e:
                        logger.warning(f"Error finalizing speech result: {e}")
                    return None

                # Read next audio chunk from existing audio queue
                chunk = audio_source.get_audio_chunk(timeout=0.2)
                if not chunk:
                    continue

                # Process chunk through Kaldi recognizer
                try:
                    if self._recognizer.AcceptWaveform(chunk):
                        # Kaldi reached an utterance endpoint internally
                        result = json.loads(self._recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            logger.info(f"Command recognized: '{text}'")
                            return text
                    else:
                        # Inspect partial recognition to track speech activity (never return partial text directly)
                        partial_data = json.loads(self._recognizer.PartialResult())
                        partial_text = partial_data.get("partial", "").strip()
                        if partial_text:
                            if not has_started_speaking:
                                logger.debug(f"User started speaking: '{partial_text}'")
                                has_started_speaking = True
                            last_speech_time = time.time()
                except Exception as e:
                    logger.error(f"Error processing audio waveform chunk: {e}")

        except Exception as e:
            logger.error(f"Unexpected error while listening for command: {e}", exc_info=True)
            return None
