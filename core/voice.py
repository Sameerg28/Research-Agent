import logging
import tempfile

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd

from interfaces.tool import ToolInterface

logger = logging.getLogger(__name__)


class VoiceInput:
    def __init__(self, transcriber: ToolInterface, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self._transcriber = transcriber

    def record_audio(self, duration=None, silence_threshold=0.01, silence_duration=2.0):
        logger.info("Recording...")
        if duration:
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
            )
            sd.wait()
        else:
            recording = []

            def callback(indata, frames, time, status):
                if status:
                    print(status)
                recording.append(indata.copy())

            with sd.InputStream(samplerate=self.sample_rate, channels=1, callback=callback):
                print("Recording... (Press Ctrl+C to stop if it does not auto-stop)")
                try:
                    import time

                    start_time = time.time()
                    while True:
                        time.sleep(0.1)
                        if duration and (time.time() - start_time) > duration:
                            break
                except KeyboardInterrupt:
                    pass
            recording = np.concatenate(recording, axis=0)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            wav.write(temp_audio.name, self.sample_rate, recording)
            return temp_audio.name

    def transcribe(self, audio_file_path: str) -> str:
        return str(self._transcriber.execute({"audio_file_path": audio_file_path})).strip()

    def get_input(self, prompt_text=""):
        if prompt_text:
            print(prompt_text)

        audio_path = self.record_audio(duration=5)
        return self.transcribe(audio_path)
