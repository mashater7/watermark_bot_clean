import os
import uuid
from telebot import types
from services.storage import save_file
from services.watermark import apply_watermark, generate_preview_variants
from utils.watermark_ui import ask_watermark_size, SCALE_MAP  # ✅ добавим поддержку размеров

def handle_single_photo(bot, message, state):
    chat_id = message.chat.id
    step = state.get("step")

    if step == "single_photo" and (message.photo or message.document):
        file_path = save_file(bot, message, "media")
        state["photo_path"] = file_path
        state["step"] = "waiting_watermark"
        bot.send_message(chat_id, "Теперь отправь водяной знак (фото или документ).")

    elif step == "waiting_watermark" and (message.photo or message.document):
        watermark_path = save_file(bot, message, "media")
        state["watermark_path"] = watermark_path
        state["step"] = "choosing_position"

        previews = generate_preview_variants(state["photo_path"], watermark_path)
        media = [types.InputMediaPhoto(open(p, "rb"), caption=f"Вариант {i+1}" if i == 0 else None) for i, p in enumerate(previews)]
        bot.send_media_group(chat_id, media)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4")
        bot.send_message(chat_id, "Выбери, где разместить водяной знак:", reply_markup=markup)

    elif step == "choosing_position":
        try:
            variant = int(message.text.split()[-1])
        except ValueError:
            bot.send_message(chat_id, "Некорректный формат. Попробуйте ещё раз.")
            return

        state["last_position_variant"] = variant
        ask_watermark_size(bot, chat_id, state, next_step_key="apply_single_photo")

    elif step == "apply_single_photo" and message.text in SCALE_MAP:
        scale_ratio = SCALE_MAP[message.text]
        variant = state["position_variant"]

        photo_path = state["photo_path"]
        watermark_path = state["watermark_path"]
        output_path = photo_path.replace(".jpg", f"_wm_v{variant}.jpg")

        apply_watermark(photo_path, output_path, watermark_path, variant, scale_ratio)

        with open(output_path, "rb") as out:
            bot.send_document(chat_id, out , timeout=60)

        state.clear()
        with open(output_path, "rb") as out:
            bot.send_message(chat_id, "✅ Готово. Нажмите /start для новой обработки.")
