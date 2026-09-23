"""Voice Engine: Handles Speech-to-Text (STT) and Text-to-Speech (TTS) for macOS, Windows, Linux, and Android."""
import os
import platform
import shutil
import subprocess
import sys

try:
    from src.platform_util.desktop import is_termux
except ImportError:
    from desktop_helper import is_termux


class VoiceEngine:
    """Voice assistant engine supporting native macOS (say), Windows (PowerShell/SAPI), pyttsx3, and Termux API."""

    def __init__(self):
        self.system = platform.system()
        self.is_termux = is_termux() and (shutil.which("termux-tts-speak") is not None)
        self.has_say = shutil.which("say") is not None  # macOS built-in TTS
        self.is_windows = self.system == "Windows"
        self.has_espeak = shutil.which("espeak") is not None

        # Check for pyttsx3 cross-platform offline TTS
        self.pyttsx3_engine = None
        try:
            import pyttsx3
            self.pyttsx3_engine = pyttsx3.init()
            self.pyttsx3_engine.setProperty('rate', 175)
        except Exception:
            pass

        # Check for speech_recognition module and microphone
        self.recognizer = None
        self.microphone = None
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
        except Exception:
            pass

    def _speak_windows_native(self, text: str):
        """
        Speaks text on Windows using built-in PowerShell System.Speech.
        Hardened: Text is passed as a positional argument ($args[0]) rather than string-interpolated.
        """
        ps_cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$synth.Rate = 1; "
            "$synth.Speak($args[0]);"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd, text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception as e:
            print(f"[Windows TTS Notice]: {e}")

    def speak(self, text: str):
        """Speaks out the given text using the best available platform TTS engine."""
        print(f"\n[Bot Says]: {text}\n")

        # 1. Android Termux TTS
        if self.is_termux:
            try:
                subprocess.run(["termux-tts-speak", text], check=True)
                return
            except Exception as e:
                print(f"[TTS Error in Termux]: {e}")

        # 2. macOS native 'say' command (highest fidelity on Mac, zero dependencies)
        if self.has_say:
            try:
                subprocess.run(["say", text], check=True)
                return
            except Exception as e:
                print(f"[TTS Error in macOS]: {e}")

        # 3. Windows pyttsx3 (fast offline SAPI5)
        if self.is_windows and self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
                return
            except Exception:
                pass

        # 4. Windows native PowerShell SpeechSynthesizer (built into Windows 10/11)
        if self.is_windows:
            self._speak_windows_native(text)
            return

        # 5. Linux / Other pyttsx3 engine
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
                return
            except Exception as e:
                print(f"[TTS Error in pyttsx3]: {e}")

        # 6. Linux espeak fallback
        if self.has_espeak:
            try:
                subprocess.run(["espeak", text], check=True)
                return
            except Exception as e:
                print(f"[TTS Error in espeak]: {e}")

    def listen(self, prompt: str = "Listening...") -> str:
        """
        Listens to user voice input via microphone or Termux STT.
        Falls back seamlessly to keyboard input on desktop if microphone is not available.
        """
        print(f"[Voice] {prompt}")

        # 1. Android Termux Speech-to-Text
        if is_termux() and shutil.which("termux-speech-to-text"):
            try:
                result = subprocess.run(
                    ["termux-speech-to-text"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                text = result.stdout.strip().lower()
                if text:
                    print(f"[User Said (Android)]: {text}")
                    return text
            except Exception:
                pass

        # 2. Python SpeechRecognition (Microphone on Desktop Mac / Windows)
        if self.recognizer and self.microphone:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                    audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio).strip().lower()
                print(f"[User Said (Mic)]: {text}")
                return text
            except Exception:
                pass

        # 3. Interactive keyboard input fallback
        try:
            text = input("[You] > ").strip().lower()
            return text
        except (EOFError, KeyboardInterrupt):
            return "exit"


if __name__ == "__main__":
    voice = VoiceEngine()
    voice.speak("Testing voice engine. Hello Boss!")
    heard = voice.listen("Say something or type your reply:")
    voice.speak(f"You said: {heard}")
