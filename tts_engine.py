import subprocess
import wave
from pathlib import Path

from piper import PiperVoice
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
MODEL_PATH = Path(__file__).parent / "models" / "en_US-lessac-medium.onnx"

_voice = PiperVoice.load(str(MODEL_PATH))

def text_to_mp3(text: str, output_path: str) -> None:
    wav_path = Path(output_path).with_suffix(".wav")

    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(_voice.config.sample_rate)

        for chunk in _voice.synthesize(text):
            wav_file.writeframes(chunk.audio_int16_bytes)

    subprocess.run(
        [FFMPEG_EXE, "-y", "-i", str(wav_path), str(output_path)],
        check=True,
        capture_output=True
    )

    wav_path.unlink()

if __name__ == "__main__":
    text_to_mp3(
        "this is a test of the text to speech engine",
        "test_output.mp3"
    )
    print("Done, check test_output.mp3")

