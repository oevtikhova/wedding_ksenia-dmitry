import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8627939314:AAFV0_NMZpL6jm9RTh8ZiWu9TpalwetSpOw")
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1004353135218"))

# Интервал между заданиями (в секундах). 900 = 15 минут
TASK_INTERVAL = 900


# --- ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ ---
INTRO = (
    "💍 <b>Дорогие гости!</b> 💍\n\n"
    "Сегодня у нас необычный день — мы запускаем <b>свадебный квест</b>! 🎉\n\n"
    "<b>Как это работает</b>\n"
    "• Каждые 15 минут сюда прилетает новое задание.\n"
    "• Выполняйте его и присылайте результат в этот чат — фото, видео, текст или голосовое.\n"
    "• Фантазируйте! Лучшие моменты попадут в общий свадебный альбом.\n\n"
    "🏆 <b>И это не просто игра — это соревнование!</b> 🏆\n\n"
    "<b>Каждый сам за себя!</b>\n"
    "Главный приз на банкете получит только один абсолютный победитель 👑 — "
    "тот, кто выполнит <b>все задания быстрее всех</b>.\n\n"
    "<b>Участвуют ВСЕ одновременно.</b>\n"
    "Если задание требует сфотографировать кого-то или что-то — "
    "каждый присылает <b>своё личное фото</b>. Старайтесь не повторяться: "
    "если один гость уже сфотографировался с кем-то, пусть второй участник "
    "найдёт для селфи кого-то другого. Так у нас получится больше живых, "
    "разных и неожиданных кадров! 😉\n\n"
    "<b>Скорость решает всё!</b> ⏱️🔥\n"
    "Ловите моменты, пишите ответы и отправляйте их без промедления. "
    "Если на финише несколько человек выполнят все задания — "
    "победу заберёт тот, чьи сообщения прилетели хотя бы <b>на секунду раньше</b> остальных!\n\n"
    "<b>Маленькое исключение — командные задания.</b>\n"
    "Если задание групповое (например, «сфотографируйтесь всей командой»), "
    "его может прислать <b>один человек за всех</b> — повторять всей группой не нужно. 📸\n\n"
    "<b>Готовы?</b> Первое задание уже летит! 🚀\n\n"
    "<i>С любовью, Дмитрий и Ксения 💕</i>"
)


# --- СПИСОК ЗАДАНИЙ ---
TASKS = [
    "Сделайте селфи с гостем, которого видите впервые 😄",
    "Найдите в автобусе человека в самых ярких носках и сфотографируйте его 🧦",
    "Напишите четверостишие, используя слова: любовь, автобус, кольца, тёща ✍️",
    "Соберите комплимент от 3 гостей и отправьте его голосовым сообщением 🎤",
    "Сфотографируйтесь всей командой в одной забавной позе 📸",
    "Возьмите мудрый совет для молодых у самого старшего гостя 👴",
    "Изобразите молодожёнов на фото так, чтобы было смешно 😂",
    "Отправьте видеокружок с пожеланием для молодой пары 🎉",
    "Помашите из окна случайному прохожему так, чтобы он помахал вам в ответ. Снимите этот триумф на видео! 👋",
    "Включите фантазию! Сделайте фото любого предмета в автобусе (бутылка, поручень, ремень безопасности) так, будто это свадебное кольцо 💍",
    "Сделайте фото в стиле «Серьёзная мафия». Никаких улыбок, суровые лица, бокалы в руках 😎",
    "Изучаем палитру сегодняшнего дня прямо на улицах города! 🏙️ Найдите за окном автобуса что-то голубое, коричневое, оливковое, сливочное или синее. Сделайте фото через стекло и подпишите, насколько этот объект вписывается в наш дресс-код от 1 до 10. Самый стильный кадр получит приз на банкете! 🪟👔",
]

current_task_index = 0


# --- Логирование ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# --- Мини-сервер для Render ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# --- Проверка, что пользователь — админ группы ---
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.message.from_user.id
    try:
        member = await context.bot.get_chat_member(GROUP_CHAT_ID, user_id)
        return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)
    except Exception as e:
        print(f"Ошибка проверки админа: {e}")
        return False


# --- Отправка одного задания ---
async def send_scheduled_task(context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_task_index
    if current_task_index < len(TASKS):
        task_text = TASKS[current_task_index]
        try:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"🎉 <b>Задание №{current_task_index + 1}</b>\n\n{task_text}\n\n📸 Присылайте результат в этот чат!",
                parse_mode='HTML'
            )
            print(f"Задание №{current_task_index + 1} отправлено.")
            current_task_index += 1
        except Exception as e:
            print(f"Ошибка отправки задания: {e}")
    else:
        print("Все задания выполнены!")


# --- КОМАНДЫ УПРАВЛЕНИЯ ---

async def start_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск квеста. Только для админов."""
    if not await is_admin(update, context):
        await update.message.reply_text("Эту команду может использовать только организатор. 🙅")
        return

    global current_task_index
    current_task_index = 0

    job_queue = context.application.job_queue
    for job in job_queue.get_jobs_by_name("quest_task"):
        job.schedule_removal()

    # 1. Приветствие — в группу
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=INTRO,
        parse_mode='HTML'
    )

    # 2. Запускаем цикл заданий (первое через 8 секунд)
    job_queue.run_repeating(
        send_scheduled_task,
        interval=TASK_INTERVAL,
        first=8,
        name="quest_task"
    )

    # 3. Подтверждение — только организатору (в личку)
    await update.message.reply_text(
        f"✅ Квест запущен!\n\n"
        f"Приветствие ушло в группу.\n"
        f"Первое задание — через 8 секунд.\n"
        f"Дальше — каждые {TASK_INTERVAL // 60} минут.\n\n"
        f"<b>Команды управления:</b>\n"
        f"/next — отправить следующее задание сейчас\n"
        f"/reset — сбросить и начать с №1\n"
        f"/stop — остановить квест",
        parse_mode='HTML'
    )


async def next_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправить следующее задание немедленно. Только для админов."""
    if not await is_admin(update, context):
        return
    await send_scheduled_task(context)


async def reset_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сбросить счётчик. Только для админов."""
    if not await is_admin(update, context):
        return
    global current_task_index
    current_task_index = 0
    await update.message.reply_text("🔄 Счётчик заданий сброшен. Следующее задание будет №1.")


async def stop_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Остановить рассылку. Только для админов."""
    if not await is_admin(update, context):
        return
    job_queue = context.application.job_queue
    removed = 0
    for job in job_queue.get_jobs_by_name("quest_task"):
        job.schedule_removal()
        removed += 1
    await update.message.reply_text(f"⏹ Квест остановлен (удалено задач: {removed}).")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот для свадебного квеста. 🎉\n\n"
        "Когда будете готовы начать — напишите /start_quest."
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

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_quest", start_quest))
    application.add_handler(CommandHandler("next", next_task))
    application.add_handler(CommandHandler("reset", reset_quest))
    application.add_handler(CommandHandler("stop", stop_quest))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    threading.Thread(target=run_health_server, daemon=True).start()

    print("Бот запущен и работает. Ожидание команды /start_quest...")
    application.run_polling()


if __name__ == '__main__':
    main()
