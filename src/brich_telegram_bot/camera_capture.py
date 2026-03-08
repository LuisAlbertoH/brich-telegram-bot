from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class CameraCaptureError(RuntimeError):
    """Raised when the local webcam photo capture fails."""


@dataclass(slots=True)
class CapturedPhoto:
    path: Path
    width: int
    height: int


def capture_webcam_photo(
    device_index: int,
    warmup_frames: int,
    timeout_sec: int,
) -> CapturedPhoto:
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise CameraCaptureError(
            "Falta OpenCV. Instala dependencias con: pip install -r requirements.txt"
        ) from exc

    backend = cv2.CAP_DSHOW if os.name == "nt" and hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY
    capture = cv2.VideoCapture(device_index, backend)
    if not capture or not capture.isOpened():
        raise CameraCaptureError(
            f"No se pudo abrir la webcam local (indice {device_index}). "
            "Verifica permisos de camara y que no este siendo usada por otra app."
        )

    frame = None
    deadline = time.monotonic() + max(1, timeout_sec)
    try:
        for _ in range(max(1, warmup_frames)):
            ok, candidate = capture.read()
            if ok and candidate is not None:
                frame = candidate
            time.sleep(0.04)

        while frame is None and time.monotonic() < deadline:
            ok, candidate = capture.read()
            if ok and candidate is not None:
                frame = candidate
                break
            time.sleep(0.05)
    finally:
        capture.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    if frame is None:
        raise CameraCaptureError("No se pudo capturar un frame valido desde la webcam.")

    photo_dir = Path(tempfile.gettempdir()) / "brich-telegram-bot"
    photo_dir.mkdir(parents=True, exist_ok=True)
    filename = f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    photo_path = photo_dir / filename

    quality_args: list[int] = []
    if hasattr(cv2, "IMWRITE_JPEG_QUALITY"):
        quality_args = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
    saved = cv2.imwrite(str(photo_path), frame, quality_args)
    if not saved:
        raise CameraCaptureError("No se pudo guardar la imagen capturada.")

    height, width = frame.shape[:2]
    return CapturedPhoto(path=photo_path, width=width, height=height)
