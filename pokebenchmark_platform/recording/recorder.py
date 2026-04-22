import subprocess
import numpy as np
from PIL import Image

class VideoRecorder:
    def __init__(self, output_path: str, width: int = 240, height: int = 160, fps: int = 30):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_count = 0
        self._process: subprocess.Popen | None = None

    def start(self):
        self._process = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
             "-s", f"{self.width}x{self.height}", "-pix_fmt", "rgb24",
             "-r", str(self.fps), "-i", "-", "-an", "-vcodec", "libx264",
             "-pix_fmt", "yuv420p", "-preset", "fast", self.output_path],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    def write_frame(self, frame: Image.Image):
        if self._process is None:
            raise RuntimeError("Recorder not started")
        if frame.size != (self.width, self.height):
            frame = frame.resize((self.width, self.height))
        raw = np.array(frame.convert("RGB")).tobytes()
        self._process.stdin.write(raw)
        self.frame_count += 1

    def stop(self):
        if self._process is not None:
            self._process.stdin.close()
            self._process.wait()
            self._process = None
