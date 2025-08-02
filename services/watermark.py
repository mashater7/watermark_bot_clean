import os
import uuid
import subprocess
import pathlib

def apply_watermark(input_path, output_path, watermark_path, variant=1, scale_ratio=0.1):
    positions = {
        1: "10:10",
        2: "main_w-overlay_w-10:10",
        3: "10:main_h-overlay_h-10",
        4: "main_w-overlay_w-10:main_h-overlay_h-10"
    }

    position = positions.get(variant, "10:10")

    input_path = str(pathlib.Path(input_path).as_posix())
    output_path = str(pathlib.Path(output_path).as_posix())
    watermark_path = str(pathlib.Path(watermark_path).as_posix())

    scale_expr = f"iw*{scale_ratio}:-1"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", watermark_path,
        "-filter_complex", f"[1:v]scale={scale_expr}[wm];[0:v][wm]overlay={position}",
        "-frames:v", "1",
        "-update", "1",  # 💡 это важно!
        output_path
   ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print("[FFMPEG PREVIEW STDERR]:", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"FFMPEG preview failed: {result.stderr}")


def apply_video_watermark(input_path, output_path, watermark_path, variant=1, scale_ratio=0.1):
    positions = {
        1: "10:10",
        2: "main_w-overlay_w-10:10",
        3: "10:main_h-overlay_h-10",
        4: "main_w-overlay_w-10:main_h-overlay_h-10"
    }

    position = positions.get(variant, "10:10")
    scale_expr = f"iw*{scale_ratio}:-1"

    input_path = str(pathlib.Path(input_path).as_posix())
    output_path = str(pathlib.Path(output_path).as_posix())
    watermark_path = str(pathlib.Path(watermark_path).as_posix())

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", watermark_path,
        "-filter_complex", f"[1:v]scale={scale_expr}[wm];[0:v][wm]overlay={position}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "copy",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print("[FFMPEG VIDEO STDERR]:", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"FFMPEG video processing failed: {result.stderr}")


def generate_preview_variants(input_path, watermark_path, out_dir="previews"):
    os.makedirs(out_dir, exist_ok=True)
    paths = []

    for variant in range(1, 5):
        out_path = os.path.join(out_dir, f"{uuid.uuid4().hex}_v{variant}.jpg")
        apply_watermark(input_path, out_path, watermark_path, variant)
        paths.append(out_path)

    return paths
