"""
LOVIX Core Assistant Engine
Coordinates the continuous offline lifecycle state machine with Continuous Conversation Mode:
State 1: IDLE / STANDBY - Listening for wake word ("Lovix")
State 2: WAKE WORD DETECTED - Responds "Yes?" using Zira TTS
State 3: CONTINUOUS CONVERSATION SESSION:
         - Displays recognized user command in console
         - Executes safe action and speaks/prints response
         - Resets 15-second inactivity timer after each recognized command
         - Accepts multiple consecutive commands without repeating wake word
State 4: INACTIVITY TIMEOUT (15s elapsed without speech) -> Returns to State 1
"""

import time
import logging
from typing import Optional
from pathlib import Path
import vosk

from config.settings import VOSK_MODEL_PATH
from src.audio.mic_stream import AudioStreamManager
from src.wake_word.detector import WakeWordDetector
from src.speech.recognizer import SpeechRecognizer
from src.speech.tts import TextToSpeech
from src.commands.router import CommandRouter

logger = logging.getLogger("LOVIX.Core")

CONVERSATION_INACTIVITY_TIMEOUT: float = 15.0


class LovixAssistant:
    """Main coordinator class for the LOVIX desktop voice assistant."""

    def __init__(self):
        self.audio_manager = AudioStreamManager()
        self.tts = TextToSpeech()
        self.router = CommandRouter(tts_engine=self.tts)
        self.wake_detector = WakeWordDetector()
        self.recognizer = SpeechRecognizer()
        self._vosk_model: Optional[vosk.Model] = None
        self._is_running = False

    def initialize(self) -> bool:
        """
        Initializes all LOVIX components:
        1. Initializes offline Text-to-Speech (pyttsx3 / Windows SAPI5 with Zira voice).
        2. Loads the local Vosk model exactly once from VOSK_MODEL_PATH.
        3. Shares the loaded model instance with WakeWordDetector and SpeechRecognizer.
        4. Initializes the wake-word detector and speech recognizer.

        Returns:
            bool: True if all components initialized successfully, False otherwise.
        """
        logger.info("Initializing LOVIX Assistant core systems...")

        # 1. Initialize Text-to-Speech engine
        if not self.tts.initialize():
            logger.error("Failed to initialize Text-To-Speech engine.")
            return False

        # 2. Validate model path and load Vosk model exactly once into RAM
        model_path = Path(VOSK_MODEL_PATH)
        if not model_path.exists():
            logger.error(
                f"Vosk model path not found at: {model_path}. "
                "Please ensure the model is placed in the models directory."
            )
            return False

        logger.info(f"Loading offline Vosk model from: {model_path}")
        try:
            self._vosk_model = vosk.Model(str(model_path))
            logger.info("Vosk model loaded into memory successfully.")
        except Exception as e:
            logger.error(f"Failed to load Vosk model from {model_path}: {e}", exc_info=True)
            return False

        # 3. Pass the single shared model instance to WakeWordDetector
        self.wake_detector.model = self._vosk_model
        if not self.wake_detector.initialize():
            logger.error("Failed to initialize WakeWordDetector.")
            return False

        # 4. Pass the single shared model instance to SpeechRecognizer
        self.recognizer.model = self._vosk_model
        if not self.recognizer.initialize():
            logger.error("Failed to initialize SpeechRecognizer.")
            return False

        logger.info("All LOVIX core components initialized successfully.")
        return True

    def start(self):
        """
        Starts the continuous listening lifecycle.
        - Spawns a single microphone input stream.
        - Continuously monitors audio for the wake word 'Lovix'.
        - When wake word is heard, enters Continuous Conversation Mode.
        """
        if self._is_running:
            logger.warning("LOVIX Assistant is already running.")
            return

        logger.info("Starting LOVIX Assistant main loop...")

        # Start single microphone stream
        if not self.audio_manager.start():
            logger.error("Failed to start microphone stream. Aborting assistant startup.")
            return

        self._is_running = True
        self.tts.speak("Lovix is ready and listening for wake word.")

        try:
            while self._is_running:
                # State 1: Standby - Listen for wake word ("Lovix")
                audio_chunk = self.audio_manager.get_audio_chunk(timeout=0.5)
                if audio_chunk is None:
                    continue

                if self.wake_detector.process_audio(audio_chunk):
                    logger.info("Wake word 'Lovix' detected! Starting conversation session...")

                    # State 2: Clear pre-trigger audio and prompt user with Zira voice
                    self.audio_manager.clear_queue()
                    self.tts.speak("Yes?", block=True)

                    # Clear microphone buffer again to avoid capturing assistant's own voice/echo
                    self.audio_manager.clear_queue()
                    self.wake_detector.reset()

                    # State 3: Enter Continuous Conversation Mode
                    self._run_conversation_session(inactivity_timeout=CONVERSATION_INACTIVITY_TIMEOUT)

                    # State 4: Clear queue & reset wake detector before resuming standby
                    self.audio_manager.clear_queue()
                    self.wake_detector.reset()
                    logger.info("Standby mode resumed: Listening for wake word ('Lovix').")

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received in LOVIX main loop.")
        except Exception as e:
            logger.error(f"Unexpected error in LOVIX main loop: {e}", exc_info=True)
        finally:
            self.stop()

    def _run_conversation_session(self, inactivity_timeout: float = CONVERSATION_INACTIVITY_TIMEOUT):
        """
        Manages an active multi-turn conversation session.
        Allows the user to speak multiple commands without repeating the wake word.
        Displays user commands in the console and speaks all responses via Zira TTS.
        Automatically exits to wake-word standby if no command is detected for inactivity_timeout seconds.
        """
        logger.info(
            f"--- Conversation Mode Active: Listening for commands (Inactivity Timeout: {inactivity_timeout}s) ---"
        )
        last_activity_time = time.time()

        while self._is_running:
            elapsed_since_activity = time.time() - last_activity_time
            remaining_time = inactivity_timeout - elapsed_since_activity

            # Check if 15 seconds of inactivity have elapsed
            if remaining_time <= 0:
                logger.info(
                    f"Conversation session timed out after {inactivity_timeout:.1f}s of inactivity. "
                    "Returning to wake-word standby."
                )
                self.tts.speak("Returning to standby.", block=True)
                self.audio_manager.clear_queue()
                break

            # Listen for command, capping the listen window to remaining inactivity time
            listen_timeout = min(5.0, remaining_time)
            command_text = self.recognizer.listen_for_command(
                self.audio_manager, timeout_seconds=listen_timeout
            )

            # Check if assistant was stopped during listening
            if not self._is_running:
                break

            if command_text and command_text.strip():
                # Display the recognized user command in console
                print(f"\n[USER]: {command_text}")
                logger.info(f"Command recognized in session: '{command_text}'")

                # Check for explicit session termination commands
                cleaned_cmd = command_text.strip().lower()
                if any(phrase in cleaned_cmd for phrase in ["stop listening", "go to sleep", "sleep", "goodbye", "bye", "cancel"]):
                    logger.info("User requested to end active conversation session.")
                    self.tts.speak("Returning to standby.", block=True)
                    self.audio_manager.clear_queue()
                    break

                if any(phrase in cleaned_cmd for phrase in ["exit lovix", "exit program", "quit lovix", "quit"]):
                    logger.info("User requested to stop LOVIX.")
                    self.stop()
                    break

                # Dispatch safe command through router (prints response & speaks via Zira TTS)
                self.router.route_command(command_text)

                # Clear microphone audio buffer after speech finishes so LOVIX does not hear itself
                self.audio_manager.clear_queue()

                # Reset the 15-second inactivity timer after a successfully recognized command
                last_activity_time = time.time()
                logger.info(
                    f"Inactivity timer reset. LOVIX is still listening for another command ({inactivity_timeout}s window)..."
                )
            else:
                # No speech detected in this listen chunk; continue waiting until inactivity_timeout expires
                logger.debug(
                    f"No command speech detected in chunk. {remaining_time:.1f}s remaining in session."
                )

        logger.info("--- Conversation Mode Ended: Standby mode resumed ('Lovix') ---")

    def stop(self):
        """Stops the assistant cleanly, shutting down microphone capture and TTS."""
        if not self._is_running:
            return

        logger.info("Stopping LOVIX Assistant...")
        self._is_running = False

        # Stop microphone capture stream
        if self.audio_manager is not None:
            try:
                self.audio_manager.stop()
            except Exception as e:
                logger.warning(f"Error stopping microphone manager: {e}")

        # Stop and speak shutdown notice
        if self.tts is not None:
            try:
                self.tts.speak("Lovix is going to sleep. Goodbye.", block=True)
                self.tts.stop()
            except Exception as e:
                logger.warning(f"Error stopping TTS engine: {e}")

        logger.info("LOVIX Assistant stopped successfully.")

    @property
    def is_running(self) -> bool:
        """Returns True if the assistant is currently running."""
        return self._is_running
