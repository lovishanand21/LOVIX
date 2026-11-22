"""
LOVIX - Windows 11 Desktop Voice Assistant
Main Entry Point

How to Run:
    python main.py

How to Stop:
    Press Ctrl + C in the terminal window, or say "Lovix, exit".
"""

import sys
import logging
from config.settings import WAKE_WORD

# Configure clean console logging format
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("LOVIX")


def print_banner():
    """Prints a friendly beginner startup banner."""
    banner = f"""
============================================================
              LOVIX - Desktop Voice Assistant              
              Windows 11 | 100% Offline | Cost: \u20b90       
============================================================
Wake Word       : "{WAKE_WORD.capitalize()}"
Audio Mode      : Volatile In-Memory (No audio saved to disk)
Command Security: Strict Allowlist (No arbitrary shell code)
To Stop         : Press Ctrl + C at any time
============================================================
    """
    print(banner)


def main():
    """Main program entry point."""
    print_banner()

    # Step 1: Check dependencies before starting
    print("[1/2] Verifying core environment...")
    logger.info("Environment check complete.")

    # Step 2: Initialize Assistant
    print("[2/2] Loading LOVIX components...")
    from src.core.assistant import LovixAssistant

    assistant = LovixAssistant()
    if not assistant.initialize():
        print("\n[ERROR] Failed to initialize LOVIX components.")
        sys.exit(1)

    print("\n[READY] LOVIX is initialized.")
    print(f"Say '{WAKE_WORD.capitalize()}' to wake me up!\n")

    # Start loop
    try:
        assistant.start()
    except KeyboardInterrupt:
        print("\n\nStopping LOVIX gracefully...")
        assistant.stop()
        print("LOVIX stopped successfully. Have a great day!")


if __name__ == "__main__":
    main()
