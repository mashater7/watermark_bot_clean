# handlers/multi/document.py
import os
from telebot import types
from services.storage import save_file
from services.watermark import apply_watermark

def handle_multi_document(bot, message, state):
    chat_id = message.chat.id
    step = state.get("step")

    if step == "multi_document" and message.document:
        doc_path = save_file(bot, message, "media")
        if "media_files" not in state:
            state["media_files"] = []
        state["media_files"].append(doc_path)
        bot.send_message(chat_id, f"📄 Документ добавлен. Всего: {len(state['media_files'])}")

    elif step == "multi_document" and message.text == "✅ Готово":
        if not state.get("media_files"):
            bot.send_message(chat_id, "Сначала добавьте хотя бы один документ.")
            return

        state["step"] = "multi_document_watermark"
        bot.send_message(chat_id, "Теперь отправь водяной знак (фото или документ).")

    elif step == "multi_document_watermark" and (message.photo or message.document):
        watermark_path = save_file(bot, message, "media")
        state["watermark_path"] = watermark_path
        state["step"] = "multi_document_choose_position"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4")
        bot.send_message(chat_id, "Выбери позицию водяного знака:", reply_markup=markup)

    elif step == "multi_document_choose_position":
        try:
            variant = int(message.text.split()[-1])
        except:
            bot.send_message(chat_id, "Некорректный формат варианта.")
            return

        bot.send_message(chat_id, f"⏳ Обрабатываю {len(state['media_files'])} документов...")
        results = []
        for path in state["media_files"]:
            out = os.path.splitext(path)[0] + f"_wm_v{variant}.jpg"
            try:
                apply_watermark(path, out, state["watermark_path"], variant)
                results.append(out)
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ Ошибка при обработке: {e}")

        for out_path in results:
            with open(out_path, "rb") as f:
                bot.send_document(chat_id, f)

        bot.send_message(chat_id, "✅ Готово! Все документы обработаны.")
        state.clear()
        bot.send_message(chat_id, "Нажмите /start для новой обработки.")
# несколько — документы