# handlers/multi/video.py
import os
import uuid
from telebot import types
from services.storage import save_file
from services.watermark import apply_video_watermark, generate_preview_variants
from utils.watermark_ui import ask_watermark_size, SCALE_MAP  # 👈 обязательно

def handle_multi_video(bot, message, state):
    chat_id = message.chat.id
    step = state.get("step")

    if step == "multi_video" and message.video:
        path = save_file(bot, message, "media/input")
        state.setdefault("media_files", []).append(path)
        bot.send_message(chat_id, f"🎞 Видео добавлено. Всего: {len(state['media_files'])}")
        send_upload_buttons(bot, chat_id)

    elif step == "multi_video" and message.text == "✅ Готово":
        if not state.get("media_files"):
            bot.send_message(chat_id, "⚠️ Сначала добавьте хотя бы одно видео.")
            return
        state["step"] = "multi_video_watermark"
        bot.send_message(chat_id, "🖼 Теперь отправь водяной знак (PNG/фото).")

    elif step == "multi_video_watermark" and (message.photo or message.document):
        watermark_path = save_file(bot, message, "media/input")
        state["watermark_path"] = watermark_path
        state["step"] = "multi_video_choose_position"

        preview_path = state["media_files"][0]
        previews = generate_preview_variants(preview_path, watermark_path)

        media = [
            types.InputMediaPhoto(open(p, "rb"), caption=f"Вариант {i+1}" if i == 0 else None)
            for i, p in enumerate(previews)
        ]
        bot.send_media_group(chat_id, media , timeout=60)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4")
        bot.send_message(chat_id, "Выбери позицию водяного знака:", reply_markup=markup)

    elif step == "multi_video_choose_position" and message.text.startswith("Вариант "):
        try:
            variant = int(message.text.split()[-1])
        except:
            bot.send_message(chat_id, "❌ Некорректный формат варианта.")
            return

        state["last_position_variant"] = variant
        ask_watermark_size(bot, chat_id, state, next_step_key="multi_video_apply")

    elif step == "multi_video_apply" and message.text in SCALE_MAP:
        scale_ratio = SCALE_MAP[message.text]
        variant = state.get("position_variant", 1)

        bot.send_message(chat_id, f"⏳ Обрабатываю {len(state['media_files'])} видео...")

        results = []
        for in_path in state["media_files"]:
            filename = os.path.basename(in_path)
            out_path = f"media/output/{uuid.uuid4()}_v{variant}_{filename}"
            try:
                apply_video_watermark(in_path, out_path, state["watermark_path"], variant, scale_ratio)
                results.append(out_path)
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ Ошибка при обработке {filename}: {e}")

        for path in results:
            with open(path, "rb") as f:
                bot.send_document(chat_id, f , timeout=60)

        bot.send_message(chat_id, "✅ Все видео обработаны!")
        state.clear()
        bot.send_message(chat_id, "↩ Нажмите /start для новой обработки.")

def send_upload_buttons(bot, chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add("➕ Ещё загрузить", "✅ Готово")
    bot.send_message(chat_id, "🎞 Ещё видео?", reply_markup=markup)
