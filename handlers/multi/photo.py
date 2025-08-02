# handlers/multi/photo.py

import os
import uuid
from telebot import types
from services.storage import save_file
from services.watermark import apply_watermark, generate_preview_variants
from utils.watermark_ui import ask_watermark_size, SCALE_MAP


def handle_multi_photo(bot, message, state):
    chat_id = message.chat.id
    step = state.get("step")

    # 1. Загрузка фото
    if step == "multi_photo" and (message.photo or message.document):
        path = save_file(bot, message, "media/input")
        state.setdefault("media_files", []).append(path)
        bot.send_message(chat_id, f"📸 Фото добавлено. Всего: {len(state['media_files'])}")
        send_upload_buttons(bot, chat_id)

    # 2. Завершили загрузку
    elif step == "multi_photo" and message.text == "✅ Готово":
        if not state.get("media_files"):
            bot.send_message(chat_id, "⚠️ Сначала добавьте хотя бы одно фото.")
            return

        state["photo_groups"] = group_photos_by_ratio(state["media_files"])
        state["current_group_index"] = 0
        state["step"] = "multi_photo_watermark"
        bot.send_message(chat_id, "🖼 Теперь отправь водяной знак (PNG/фото).")

    # 3. Загрузка вотермарка
    elif step == "multi_photo_watermark" and (message.photo or message.document):
        state["watermark_path"] = save_file(bot, message, "media/input")
        state["step"] = "multi_photo_choose_position"
        show_preview_for_next_group(bot, chat_id, state)

    # 4. Выбор позиции
    elif step == "multi_photo_choose_position":
        try:
            variant = int(message.text.split()[-1])
        except Exception:
            bot.send_message(chat_id, "❌ Некорректный вариант. Выбери один из вариантов.")
            return

        state["last_position_variant"] = variant
        ask_watermark_size(bot, chat_id, state, next_step_key="multi_photo_apply")

    # 5. Выбор размера и применение
    elif step == "multi_photo_apply" and message.text in SCALE_MAP:
        scale_ratio = SCALE_MAP[message.text]
        variant = state["last_position_variant"]

        group_idx = state["current_group_index"]
        photo_groups = state["photo_groups"]
        current_group = photo_groups[group_idx]

        bot.send_message(chat_id, f"🔧 Обрабатываю группу {group_idx+1}/{len(photo_groups)}...")

        for path in current_group:
            filename = os.path.basename(path)
            out = f"media/output/{uuid.uuid4()}_v{variant}_{filename}"
            apply_watermark(path, out, state["watermark_path"], variant, scale_ratio)
            with open(out, "rb") as f:
                bot.send_document(chat_id, f , timeout=60)

        if group_idx + 1 < len(photo_groups):
            state["current_group_index"] += 1
            state["step"] = "multi_photo_choose_position"
            show_preview_for_next_group(bot, chat_id, state)
        else:
            bot.send_message(chat_id, "✅ Все фото обработаны!")
            state.clear()
            bot.send_message(chat_id, "↩ Нажмите /start для новой обработки.")


def send_upload_buttons(bot, chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add("➕ Ещё загрузить", "✅ Готово")
    bot.send_message(chat_id, "📷 Еще изображения?", reply_markup=markup)


def show_preview_for_next_group(bot, chat_id, state):
    group_idx = state["current_group_index"]
    photo_groups = state["photo_groups"]
    current_group = photo_groups[group_idx]
    first = current_group[0]
    previews = generate_preview_variants(first, state["watermark_path"])

    media = [
        types.InputMediaPhoto(open(p, "rb"), caption=f"Вариант {i+1}" if i == 0 else None)
        for i, p in enumerate(previews)
    ]
    bot.send_media_group(chat_id, media, timeout=60)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4")
    bot.send_message(chat_id, "Чтобы применить, выбери вариант:", reply_markup=markup)


def group_photos_by_ratio(file_paths):
    from PIL import Image
    from collections import defaultdict

    groups = defaultdict(list)
    for path in file_paths:
        try:
            with Image.open(path) as img:
                w, h = img.size
                ratio = round(w / h, 2)
                groups[ratio].append(path)
        except:
            continue

    return list(groups.values())
