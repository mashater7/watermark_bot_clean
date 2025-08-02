import os
import uuid
import requests

from telebot import types
from services.storage import save_file
from services.watermark import apply_video_watermark, generate_preview_variants
from utils.watermark_ui import ask_watermark_size, SCALE_MAP  # 👈 импорт общей логики

def upload_to_transfersh(file_path):
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        res = requests.put(f"https://transfer.sh/{filename}", data=f)
    if res.ok:
        return res.text.strip()
    else:
        return None

def handle_single_video(bot, message, state):
    chat_id = message.chat.id
    step = state.get("step")

    if step == "single_video" and message.video:
        try:
            video_path = save_file(bot, message, "media/input")
        except ValueError as e:
            bot.send_message(chat_id, f"⚠️ {e}")
            return

        state["video_path"] = video_path
        state["step"] = "waiting_video_watermark"
        bot.send_message(chat_id, "📎 Теперь отправь водяной знак (фото или документ).")

    elif step == "waiting_video_watermark" and (message.photo or message.document):
        watermark_path = save_file(bot, message, "media/input")
        state["watermark_path"] = watermark_path
        state["step"] = "choosing_video_position"

        bot.send_message(chat_id, "🖼 Генерирую превью с водяным знаком…")
        preview_paths = generate_preview_variants(
            state["video_path"], watermark_path, out_dir="media/previews"
        )
        for i, path in enumerate(preview_paths, start=1):
            with open(path, "rb") as f:
                bot.send_photo(chat_id, f, caption=f"Вариант {i}")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4")
        bot.send_message(chat_id, "Выбери позицию водяного знака:", reply_markup=markup)

    elif step == "choosing_video_position":
        try:
            variant = int(message.text.split()[-1])
        except ValueError:
            bot.send_message(chat_id, "⚠️ Некорректный формат. Выбери, например: Вариант 2")
            return

        state["last_position_variant"] = variant
        ask_watermark_size(bot, chat_id, state, next_step_key="apply_single_video")

    elif step == "apply_single_video" and message.text in SCALE_MAP:
        scale_ratio = SCALE_MAP[message.text]
        variant = state["position_variant"]

        video_path = state["video_path"]
        watermark_path = state["watermark_path"]
        filename = os.path.basename(video_path)
        output_path = os.path.join("media/output", f"{uuid.uuid4()}_v{variant}_{filename}")

        apply_video_watermark(video_path, output_path, watermark_path, variant, scale_ratio)

        # 👉 Отправляем либо файл, либо ссылку (если слишком большой)
        if os.path.getsize(output_path) <= 49 * 1024 * 1024:
            with open(output_path, "rb") as f:
                bot.send_document(chat_id, f, timeout=60)
        else:
            url = upload_to_transfersh(output_path)
            if url:
                bot.send_message(chat_id, f"📁 Видео слишком большое, вот ссылка на скачивание:\n{url}")
            else:
                bot.send_message(chat_id, "❌ Не удалось загрузить видео на сервер.")

        bot.send_message(chat_id, "✅ Видео готово!")
        state.clear()
        bot.send_message(chat_id, "↩ Нажмите /start для новой обработки.")