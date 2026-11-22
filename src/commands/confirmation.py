"""
LOVIX Confirmation Safety Manager
Guards critical and destructive operations (shutdown, restart, deletion).
Requires an explicit follow-up "yes" from the user before executing.
"""

import logging
import subprocess

logger = logging.getLogger("LOVIX.Confirmation")


class ConfirmationManager:
    """Handles verification for sensitive actions."""

    def __init__(self, tts_engine=None):
        self.tts = tts_engine
        self._pending_action = None

    def request_confirmation(self, action_name: str):
        """Prepares a destructive action and prompts the user for verbal consent."""
        self._pending_action = action_name
        prompt = (
            f"Are you sure you want to {action_name}? "
            "Please say 'yes' to confirm, or 'cancel' to abort."
        )
        logger.warning(f"Safety prompt triggered for action: {action_name}")
        if self.tts:
            self.tts.speak(prompt)

    def process_confirmation(self, user_response: str) -> bool:
        """
        Validates the user's response to a pending confirmation request.
        Only executes if user explicitly confirms with 'yes' or 'confirm'.
        """
        if not self._pending_action:
            return False

        response = user_response.strip().lower()

        if response in ["yes", "confirm", "proceed", "do it"]:
            action = self._pending_action
            self._pending_action = None
            self._execute_action(action)
            return True
        else:
            self._pending_action = None
            if self.tts:
                self.tts.speak("Action cancelled.")
            return False

    def _execute_action(self, action: str):
        """Executes the confirmed action safely."""
        logger.warning(f"Executing confirmed critical action: {action}")
        if "shutdown" in action:
            if self.tts:
                self.tts.speak("Shutting down the computer now.")
            # subprocess.run(["shutdown", "/s", "/t", "10"])
        elif "restart" in action:
            if self.tts:
                self.tts.speak("Restarting the computer now.")
            # subprocess.run(["shutdown", "/r", "/t", "10"])
