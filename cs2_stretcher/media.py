"""FFmpeg and FFprobe integration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

class MediaError(RuntimeError):
    """A media tool could not inspect or convert the selected video."""


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration: float


def find_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        executable = f"{name}.exe" if os.name == "nt" and not name.lower().endswith(".exe") else name
        configured_dir = os.environ.get("FFMPEG_DIR")
        search_dirs = [Path(configured_dir)] if configured_dir else []
        if os.name == "nt":
            search_dirs.extend((Path(r"C:\ffmpeg\bin"), Path(r"C:\Program Files\ffmpeg\bin"),
                                Path(r"C:\Program Files (x86)\ffmpeg\bin")))
            for variable, suffix in (
                ("LOCALAPPDATA", Path("Programs") / "ffmpeg" / "bin"),
                ("LOCALAPPDATA", Path("Microsoft") / "WinGet" / "Links"),
                ("USERPROFILE", Path("scoop") / "apps" / "ffmpeg" / "current" / "bin"),
                ("ChocolateyInstall", Path("bin")),
            ):
                root = os.environ.get(variable)
                if root:
                    search_dirs.append(Path(root) / suffix)
            if os.environ.get("ChocolateyInstall") is None:
                search_dirs.append(Path(r"C:\ProgramData\chocolatey\bin"))
        path = next((str(candidate) for folder in search_dirs
                     if (candidate := folder / executable).is_file()), None)
    if not path:
        raise MediaError(
            f'Não localizei "{name}". Se o FFmpeg já estiver instalado, adicione ao PATH do Windows '
            "a pasta que contém ffmpeg.exe e ffprobe.exe e abra o aplicativo novamente."
        )
    return path


def probe_video(path: str | Path) -> VideoInfo:
    command = [find_tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "json", str(path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        duration = float(data.get("format", {}).get("duration", 0))
        if int(stream["width"]) <= 0 or int(stream["height"]) <= 0:
            raise ValueError("invalid dimensions")
        return VideoInfo(int(stream["width"]), int(stream["height"]), duration)
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise MediaError(f"Não foi possível ler as propriedades do vídeo: {detail.strip()}") from exc


def convert_video(
    source: str | Path,
    destination: str | Path,
    width: int,
    height: int,
    crf: int,
    duration: float,
    on_progress: Callable[[float], None] | None = None,
) -> None:
    if width < 2 or height < 2 or width % 2 or height % 2:
        raise MediaError("A largura e a altura de saída precisam ser números pares maiores que zero.")
    if not 0 <= crf <= 51:
        raise MediaError("O CRF precisa estar entre 0 e 51.")
    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_file():
        raise MediaError(f"O vídeo de origem não existe: {source_path}")
    command = [
        find_tool("ffmpeg"), "-y", "-nostdin", "-v", "error", "-i", str(source_path),
        "-vf", f"scale={width}:{height},setsar=1",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-c:a", "copy", "-progress", "pipe:1", "-nostats", str(destination_path),
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding="utf-8", errors="replace",
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert process.stdout is not None
        for line in process.stdout:
            if line.startswith("out_time_us=") and duration > 0 and on_progress:
                try:
                    fraction = int(line.partition("=")[2]) / (duration * 1_000_000)
                    on_progress(min(1.0, max(0.0, fraction)))
                except ValueError:
                    continue
        stderr = process.stderr.read() if process.stderr else ""
        return_code = process.wait()
        if return_code:
            raise MediaError(f"A conversão pelo FFmpeg falhou: {stderr[-2000:].strip()}")
        if on_progress:
            on_progress(1.0)
    except (OSError, MediaError) as exc:
        try:
            destination_path.unlink(missing_ok=True)
        except OSError:
            pass
        if isinstance(exc, MediaError):
            raise
        raise MediaError(f"Não foi possível iniciar o FFmpeg: {exc}") from exc
