import os
import uuid

import os
import uuid

def save_file(bot, message, folder="media"):
    os.makedirs(folder, exist_ok=True)

    file_id = None
    ext = ".bin"
    size = 0

    if message.document:
        file_id = message.document.file_id
        ext = os.path.splitext(message.document.file_name)[1]
        size = message.document.file_size
    elif message.photo:
        file_id = message.photo[-1].file_id
        ext = ".jpg"
        size = 0  # фото обычно маленькие
    elif message.video:
        file_id = message.video.file_id
        ext = ".mp4"
        size = message.video.file_size
    else:
        raise ValueError("Unsupported file type")

    # ⛔️ ВАЖНО: если слишком большой — сразу отменяем
    if size and size > 49 * 1024 * 1024:
        raise ValueError("Файл слишком большой (максимум 50 МБ).")

    # Только теперь — получаем файл
    file_info = bot.get_file(file_id)
    downloaded = bot.download_file(file_info.file_path)

    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(folder, filename)

    with open(path, "wb") as f:
        f.write(downloaded)

    return path