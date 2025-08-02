from telebot import types
from handlers.single.photo import handle_single_photo
from handlers.single.video import handle_single_video
from handlers.multi.photo import handle_multi_photo
from handlers.multi.video import handle_multi_video
from handlers.multi.document import handle_multi_document
from utils.watermark_ui import SCALE_MAP

user_state = {}

def handle_start(bot, message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🖼 Один файл", "📁 Несколько файлов")
    bot.send_message(chat_id, "Привет! Что будем делать?", reply_markup=markup)

    user_state[chat_id] = {
        "step": "choose_mode",
        "mode": None,
        "media_files": [],
        "file_type": None,
        "watermark_path": None
    }

def handle_text_router(bot, message):
    chat_id = message.chat.id
    text = message.text
    state = user_state.get(chat_id, {})

    if chat_id not in user_state:
        user_state[chat_id] = {
            "step": None,
            "mode": None,
            "file_type": None,
            "media_files": [],
            "watermark_path": None
        }

    state = user_state[chat_id]

    if text == "🖼 Один файл":
        state["mode"] = "single"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("📷 Фото", "🎥 Видео")
        bot.send_message(chat_id, "Что за файл будет?", reply_markup=markup)
        state["step"] = "choose_single_type"

    elif text == "📁 Несколько файлов":
        state["mode"] = "multi"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("📷 Фото", "🎥 Видео", "📄 Документ")
        bot.send_message(chat_id, "Какой тип файлов?", reply_markup=markup)
        state["step"] = "choose_multi_type"

    elif state.get("step") == "choose_single_type":
        if text == "📷 Фото":
            state["file_type"] = "photo"
            state["step"] = "single_photo"
            bot.send_message(chat_id, "Отправь фото")
        elif text == "🎥 Видео":
            state["file_type"] = "video"
            state["step"] = "single_video"
            bot.send_message(chat_id, "Отправь видео")

    elif state.get("step") == "choose_multi_type":
        if text == "📷 Фото":
            state["file_type"] = "photo"
            state["step"] = "multi_photo"
            state["media_files"] = []
            bot.send_message(chat_id, "Отправляй фото")
        elif text == "🎥 Видео":
            state["file_type"] = "video"
            state["step"] = "multi_video"
            state["media_files"] = []
            bot.send_message(chat_id, "Отправляй видео")
        elif text == "📄 Документ":
            state["file_type"] = "document"
            state["step"] = "multi_document"
            state["media_files"] = []
            bot.send_message(chat_id, "Отправляй документы")

    # 👉 Обработка кнопки "✅ Готово" для мультифото
    elif state.get("step") == "multi_photo" and text == "✅ Готово":
        handle_multi_photo(bot, message, state)

    # 👉 Обработка кнопки выбора позиции (Вариант 1/2/3/4)
    elif text.startswith("Вариант "):
        if state["mode"] == "single" and state["file_type"] == "photo":
            handle_single_photo(bot, message, state)
        elif state["mode"] == "multi" and state["file_type"] == "photo":
            handle_multi_photo(bot, message, state)
        elif state["mode"] == "multi" and state["file_type"] == "video":
            handle_multi_video(bot, message, state)
        elif state["mode"] == "multi" and state["file_type"] == "document":
            handle_multi_document(bot, message, state)
        elif state["mode"] == "single" and state["file_type"] == "video":
            handle_single_video(bot, message, state)

    # 👉 Обработка выбора размера watermark (все apply_ шаги)
    elif state.get("step") == "apply_single_photo" and text in SCALE_MAP:
        handle_single_photo(bot, message, state)
    elif state.get("step") == "apply_single_video" and text in SCALE_MAP:
        handle_single_video(bot, message, state)
    elif state.get("step") == "multi_photo_apply" and text in SCALE_MAP:
        handle_multi_photo(bot, message, state)
    elif state.get("step") == "multi_video_apply" and text in SCALE_MAP:
        handle_multi_video(bot, message, state)

def handle_file_router(bot, message):
    chat_id = message.chat.id
    state = user_state.get(chat_id)

    if not state:
        bot.send_message(chat_id, "Сначала нажмите /start.")
        return

    step = state.get("step")
    mode = state.get("mode")
    file_type = state.get("file_type")

    # Обработка промежуточных шагов мультифото/видео
    if step and step.startswith("multi_photo"):
        handle_multi_photo(bot, message, state)
        return

    if step and step.startswith("multi_video"):
        handle_multi_video(bot, message, state)
        return

    # Обычные маршруты
    if mode == "single" and file_type == "photo":
        handle_single_photo(bot, message, state)
    elif mode == "single" and file_type == "video":
        handle_single_video(bot, message, state)
    elif mode == "multi" and file_type == "photo":
        handle_multi_photo(bot, message, state)
    elif mode == "multi" and file_type == "document":
        handle_multi_document(bot, message, state)
