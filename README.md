# LOVIX — Offline Windows 11 Desktop Voice Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011-0078D4.svg)](https://microsoft.com)
[![Budget: ₹0](https://img.shields.io/badge/Cost-Strictly%20%E2%82%B90-success.svg)](#)
[![Privacy: 100% Offline](https://img.shields.io/badge/Privacy-100%25%20Offline-brightgreen.svg)](#)

LOVIX is a 100% free, private, and fully offline desktop voice assistant built specifically for Windows 11. It continuously listens for the wake word **"Lovix"**, processes spoken commands entirely on your local machine, executes approved Windows operations, and responds with speech.

---

## 🌟 Key Highlights

- **Strictly ₹0 Budget**: No paid APIs, no subscriptions, no credit card requirements, no hidden fees.
- **100% Offline & Private**: Zero audio data or telemetry leaves your computer. Your microphone audio is processed in volatile memory and never recorded to disk or uploaded to the cloud.
- **Custom Wake Word ("Lovix")**: Uses offline keyword and grammar spotting with phonetic matching so you don't need any paid or proprietary wake-word models.
- **Native Windows Speech Synthesis**: Uses Windows SAPI5 via `pyttsx3` for instant, natural, offline voice feedback.
- **Safe Command Allowlist**: Arbitrary speech is never passed directly into the command prompt or terminal. All actions are strictly validated against an approved list.
- **Destructive Action Protection**: Commands like shutdown, restart, or file deletion require explicit verbal confirmation before execution.
- **Beginner-Friendly Architecture**: Clean, modular Python code designed for users with zero prior coding experience.

---

## 📐 Architecture Overview

```
 [Microphone] 🎤
      │ (16kHz 16-bit Mono PCM stream via sounddevice)
      ▼
 [Audio Stream Buffer] ──► Queue (Thread-Safe)
      │
      ▼
 [Wake-Word Detector] ──► Listens specifically for "Lovix" (Phonetic Grammar Spotter)
      │
   "Lovix" Detected!
      │
      ├─► Audio Prompt / Chime ("Yes?")
      ▼
 [Command Speech Recognizer] ──► Offline Vosk STT converts your spoken words into text
      │
      ▼
 [Safe Command Router]
      │
      ├─── Matches Allowed Intent? ──► NO ──► Speech: "I didn't understand that command."
      │
      ├─── Destructive Action? ──────► YES ─► Confirmation Prompt: "Are you sure? Say yes or cancel."
      │                                            │
      │                                            └─► Confirmed? ─► Execute Action
      ▼
 [Windows Native Action Handler] ────► Opens App / Reports Time / Controls Volume / System Info
      │
      ▼
 [Text-To-Speech (TTS)] ─────────────► Offline Speech Response via Windows SAPI5 🔊
```

---

## 💻 Hardware & Software Requirements

| Requirement | Recommended / Detected |
|---|---|
| **Operating System** | Windows 11 (64-bit) |
| **RAM** | 16 GB (Lovix uses < 250 MB) |
| **Python** | Python 3.12 (Detected: Python 3.12.10) |
| **Audio Input** | Working microphone / headset |
| **Audio Output** | Speakers or headphones |
| **Internet** | Only required once to download free open-source packages and the small Vosk model (~40 MB) |

---

## 📂 Project Structure

```
LOVIX/
├── config/
│   ├── __init__.py
│   └── settings.py          # Central configurations (sample rates, paths, volume, thresholds)
├── models/
│   └── README.md            # Guide for placing the offline Vosk speech model
├── src/
│   ├── __init__.py
│   ├── audio/
│   │   ├── __init__.py
│   │   └── mic_stream.py    # Microphone audio stream capture using sounddevice
│   ├── wake_word/
│   │   ├── __init__.py
│   │   └── detector.py      # Offline "Lovix" wake-word detection & phonetic matcher
│   ├── speech/
│   │   ├── __init__.py
│   │   ├── recognizer.py    # Offline Vosk speech-to-text recognition
│   │   └── tts.py           # Offline pyttsx3 text-to-speech engine (Windows SAPI5)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── router.py        # Safe intent router with strict allowlist
│   │   ├── handlers.py      # Approved Windows actions (time, apps, volume, battery)
│   │   └── confirmation.py  # Confirmation safety lock for destructive actions
│   └── core/
│       ├── __init__.py
│       └── assistant.py     # Main state machine (Idle -> Wake -> Listen -> Act -> Respond)
├── main.py                  # Main program entry point
├── requirements.txt         # List of free open-source Python dependencies
└── README.md                # This beginner-friendly documentation
```

---

## 🛡️ Safe Command Allowlist (Phase 1)

LOVIX comes out of the box with safe, predetermined commands. It **never** runs raw text inside Windows PowerShell or CMD.

| Category | Spoken Command Example | Action Performed |
|---|---|---|
| **Greetings** | *"Hello"*, *"Introduce yourself"* | Speaks a friendly introduction |
| **Time & Date** | *"What time is it?"*, *"What is today's date?"* | Speaks the current local time / date |
| **System Info** | *"Battery status"*, *"System status"* | Reports battery percentage and RAM availability |
| **App Launcher** | *"Open Notepad"*, *"Open Calculator"*, *"Open File Explorer"* | Launches the specified approved Windows application |
| **Media & Volume** | *"Mute volume"*, *"Unmute volume"*, *"Volume up"*, *"Volume down"* | Adjusts master system audio safely |
| **Assistant Control**| *"Stop listening"*, *"Sleep"*, *"Exit Lovix"* | Puts assistant into standby or exits cleanly |
| **Critical Actions** | *"Shut down computer"*, *"Restart computer"* | **Asks for verbal confirmation first!** Only executes if you explicitly confirm "Yes". |

---

## 🚦 Implementation Plan (Phased Roadmap)

1. **Stage 1: Scaffold & Architecture** *(Current Step)*
   - Inspect environment and Python installation.
   - Design modular architecture and project structure.
   - Create documentation and code blueprints.

2. **Stage 2: Environment Setup & Offline Model Acquisition** *(Awaiting your approval)*
   - Create an isolated Python virtual environment (`.venv`).
   - Install required packages from `requirements.txt` (`vosk`, `sounddevice`, `numpy`, `pyttsx3`).
   - Download the free, lightweight Vosk English offline model (~40 MB) into the `models/` directory.

3. **Stage 3: Subsystem Testing (One by One)**
   - Test offline Text-to-Speech (verify your speakers).
   - Test microphone stream capture (verify audio input level).
   - Test offline "Lovix" wake-word detection.
   - Test offline command recognition and safe command router.

4. **Stage 4: Core State Machine Integration**
   - Connect all modules in `src/core/assistant.py`.
   - Implement the visual console feedback and beginner-friendly keyboard controls (e.g., press `Ctrl+C` or say *"Exit Lovix"* to stop).

5. **Stage 5: Verification & End-to-End Testing**
   - Run live end-to-end testing with spoken commands.
   - Verify safety confirmation routines.

---

## 🛑 How to Stop LOVIX

When LOVIX is running in your terminal:
- Press `Ctrl + C` on your keyboard at any time for an immediate, graceful shutdown.
- Or simply speak: *"Lovix, exit"* to close the program cleanly.
