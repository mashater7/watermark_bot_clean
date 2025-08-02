import telebot
from config import TOKEN
from handlers.common import handle_start, handle_text_router, handle_file_router

bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    handle_start(bot, message)

# Все текстовые сообщения
@bot.message_handler(content_types=['text'])
def text_router(message):
    handle_text_router(bot, message)

# Обработка всех файлов (фото, видео, документ)
@bot.message_handler(content_types=['photo', 'video', 'document'])
def file_router(message):
    handle_file_router(bot, message)

if __name__ == "__main__":
    print("🤖 Бот запущен")
    bot.polling(none_stop=True)
# точка входа