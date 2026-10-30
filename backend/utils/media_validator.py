import io
import os
import tempfile
from typing import Tuple, Dict, Any, Optional
from PIL import Image
import cv2
from fastapi import HTTPException, status
from backend.config import settings

def validate_image_upload(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Tuple[Image.Image, Dict[str, Any]]:
    """Validates image payload size, extension, MIME, resolution, and binary integrity."""
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty."
        )

    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds maximum allowed size of {max_mb}MB."
        )

    ext = os.path.splitext(filename.lower())[1]
    ct = (content_type or "").lower()
    allowed_exts = [".jpg", ".jpeg", ".png", ".webp"]

    if ct not in settings.ALLOWED_IMAGE_TYPES and ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format '{ct or ext}'. Allowed formats: JPEG, PNG, WebP."
        )

    try:
        raw_stream = io.BytesIO(file_bytes)
        img = Image.open(raw_stream)
        img.verify()
        
        # Re-open after verify
        img = Image.open(io.BytesIO(file_bytes))
        img = img.convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Corrupt or unreadable image: {str(e)}"
        )

    width, height = img.size
    if width < 32 or height < 32:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image dimensions too small. Minimum resolution is 32x32 pixels."
        )

    metadata = {
        "filename": filename,
        "content_type": ct or f"image/{ext.lstrip('.')}",
        "size_bytes": len(file_bytes),
        "dimensions": f"{width}x{height} px",
        "width": width,
        "height": height
    }

    return img, metadata


def validate_video_upload(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Validates video payload size, container format, and runtime duration via OpenCV."""
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded video file is empty."
        )

    if len(file_bytes) > settings.MAX_VIDEO_SIZE_BYTES:
        max_mb = settings.MAX_VIDEO_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video exceeds maximum allowed size of {max_mb}MB."
        )

    ext = os.path.splitext(filename.lower())[1]
    ct = (content_type or "").lower()
    allowed_exts = [".mp4", ".webm", ".mov", ".mkv"]

    if ct not in settings.ALLOWED_VIDEO_TYPES and ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{ct or ext}'. Allowed formats: MP4, WebM, MOV."
        )

    # Write safely to a temporary file on disk for OpenCV capture
    tmp = tempfile.NamedTemporaryFile(suffix=ext or ".mp4", delete=False)
    try:
        tmp.write(file_bytes)
        tmp.flush()
        tmp_path = tmp.name
    finally:
        tmp.close()

    cap = cv2.VideoCapture(tmp_path)
    if not cap.isOpened():
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not open video file. Video stream may be corrupt or missing a compatible codec."
        )

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    duration = round(total_frames / fps, 2) if fps > 0 else 0.0

    if duration > settings.MAX_VIDEO_DURATION_SECONDS:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video duration ({duration}s) exceeds the maximum limit of {settings.MAX_VIDEO_DURATION_SECONDS}s."
        )

    metadata = {
        "filename": filename,
        "content_type": ct or f"video/{ext.lstrip('.')}",
        "size_bytes": len(file_bytes),
        "duration_seconds": duration,
        "fps": round(fps, 1),
        "total_frames": total_frames,
        "dimensions": f"{width}x{height} px",
        "width": width,
        "height": height
    }

    return tmp_path, metadata
