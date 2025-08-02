from telebot import types

# Карта названия кнопки -> коэффициент масштабирования
SCALE_MAP = {
    "Авто (1/10)": 0.1,
    "Маленький (1/20)": 0.05,
    "Средний (1/15)": 0.067,
    "Большой (1/5)": 0.2
}

def ask_watermark_size(bot, chat_id, state, next_step_key):
    """
    Показывает кнопки выбора размера watermark и сохраняет следующий шаг.
    """
    variant = int(state.get("last_position_variant", 1))
    state["position_variant"] = variant
    state["step"] = next_step_key

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(*SCALE_MAP.keys())
    bot.send_message(chat_id, "Теперь выбери размер водяного знака:", reply_markup=markup)
