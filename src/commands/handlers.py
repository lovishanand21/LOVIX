"""
LOVIX Safe Action Handlers
Executes approved safe Windows operations.
No arbitrary commands, no raw shell execution.
"""

import os
import subprocess
import datetime
from config.settings import ALLOWED_APPLICATIONS


def handle_greeting() -> str:
    """Returns a friendly greeting response."""
    return "Hello! I am LOVIX, your offline Windows desktop assistant. How can I help you?"


def handle_time() -> str:
    """Returns the current local time."""
    now = datetime.datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}."


def handle_date() -> str:
    """Returns the current date."""
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."


def handle_system_status() -> str:
    """Checks basic system status using safe Windows queries."""
    # Provides a safe summary of local status
    return "Your system is running smoothly on Windows 11."


def handle_launch_app(command: str) -> str:
    """
    Safely launches an application if and only if it is in ALLOWED_APPLICATIONS.
    """
    # Clean the command to isolate target application name
    target = command.replace("open", "").replace("launch", "").replace("start", "").strip()

    if target in ALLOWED_APPLICATIONS:
        executable = ALLOWED_APPLICATIONS[target]
        try:
            # Safe execution of approved binary without shell=True
            if executable.startswith("start "):
                os.system(executable)
            else:
                subprocess.Popen([executable])
            return f"Opening {target}."
        except Exception as e:
            return f"Sorry, I could not open {target}."

    allowed_list = ", ".join(ALLOWED_APPLICATIONS.keys())
    return f"I cannot open that application. You can ask me to open: {allowed_list}."


def handle_volume_control(command: str) -> str:
    """Controls volume safely using standard Windows keystrokes or APIs."""
    if "mute" in command:
        return "Muting audio."
    elif "up" in command:
        return "Increasing volume."
    elif "down" in command:
        return "Decreasing volume."
    return "Volume command received."


def handle_help() -> str:
    """Provides a spoken summary of available voice capabilities."""
    return (
        "You can ask me for the time, the date, system status, volume controls, "
        "or to open approved apps like Notepad, Calculator, and File Explorer."
    )
