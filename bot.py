import logging
import asyncio # python-telegram-bot v20+ использует asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ ---
# ВАЖНО: Вставьте сюда ваши реальные токены!
TELEGRAM_BOT_TOKEN = "7848520955:AAHsTbUT1wRugd2Z3TigBNWxz9XTkWG9hEs"

GEMINI_API_KEY = "AIzaSyBCkO83F3TZqNIJcvsxPkpNnQYMR4Ua8lg"

# Проверка, что токены были заменены (простая)
if "ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН" in TELEGRAM_BOT_TOKEN or "ВАШ_GOOGLE_GEMINI_API_КЛЮЧ" in GEMINI_API_KEY:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("!!! ПОЖАЛУЙСТА, ЗАМЕНИТЕ ПЛЕЙСХОЛДЕРЫ ТОКЕНОВ В КОДЕ !!!")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    exit() # Выход, если токены не заменены

# Настройка логирования (чтобы видеть информацию о работе бота в консоли)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ИНИЦИАЛИЗАЦИЯ GEMINI ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Выбираем модель Gemini. 'gemini-1.5-flash-latest' - быстрая и доступная модель
    # Можно использовать 'gemini-pro' для более сложных задач
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    logger.info("Модель Google Gemini успешно инициализирована.")
except Exception as e:
    logger.error(f"Ошибка инициализации Google Gemini: {e}")
    gemini_model = None # Устанавливаем в None, чтобы бот не упал при старте

# --- ФУНКЦИИ-ОБРАБОТЧИКИ ТЕЛЕГРАМ ---

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я бот с интеграцией Google Gemini. Просто напиши мне что-нибудь.",
    )
    logger.info(f"Пользователь {user.username} ({user.id}) запустил бота командой /start.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовое сообщение пользователя и отвечает с помощью Gemini."""
    user_message = update.message.text
    user = update.effective_user
    chat_id = update.message.chat_id
    logger.info(f"Получено сообщение от {user.username} ({user.id}) в чате {chat_id}: '{user_message}'")

    if not gemini_model:
        await update.message.reply_text("Извините, произошла ошибка при инициализации модели Gemini. Попробуйте позже.")
        return

    # Отправляем сообщение пользователя в Gemini
    try:
        # Показываем пользователю, что мы обрабатываем запрос
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

        # Генерируем ответ с помощью Gemini
        response = await asyncio.to_thread(gemini_model.generate_content, user_message) # Запускаем синхронный вызов в отдельном потоке

        gemini_response = response.text
        logger.info(f"Ответ от Gemini: '{gemini_response[:100]}...'") # Логируем начало ответа

        # Отправляем ответ Gemini пользователю
        await update.message.reply_text(gemini_response)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от {user.username} ({user.id}): {e}")
        await update.message.reply_text("Произошла ошибка при обращении к Gemini. Попробуйте еще раз.")

# --- ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА БОТА ---
def main() -> None:
    """Запускает бота."""
    # Создаем объект Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    # Добавляем обработчик для всех текстовых сообщений, которые не являются командами
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запускается...")
    # Запускаем бота в режиме опроса (polling)
    application.run_polling()
    logger.info("Бот остановлен.")

# Точка входа в программу
if __name__ == '__main__':
    main()