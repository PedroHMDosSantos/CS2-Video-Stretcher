import json
import io
import subprocess

import pytest

from cs2_stretcher import media


def test_probe_video_reads_dimensions_and_duration(monkeypatch, tmp_path):
    monkeypatch.setattr(media, "find_tool", lambda name: name)
    payload = {"streams": [{"width": 1440, "height": 1080}], "format": {"duration": "42.5"}}
    monkeypatch.setattr(media.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, json.dumps(payload), ""))

    info = media.probe_video(tmp_path / "match.mp4")

    assert (info.width, info.height, info.duration) == (1440, 1080, 42.5)


@pytest.mark.parametrize("width,height,crf", [(0, 1080, 20), (1921, 1080, 20), (1920, 1080, 52)])
def test_convert_rejects_invalid_export_settings(monkeypatch, width, height, crf):
    monkeypatch.setattr(media, "find_tool", lambda name: name)

    with pytest.raises(media.MediaError):
        media.convert_video("in.mp4", "out.mp4", width, height, crf, 30)


def test_find_tool_reports_missing_dependency(monkeypatch):
    monkeypatch.setattr(media.shutil, "which", lambda name: None)
    monkeypatch.setattr(media.os, "name", "nt")
    monkeypatch.setattr(media.os, "environ", {})

    with pytest.raises(media.MediaError, match="Não localizei"):
        media.find_tool("ffmpeg")


def test_find_tool_checks_ffmpeg_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(media.shutil, "which", lambda name: None)
    monkeypatch.setattr(media.os, "name", "nt")
    executable = tmp_path / "ffmpeg.exe"
    executable.touch()
    monkeypatch.setattr(media.os, "environ", {"FFMPEG_DIR": str(tmp_path)})

    assert media.find_tool("ffmpeg") == str(executable)


def test_find_tool_checks_configured_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(media.shutil, "which", lambda name: None)
    monkeypatch.setattr(media.os, "name", "nt")
    executable = tmp_path / "ffprobe.exe"
    executable.touch()
    monkeypatch.setenv("FFMPEG_DIR", str(tmp_path))

    assert media.find_tool("ffprobe") == str(executable)


def test_convert_builds_stretch_command_and_reports_progress(monkeypatch, tmp_path):
    monkeypatch.setattr(media, "find_tool", lambda name: "ffmpeg.exe")

    class CompletedProcess:
        stdout = io.StringIO("out_time_us=5000000\nprogress=continue\n")
        stderr = io.StringIO("")

        def wait(self):
            return 0

    calls = []
    monkeypatch.setattr(media.subprocess, "Popen", lambda command, **kwargs: (calls.append(command) or CompletedProcess()))
    source = tmp_path / "input.mkv"
    source.touch()
    progress = []

    media.convert_video(source, tmp_path / "output.mp4", 1920, 1080, 20, 10, progress.append)

    assert "scale=1920:1080,setsar=1" in calls[0]
    assert "-c:a" in calls[0] and "copy" in calls[0]
    assert progress == [0.5, 1.0]


def test_convert_removes_partial_output_after_ffmpeg_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(media, "find_tool", lambda name: "ffmpeg.exe")
    output = tmp_path / "partial.mp4"

    class FailedProcess:
        stdout = io.StringIO("")
        stderr = io.StringIO("codec failure")

        def wait(self):
            return 1

    monkeypatch.setattr(media.subprocess, "Popen", lambda *args, **kwargs: (output.write_bytes(b"partial") and FailedProcess()))
    source = tmp_path / "input.mp4"
    source.touch()

    with pytest.raises(media.MediaError, match="codec failure"):
        media.convert_video(source, output, 1920, 1080, 20, 10)

    assert not output.exists()
