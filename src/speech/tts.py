"""
LOVIX Offline Text-To-Speech (TTS)
Converts text responses to natural voice speech using Windows SAPI5 via pyttsx3.
100% offline, zero latency, zero cloud dependencies.
"""

import logging
from typing import Optional
import pyttsx3
from config.settings import TTS_RATE, TTS_VOLUME, TTS_VOICE_PREFERENCE

logger = logging.getLogger("LOVIX.TTS")


class TextToSpeech:
    """Manages offline speech synthesis via Windows native SAPI5 voices."""

    def __init__(
        self,
        rate: int = TTS_RATE,
        volume: float = TTS_VOLUME,
        voice_preference: Optional[str] = None,
    ):
        self.rate = rate
        self.volume = volume
        self.voice_preference = voice_preference if voice_preference is not None else TTS_VOICE_PREFERENCE
        self._selected_voice_id: Optional[str] = None
        self._engine = None

    def initialize(self) -> bool:
        """
        Initializes the pyttsx3 engine with the SAPI5 driver and configures
        speech rate, volume, and voice preference.

        Returns:
            bool: True if initialization and configuration succeeded, False otherwise.
        """
        logger.info("Initializing offline Text-To-Speech engine using SAPI5 driver...")
        try:
            self._engine = self._create_engine()
            logger.info("Text-To-Speech engine initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Text-To-Speech engine: {e}", exc_info=True)
            self._engine = None
            return False

    def _resolve_voice_id(self, engine) -> Optional[str]:
        """Finds the voice ID matching the preferred voice (e.g. Zira or David)."""
        try:
            voices = engine.getProperty("voices")
            if not voices:
                logger.warning("No SAPI5 voices discovered on this system.")
                return None

            chosen_voice = None
            if self.voice_preference:
                pref_lower = self.voice_preference.strip().lower()
                for voice in voices:
                    voice_name = getattr(voice, "name", "") or ""
                    voice_id = getattr(voice, "id", "") or ""
                    if pref_lower in voice_name.lower() or pref_lower in voice_id.lower():
                        chosen_voice = voice
                        break

            if chosen_voice:
                logger.info(f"Selected voice: {getattr(chosen_voice, 'name', chosen_voice.id)}")
                return chosen_voice.id
            else:
                default_voice = voices[0]
                logger.info(
                    f"Preferred voice '{self.voice_preference}' not found. "
                    f"Defaulting to: {getattr(default_voice, 'name', default_voice.id)}"
                )
                return default_voice.id
        except Exception as e:
            logger.warning(f"Could not discover SAPI5 voices: {e}")
            return None

    def _create_engine(self):
        """Creates a fresh, configured pyttsx3 SAPI5 engine instance."""
        engine = pyttsx3.init("sapi5")
        engine.setProperty("rate", self.rate)
        clamped_volume = max(0.0, min(1.0, float(self.volume)))
        engine.setProperty("volume", clamped_volume)

        if self._selected_voice_id is None:
            self._selected_voice_id = self._resolve_voice_id(engine)

        if self._selected_voice_id:
            try:
                engine.setProperty("voice", self._selected_voice_id)
            except Exception as e:
                logger.warning(f"Could not set voice property on engine: {e}")

        return engine

    def speak(self, text: str, block: bool = True):
        """
        Speaks the given text out loud through speakers using the offline TTS engine.
        Also displays the text in the console for user visibility.
        Fresh SAPI5 instance per utterance ensures every single response is audible without loop freezing.

        Args:
            text: The sentence or message to speak.
            block: If True, waits for speech playback to finish before returning.
        """
        print(f"\n[LOVIX]: {text}\n")
        if not text or not text.strip():
            return

        try:
            # Create a fresh engine instance per utterance to completely bypass
            # the known Windows SAPI5 event-loop lockup on subsequent speech calls
            engine = self._create_engine()
            engine.say(text)
            if block:
                engine.runAndWait()
            try:
                engine.stop()
            except Exception:
                pass
            del engine
        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}", exc_info=True)

    def stop(self):
        """Stops any active speech immediately."""
        if self._engine is not None:
            try:
                self._engine.stop()
                logger.info("TTS playback stopped.")
            except Exception as e:
                logger.warning(f"Error while stopping TTS engine: {e}")
