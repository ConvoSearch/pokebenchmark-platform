from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np
import pytest

from pokebenchmark_platform.recording.recorder import VideoRecorder


def make_frame(width=240, height=160):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


def test_recorder_init():
    rec = VideoRecorder("out.mp4", width=320, height=240, fps=24)
    assert rec.output_path == "out.mp4"
    assert rec.width == 320
    assert rec.height == 240
    assert rec.fps == 24
    assert rec.frame_count == 0
    assert rec._process is None


def test_recorder_start_spawns_ffmpeg():
    rec = VideoRecorder("out.mp4")
    with patch("pokebenchmark_platform.recording.recorder.subprocess") as mock_sub:
        mock_proc = MagicMock()
        mock_sub.Popen.return_value = mock_proc
        mock_sub.PIPE = -1
        mock_sub.DEVNULL = -2

        rec.start()

        mock_sub.Popen.assert_called_once()
        call_args = mock_sub.Popen.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "240x160" in cmd
        assert "out.mp4" in cmd
        assert rec._process is mock_proc


def test_recorder_write_frame():
    rec = VideoRecorder("out.mp4")
    mock_proc = MagicMock()
    rec._process = mock_proc

    frame = make_frame()
    rec.write_frame(frame)

    mock_proc.stdin.write.assert_called_once()
    written = mock_proc.stdin.write.call_args[0][0]
    # 240 * 160 * 3 bytes for RGB
    assert len(written) == 240 * 160 * 3


def test_recorder_stop():
    rec = VideoRecorder("out.mp4")
    mock_proc = MagicMock()
    rec._process = mock_proc

    rec.stop()

    mock_proc.stdin.close.assert_called_once()
    mock_proc.wait.assert_called_once()
    assert rec._process is None


def test_recorder_frame_count():
    rec = VideoRecorder("out.mp4")
    mock_proc = MagicMock()
    rec._process = mock_proc

    for _ in range(5):
        rec.write_frame(make_frame())

    assert rec.frame_count == 5
