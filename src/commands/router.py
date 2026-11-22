"""
LOVIX Command Router
Safely matches recognized spoken commands against an explicit allowlist.
NEVER runs arbitrary text as terminal commands or arbitrary Python code.
"""

import logging
from typing import Tuple, Optional, Callable
from src.commands.handlers import (
    handle_greeting,
    handle_time,
    handle_date,
    handle_launch_app,
    handle_system_status,
    handle_volume_control,
    handle_help,
)
from src.commands.confirmation import ConfirmationManager

logger = logging.getLogger("LOVIX.CommandRouter")


class CommandRouter:
    """Routes recognized speech intents to safe predefined handlers."""

    def __init__(self, tts_engine=None):
        self.tts = tts_engine
        self.confirmation_mgr = ConfirmationManager(tts_engine)

    def route_command(self, text: str) -> bool:
        """
        Analyzes spoken command text and triggers the appropriate safe action.
        Returns True if a command was matched and executed, False otherwise.
        """
        if not text:
            return False

        command = text.strip().lower()
        logger.info(f"Routing spoken command: '{command}'")

        # 1. Greetings & Identity
        if any(w in command for w in ["hello", "hi lovix", "introduce yourself", "who are you"]):
            response = handle_greeting()
            if self.tts:
                self.tts.speak(response)
            return True

        # 2. Time & Date
        if "time" in command:
            response = handle_time()
            if self.tts:
                self.tts.speak(response)
            return True

        if any(w in command for w in ["date", "today", "day is it"]):
            response = handle_date()
            if self.tts:
                self.tts.speak(response)
            return True

        # 3. System Status (Battery, RAM)
        if any(w in command for w in ["battery", "ram", "system status", "memory"]):
            response = handle_system_status()
            if self.tts:
                self.tts.speak(response)
            return True

        # 4. Application Launching (Strict Allowlist)
        if any(command.startswith(prefix) for prefix in ["open ", "launch ", "start "]):
            # Extracts application name and verifies against ALLOWED_APPLICATIONS
            response = handle_launch_app(command)
            if self.tts:
                self.tts.speak(response)
            return True

        # 5. Volume Controls
        if "volume" in command or "mute" in command:
            response = handle_volume_control(command)
            if self.tts:
                self.tts.speak(response)
            return True

        # 6. Help / What can you do
        if any(w in command for w in ["help", "what can you do", "commands"]):
            response = handle_help()
            if self.tts:
                self.tts.speak(response)
            return True

        # 7. Critical / Destructive Actions (Require explicit confirmation)
        if any(w in command for w in ["shutdown", "shut down", "restart"]):
            self.confirmation_mgr.request_confirmation(command)
            return True

        # 8. Unrecognized Command
        if self.tts:
            self.tts.speak("I didn't recognize that command. Say 'help' to hear what I can do.")
        return False
