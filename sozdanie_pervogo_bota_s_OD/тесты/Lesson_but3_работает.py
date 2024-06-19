# но по параментрам редыдущего фото

import os
import shutil
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from TerraYolo.TerraYolo import TerraYoloV5
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# Загрузка переменных окружения из .env
load_dotenv()

# Получение токена бота
TOKEN = os.environ.get("TOKEN")

# Инициализация класса YOLO
WORK_DIR = r"D:\vscode\bot_s_OD\sozdanie_pervogo_bota_s_OD\yolo"
os.makedirs(WORK_DIR, exist_ok=True)
yolov5 = TerraYoloV5(work_dir=WORK_DIR)


# Функция команды /start
async def start(update: Update, context):
    await update.message.reply_text("""Привет, я умею распознавать объекты на фотографиях.
Пришли фото в формате jpg, jepg или png и выбери параметры распознавания.""")


# Функция обработки нажатия кнопок
async def button(update, context):
    query = update.callback_query
    data = query.data

    if data.startswith("conf_"):
        conf = float(data.split("_")[1])
        await query.answer(f"Установлен порог распознавания: {conf}")
        context.user_data["conf"] = conf
    elif data.startswith("classes_"):
        classes = int(data.split("_")[1])
        await query.answer(f"Установлены классы объектов: {classes}")
        context.user_data["classes"] = classes
    elif data.startswith("iou_"):
        iou = float(data.split("_")[1])
        await query.answer(f"Установлен уровень метрики пересечения на объединение: {iou}")
        context.user_data["iou"] = iou
    elif data == "proceed":
        context.user_data["proceed"] = True
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)


# Функция для работы с текстом
async def text(update, context):
    await update.message.reply_text(
        """Вряд ли я смогу ответить что-то осмысленное на это, 
но я могу распознать объекты на тех фотографиях которые пришлёшь""",
        reply_markup=ReplyKeyboardRemove()
    )


# Функция обработки изображения
# функция обработки изображения
async def detection(update, context):
    """
    Удаляет папки images и runs, загружает изображение, вызывает функцию detect из класса TerraYolo,
    удаляет предыдущее сообщение от бота, отправляет пользователю результат.
    """
    try:
        shutil.rmtree("images")
        shutil.rmtree(f"{WORK_DIR}\\yolov5\\runs")
    except FileNotFoundError:
        pass

    if update.message and (update.message.photo or update.message.document):
        if update.message.document and update.message.document.mime_type not in ['image/jpeg', 'image/png']:
            await update.message.reply_text("Пожалуйста, отправьте изображение в формате JPEG или PNG.")
            return

        my_message = await update.message.reply_text(
            "Мы получили от тебя фотографию. Идет распознавание объектов..."
        )

        if update.message.photo:
            # получение файла из сообщения
            new_file = await update.message.photo[-1].get_file()
        elif update.message.document:
            # получение файла из сообщения
            new_file = await update.message.document.get_file()

       # имя файла на сервере
        os.makedirs("images", exist_ok=True)
        image_name = str(new_file["file_path"]).rsplit("/", maxsplit=1)[-1]
        image_path = os.path.join("images", image_name)
        # скачиваем файл с сервера Telegram в папку images
        await new_file.download_to_drive(image_path)

        # Определяем клавиатуру
        keyboard = [
            [
                InlineKeyboardButton("conf 0.01", callback_data="conf_0.01"),
                InlineKeyboardButton("conf 0.5", callback_data="conf_0.5"),
                InlineKeyboardButton("conf 0.99", callback_data="conf_0.99")
            ],
            [
                InlineKeyboardButton("только люди", callback_data="classes_0"),
                InlineKeyboardButton("только бутылки", callback_data="classes_39"),
                InlineKeyboardButton("только авто", callback_data="classes_2")
            ],
            [
                InlineKeyboardButton("iou 0.01", callback_data="iou_0.01"),
                InlineKeyboardButton("iou 0.5", callback_data="iou_0.5"),
                InlineKeyboardButton("iou 0.99", callback_data="iou_0.99")
            ],
            [
                InlineKeyboardButton("Продолжить", callback_data="proceed")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.chat_data["message_id"] = update.message.message_id

        await update.message.reply_text('''*conf-Распознавание с различным уровнем достоверности
*iou-Уровень метрики “пересечения на объединение”
*если не выбрать параметры, то будут использованы все классы, conf=0.5, iou=0.5''',
                                     reply_markup=reply_markup)

        # Добавляем обработчик для кнопки "Продолжить"
        async def proceed_callback_query_handler(update, context):
            query = update.callback_query
            if query.data == "proceed":
                context.user_data["proceed"] = True

        context.application.add_handler(CallbackQueryHandler(proceed_callback_query_handler))

        # Добавляем цикл ожидания нажатия кнопки "Продолжить"
        while True:
            if "proceed" in context.user_data:
                break
            await asyncio.sleep(1)

        # удаляем обработчик кнопки "Продолжить"
        context.application.remove_handler(CallbackQueryHandler(proceed_callback_query_handler))

        # получаем параметры из нажатых кнопок
        conf = context.user_data.get("conf", 0.5)
        classes = context.user_data.get("classes", -1)
        iou = context.user_data.get("iou", 0.5)

        # создаем словарь с параметрами
        test_dict = dict()
        test_dict["weights"] = (
            "yolov5x.pt"
        )
        test_dict["source"] = (
            "images"  # папка, в которую загружаются присланные в бота изображения
        )
        # устанавливаем параметры кнопок в словарь
        if conf != 0.5:
            test_dict["conf"] = conf
        if classes != -1:
            test_dict["classes"] = classes
        if iou != 0.5:
            test_dict["iou"] = iou

        # вызов функции detect из класса TerraYolo)
        yolov5.run(test_dict, exp_type="test")

        # удаляем предыдущее сообщение от бота
        await context.bot.deleteMessage(
            message_id=my_message.message_id, chat_id=update.message.chat_id
        )

        # отправляем пользователю результат
        await update.message.reply_text(
            "Распознавание объектов завершено"
        )# отправляем пользователю результат
        await update.message.reply_photo(
            open(f"{WORK_DIR}\\yolov5\\runs\\detect\\exp\\{image_name}", "rb")
        )
    else:
        await update.message.reply_text("Пожалуйста, отправьте фотографию.")





# Точка входа в приложение
def main():
    # Создаем объект класса Application
    application = Application.builder().token(TOKEN).build()
    print("Бот запущен...")

    # Добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавляем обработчик нажатия Inline кнопок
    application.add_handler(CallbackQueryHandler(button))

    # Добавляем обработчик изображений, которые загружаются в Telegram в СЖАТОМ формате
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, detection, block=False))

    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()
