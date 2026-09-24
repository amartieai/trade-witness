"""Screen recorder — thin ffmpeg wrapper (portable, no OBS required).

Captures the screen from session start to end. Records with a high-speed
encode preset so a full trading day stays on disk cheaply.
"""
import os
import shutil
import subprocess
import sys


def _input_args(capture: str, fps: int) -> list:
    """Return ffmpeg input args for the platform/capture mode."""
    os_name = sys.platform
    if os_name == "darwin":
        # avfoundation: screen device is "1" (or "1:none")
        return ["-f", "avfoundation", "-framerate", str(fps), "-i", "1:none"]
    if os_name in ("win32", "cygwin"):
        return ["-f", "gdigrab", "-framerate", str(fps), "-i", "desktop"]
    # linux x11
    if capture == "full":
        return ["-f", "x11grab", "-framerate", str(fps), "-i", os.environ.get("DISPLAY", ":0.0")]
    # capture == "region": "WxH+X,Y"
    return ["-f", "x11grab", "-framerate", str(fps),
            "-video_size", capture.split("+")[0],
            "-i", os.environ.get("DISPLAY", ":0.0") + "+" + capture.split("+", 1)[1]]


class Recorder:
    def __init__(self, capture: str = "full", fps: int = 5, codec: str = "libx264"):
        self.capture = capture
        self.fps = fps
        self.codec = codec
        self.proc = None
        self.out_path = None

    def start(self, out_path: str):
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not found — install it first (see install.sh)")
        self.out_path = out_path
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + _input_args(self.capture, self.fps) + [
            "-c:v", self.codec, "-preset", "ultrafast", "-pix_fmt", "yuv420p", out_path,
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self.proc

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self.proc = None

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None