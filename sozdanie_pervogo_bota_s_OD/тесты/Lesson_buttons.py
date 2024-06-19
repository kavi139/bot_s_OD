import os
import shutil
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from TerraYolo.TerraYolo import TerraYoloV5 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove

# загружаем переменные окружения из.env
load_dotenv()

# загружаем токен бота
TOKEN = os.environ.get("")

# инициализируем класс YOLO
WORK_DIR = r"D:\vscode\bot_s_OD\sozdanie_pervogo_bota_s_OD\yolo"
os.makedirs(WORK_DIR, exist_ok=True)
yolov5 = TerraYoloV5(work_dir=WORK_DIR)


# функция команды /start
async def start(update, context):
    """
    Отправляет сообщение пользователю с просьбой прикрепить фотографию для распознавания.
    """
    if update.message:
        await update.message.reply_text("Пришлите фото для распознавания")
    else:
        print("Обновление не содержит сообщения")

    # создаем список Inline кнопок
    keyboard = [[InlineKeyboardButton("Кнопка 1", callback_data="1"),
                InlineKeyboardButton("Кнопка 2", callback_data="2"),
                InlineKeyboardButton("Кнопка 3", callback_data="3")]]
    
    # создаем Inline клавиатуру
    reply_markup = InlineKeyboardMarkup(keyboard)

    # прикрепляем клавиатуру к сообщению
    await update.message.reply_text('Пример Inline кнопок', reply_markup=reply_markup)

# функция обработки нажатия на кнопки Inline клавиатуры
async def button(update, context):

    # параметры входящего запроса при нажатии на кнопку
    query = update.callback_query
    print(query)

    # отправка всплывающего уведомления
    await query.answer('Всплывающее уведомление!')
    
    # редактирование сообщения
    await query.edit_message_text(text=f"Вы нажали на кнопку: {query.data}")

# функция команды /help
async def help(update, context):

    # создаем список кнопок
    keyboard = ["Кнопка 1","Кнопка 2","Кнопка 3"]

    # создаем Reply клавиатуру
    reply_markup = ReplyKeyboardMarkup(keyboard, 
                                       resize_keyboard=True, 
                                       one_time_keyboard=True)

    # выводим клавиатуру с сообщением
    await update.message.reply_text('Пример Reply кнопок', reply_markup=reply_markup)


# функция для текстовых сообщений
async def text(update, context):
    await update.message.reply_text('Текстовое сообщение получено', reply_markup=ReplyKeyboardRemove())



# функция для работы с текстом
async def help_command(update, context):
    """
    Отправляет сообщение пользователю с помощью по командам бота.
    """
    await update.message.reply_text("Это помощь по командам бота")

"""""
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

    my_message = await update.message.reply_text(
        "Мы получили от тебя фотографию. Идет распознавание объектов..."
    )
    # получение файла из сообщения
    new_file = await update.message.photo[-1].get_file()

    # имя файла на сервере
    os.makedirs("images", exist_ok=True)
    image_name = str(new_file["file_path"]).rsplit("/", maxsplit=1)[-1]
    image_path = os.path.join("images", image_name)
    # скачиваем файл с сервера Telegram в папку images
    await new_file.download_to_drive(image_path)

    # создаем словарь с параметрами
    test_dict = dict()
    test_dict["weights"] = (
        "yolov5x.pt"  # Самые сильные веса yolov5x.pt, вы также можете загрузить версии: yolov5n.pt, yolov5s.pt, yolov5m.pt, yolov5l.pt (в порядке возрастания)
    )
    test_dict["source"] = (
        "images"  # папка, в которую загружаются присланные в бота изображения
    )
    # test_dict['conf'] = 0.85  # порог распознавания "Распознавание с различным уровнем достоверности conf = [0.01, 0.5, 0.99]"
    # test_dict['classes'] = '50 39'  # Распознавание определенных предобученных классов, например, только людей.
    # test_dict['iou'] = 0.85  # Распознавание с различным уровнем метрики “пересечения на объединение”  iou = [0.01, 0.5, 0.99]

    # вызов функции detect из класса TerraYolo)
    yolov5.run(test_dict, exp_type="test")

    # удаляем предыдущее сообщение от бота
    await context.bot.deleteMessage(
        message_id=my_message.message_id, chat_id=update.message.chat_id
    )

    # отправляем пользователю результат
    await update.message.reply_text(
        "Распознавание объектов завершено"
    )  # отправляем пользователю результат
    await update.message.reply_photo(
        open(f"{WORK_DIR}\\yolov5\\runs\\detect\\exp\\{image_name}", "rb")
    )
""""

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

    # Проверяем, есть ли в сообщении фотография
    if update.message.photo:
        my_message = await update.message.reply_text(
            "Мы получили от тебя фотографию. Идет распознавание объектов..."
        )
        
        new_file = await update.message.photo[-1].get_file()

        os.makedirs("images", exist_ok=True)
        image_name = str(new_file["file_path"]).rsplit("/", maxsplit=1)[-1]
        image_path = os.path.join("images", image_name)
        await new_file.download_to_drive(image_path)

        test_dict = dict()
        test_dict["weights"] = "yolov5x.pt"
        test_dict["source"] = "images"

        yolov5.run(test_dict, exp_type="test")

        await context.bot.deleteMessage(
            message_id=my_message.message_id, chat_id=update.message.chat_id
        )

        await update.message.reply_text(
            "Распознавание объектов завершено"
        )
        await update.message.reply_photo(
            open(f"{WORK_DIR}\\yolov5\\runs\\detect\\exp\\{image_name}", "rb")
        )
    else:
        await update.message.reply_text("Пожалуйста, отправьте фотографию для распознавания.")



def main():
    """
    Запускает бота.
    """
    # точка входа в приложение
    application = (
        Application.builder().token(TOKEN).build()
    )  # создаем объект класса Application
    print("Бот запущен...")

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # добавляем обработчик нажатия Inline кнопок
    application.add_handler(CallbackQueryHandler(button))

    # добавляем обработчик команды /help
    application.add_handler(CommandHandler("help", help))
    
    # добавляем обработчик изображений, которые загружаются в Telegram в СЖАТОМ формате
    # (выбирается при попытке прикрепления изображения к сообщению)
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.image, detection, block=False)) # Добавить обработчик для случая, если пользователь подаст изображение не в сжатом виде.
    # Добавить обработчик для случая, если пользователь подаст изображение не в сжатом виде.
    # application.add_handler(MessageHandler(filters.PHOTO | filters.DOCUMENT, detection, block=False))

    application.add_handler(MessageHandler(filters.TEXT, help_command))

    application.run_polling()  # запускаем бота (остановка CTRL + C)


if __name__ == "__main__":
    main()
