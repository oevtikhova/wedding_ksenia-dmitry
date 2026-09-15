import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ) ---
BOT_TOKEN = '8627939314:AAFV0_NMZpL6jm9RTh8ZiWu9TpalwetSpOw'
GROUP_CHAT_ID = -1004353135218

# Список заданий для квеста
TASKS = [
    "Сделайте селфи с гостем, которого видите впервые 😄",
    "Найдите в автобусе человека в самых ярких носках и сфотографируйте его 🧦",
    "Напишите четверостишие, используя слова: любовь, автобус, кольца, тёща ✍️",
    "Соберите комплимент от 3 гостей и отправьте его голосовым сообщением 🎤",
    "Сфотографируйтесь всей командой в одной забавной позе 📸",
    "Возьмите мудрый совет для молодых у самого старшего гостя 👴",
    "Изобразите молодожёнов на фото так, чтобы было смешно 😂",
    "Отправьте видеокружок с пожеланием для молодой пары 🎉",
]

current_task_index = 0

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def send_scheduled_task(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет следующее задание из списка в группу."""
    global current_task_index
    if current_task_index < len(TASKS):
        task_text = TASKS[current_task_index]
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"🎉 <b>Новое задание!</b>\n\n{task_text}\n\n📸 Присылайте результат в этот чат!",
            parse_mode='HTML'
        )
        print(f"Задание №{current_task_index + 1} отправлено.")
        current_task_index += 1
    else:
        print("Все задания выполнены!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот для свадебного квеста. Добавь меня в группу, и я буду присылать задания! 🥳"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.message.from_user.first_name
    await update.message.reply_text(
        f"🔥 {user_name}, огонь! Задание в копилке!",
        reply_to_message_id=update.message.message_id
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text and not text.startswith('/'):
        user_name = update.message.from_user.first_name
        await update.message.reply_text(
            f"💬 {user_name}, отличный ответ!",
            reply_to_message_id=update.message.message_id
        )

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Планировщик: каждые 15 минут (900 сек), первое задание — через 10 секунд
    job_queue = application.job_queue
    job_queue.run_repeating(send_scheduled_task, interval=900, first=10)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен и работает...")
    application.run_polling()

if __name__ == '__main__':
    main()
