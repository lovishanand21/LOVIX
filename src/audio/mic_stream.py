"""
LOVIX Audio Stream Manager
Safely captures continuous microphone input using sounddevice and puts raw PCM audio into a thread-safe Queue.
100% offline, volatile in-memory processing only. No audio saved to disk.
"""

import queue
import logging
from typing import Optional
import sounddevice as sd

logger = logging.getLogger("LOVIX.AudioStream")


class AudioStreamManager:
    """Manages continuous microphone input streaming via sounddevice."""

    def __init__(
        self,
        sample_rate: int = 16000,
        block_size: int = 4000,
        max_queue_size: int = 8,
    ):
        """
        Args:
            sample_rate: Audio sampling frequency in Hz (default: 16000).
            block_size: Number of audio frames per callback chunk (default: 4000).
            max_queue_size: Maximum chunks to buffer in memory to prevent unbounded memory growth (default: 8, ~2.0s buffer).
        """
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.max_queue_size = max_queue_size
        self.audio_queue: queue.Queue = queue.Queue(maxsize=self.max_queue_size)
        self._stream: Optional[sd.RawInputStream] = None
        self._is_running = False

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Internal callback invoked by sounddevice for each audio block.
        Runs on PortAudio background thread.
        Never blocks or crashes, drops oldest chunk if queue is full.
        """
        if status:
            logger.warning(f"Audio stream status flag: {status}")

        try:
            # Convert raw input buffer into immutable bytes
            chunk = bytes(indata)

            # Put into queue without blocking
            try:
                self.audio_queue.put_nowait(chunk)
            except queue.Full:
                # Discard oldest chunk to make room for newest audio and prevent latency/backlog
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    pass

                try:
                    self.audio_queue.put_nowait(chunk)
                except queue.Full:
                    pass
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")

    def start(self) -> bool:
        """
        Starts the microphone input stream using sounddevice.RawInputStream.
        Configures: 16000 Hz, mono (1 channel), int16 format.

        Returns:
            bool: True if started successfully, False otherwise.
        """
        if self._is_running and self._stream is not None:
            logger.info("Microphone input stream is already active.")
            return True

        logger.info(
            f"Starting microphone capture (rate={self.sample_rate}Hz, channels=1, dtype=int16, block={self.block_size})..."
        )
        try:
            self._stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=1,
                dtype="int16",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._is_running = True
            logger.info("Microphone stream started successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to start microphone stream: {e}", exc_info=True)
            if self._stream is not None:
                try:
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
            self._is_running = False
            return False

    def stop(self):
        """Stops and closes the microphone input stream cleanly."""
        if not self._is_running and self._stream is None:
            return

        logger.info("Stopping and closing microphone input stream.")
        try:
            if self._stream is not None:
                if self._stream.active:
                    self._stream.stop()
                self._stream.close()
        except Exception as e:
            logger.warning(f"Exception while stopping microphone stream: {e}")
        finally:
            self._stream = None
            self._is_running = False
            self.clear_queue()
            logger.info("Microphone stream stopped cleanly.")

    def get_audio_chunk(self, timeout: float = 0.5) -> Optional[bytes]:
        """
        Retrieves the next chunk of raw audio bytes from the queue.

        Args:
            timeout: Maximum seconds to wait for a chunk.

        Returns:
            bytes of PCM audio, or None if timeout expired.
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        """Empties any stale audio chunks from the buffer."""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    @property
    def is_running(self) -> bool:
        """Returns True if the microphone stream is actively running."""
        return self._is_running
