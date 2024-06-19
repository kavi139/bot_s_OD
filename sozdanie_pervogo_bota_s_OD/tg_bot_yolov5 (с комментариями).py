"""
телеграмм-бот определения объектов на фото
"""

# импорт необходимых библиотек и модулей
import os
import shutil
import asyncio
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from TerraYolo.TerraYolo import TerraYoloV5

# Загрузка переменных окружения из .env
load_dotenv()

# Получение токена бота
TOKEN = os.environ.get("TOKEN")

# Инициализация класса YOLO
WORK_DIR = r"D:\vscode\bot_s_OD\sozdanie_pervogo_bota_s_OD\yolo"
os.makedirs(WORK_DIR, exist_ok=True)  # создает директорию, если она не существует
yolov5 = TerraYoloV5(work_dir=WORK_DIR)  # создает экземпляр класса TerraYoloV5

async def start(update, context):  # обработчик команды /start
    custom_keyboard = [['/start']]  # создает настраиваемую клавиатуру с одной кнопкой "/start"
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)  # создает объект ReplyKeyboardMarkup

    keyboard = [  # создает настраиваемую inline-клавиатуру
        [
            InlineKeyboardButton("Распознать на фото", callback_data="detection")
        ]
    ]
    inline_markup = InlineKeyboardMarkup(keyboard)  # создает объект InlineKeyboardMarkup

    await update.message.reply_text("Работаю с форматами jpg, jpeg или png.", reply_markup=reply_markup)  # отправляет сообщение с информацией о поддерживаемых форматах
    await update.message.reply_text("Нажми на кнопку ниже, чтобы начать распознавание.", reply_markup=inline_markup)  # отправляет сообщение с приглашением начать распознавание
    _ = context  # не используется, но нужно для соответствия сигнатуре функции

async def button(update, context):  # обработчик нажатия inline-кнопок
    query = update.callback_query  # получает объект CallbackQuery
    data = query.data  # получает данные из callback_data

    if data == "detection":  # если нажата кнопка "Распознать на фото"
        await query.answer()  # удаляет сообщение с inline-клавиатурой

        keyboard = [  # создает настраиваемую inline-клавиатуру для выбора параметров распознавания
            [
                InlineKeyboardButton("conf 0.01", callback_data="conf_0.01"),
                InlineKeyboardButton("conf 0.5", callback_data="conf_0.5"),
                InlineKeyboardButton("conf 0.99", callback_data="conf_0.99")
            ],
            [
                InlineKeyboardButton("только люди", callback_data="classes_0"),
                InlineKeyboardButton("только бутылки", callback_data="classes_39"),
                InlineKeyboardButton("только машины", callback_data="classes_2")
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

        reply_markup_parametr = InlineKeyboardMarkup(keyboard)  # создает объект InlineKeyboardMarkup

        await query.message.reply_text('''*conf-Распознавание с различным уровнем достоверности
*iou-Уровень метрики “пересечения на объединение”
*Если не обозначить никакой класс, то модель найдёт все.''', reply_markup=reply_markup_parametr)  # отправляет сообщение с информацией о параметрах распознавания

        context.user_data["parameters"] = {}  # создает словарь для хранения выбранных параметров

    elif data.startswith("conf_"):  # если нажата кнопка выбора conf
        conf = float(data.split("_")[1])  # получает значение conf
        context.user_data["parameters"]["conf"] = conf  # сохраняет значение conf в словаре параметров
        await query.answer(f"Установлен уровень достоверности (conf) на {conf}")  # отправляет сообщение с информацией о выбранном conf

    elif data.startswith("classes_"):  # если нажата кнопка выбора класса
        classes = int(data.split("_")[1])  # получает значение класса
        context.user_data["parameters"]["classes"] = classes  # сохраняет значение класса в словаре параметров
        await query.answer(f"Установлен фильтр по классу на {classes}")  # отправляет сообщение с информацией о выбранном классе

    elif data.startswith("iou_"):  # если нажата кнопка выбора iou
        iou = float(data.split("_")[1])  # получает значение iou
        context.user_data["parameters"]["iou"] = iou  # сохраняет значение iou в словаре параметров
        await query.answer(f"Установлено значение метрики 'пересечения на объединение' (iou) на {iou}")  # отправляет сообщение с информацией о выбранном iou

    elif data == "proceed":  # если нажата кнопка "Продолжить"
        if not context.user_data.get("parameters"):  # если параметры не выбраны
            await query.answer("Пожалуйста, выбери параметры распознавания.")  # отправляет сообщение с приглашением выбрать параметры
            return

        context.user_data["proceed"] = True  # устанавливает флаг продолжения
        await query.answer("Параметры приняты. Теперь отправь фото для распознавания.")  # отправляет сообщение с приглашением отправить фото
        await asyncio.sleep(3) # задержка удаления сообщения на 3 сек.
        await query.message.delete()  # удаляет сообщение с inline-клавиатурой

async def delete_param_message_and_set_proceed(update, context):  # обработчик удаления сообщения с параметрами и установки флага продолжения
    query = update.callback_query  # получает объект CallbackQuery
    await query.message.delete()  # удаляет сообщение с inline-клавиатурой
    context.user_data["proceed"] = True  # устанавливает флаг продолжения

async def detection(update, context):  # обработчик распознавания объектов на фото
    try:
        shutil.rmtree("images")  # удаляет директорию "images"
        shutil.rmtree(f"{WORK_DIR}\\yolov5\\runs")  # удаляет директорию "runs"
    except FileNotFoundError:  # если директории не существует, игнорирует ошибку
        pass

    if update.message and (update.message.photo or update.message.document):  # если сообщение содержит фото или документ
        if update.message.document and update.message.document.mime_type not in ['image/jpeg', 'image/png']:  # если документ не является изображением
            await update.message.reply_text("Пожалуйста, отправь изображение в формате JPEG или PNG.")  # отправляет сообщение с информацией о поддерживаемых форматах
            return

        # получаем параметры из context.user_data
        parameters = context.user_data.get("parameters", {})
        conf = parameters.get("conf", 0.5)
        classes = parameters.get("classes", -1)
        iou = parameters.get("iou", 0.5)

        if update.message.photo:  # если сообщение содержит фото
            # получение файла из сообщения
            new_file = await update.message.photo[-1].get_file()
            my_message = await update.message.reply_text("Мы получили от тебя фотографию. Идет распознавание объектов...")  # отправляет сообщение о начале распознавания
        elif update.message.document:  # если сообщение содержит документ
            # получение файла из сообщения
            new_file = await update.message.document.get_file()
            my_message = await update.message.reply_text("Мы получили от тебя фотографию. Идет распознавание объектов...")  # отправляет сообщение о начале распознавания

        # имя файла на сервере
        os.makedirs("images", exist_ok=True)  # создает директорию "images", если она не существует
        image_name = str(new_file.file_path).rsplit("/", maxsplit=1)[-1]  # получает имя файла
        image_path = os.path.join("images", image_name)  # создает путь к файлу
        # скачиваем файл с сервера Telegram в папку images
        await new_file.download_to_drive(image_path)

        # создаем словарь с параметрами
        test_dict = dict()
        test_dict["weights"] = "yolov5x.pt"  # путь к весам модели
        test_dict["source"] = image_path  # путь к изображению
        # устанавливаем параметры кнопок в словарь
        if conf != 0.5:
            test_dict["conf"] = conf
        if classes != -1:
            test_dict["classes"] = classes
        if iou != 0.5:
            test_dict["iou"] = iou

        # вызов функции detect из класса TerraYolo)
        yolov5.run(test_dict, exp_type="test")

        await context.bot.delete_message(message_id=my_message.message_id, chat_id=update.message.chat_id)  # удаляет сообщение о начале распознавания

        await update.message.reply_text("Распознавание объектов завершено")  # отправляет сообщение о завершении распознавания

        # отправляем пользователю результат
        output_image_path = f"{WORK_DIR}\\yolov5\\runs\\detect\\exp\\{image_name}"
        await update.message.reply_photo(open(output_image_path, "rb"))  # отправляет изображение с результатом распознавания

    else:
        await update.message.reply_text("Пожалуйста, отправь фотографию.")  # если сообщение не содержит фото или документ, отправляет сообщение с приглашением отправить фото

def main():  # точка входа в программу
    application = Application.builder().token(TOKEN).build()  # создает экземпляр приложения Telegram
    print("Бот запущен...")  # выводит сообщение о запуске бота

    # Добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавляем обработчик нажатия Inline кнопок
    application.add_handler(CallbackQueryHandler(button))

    # Добавляем обработчик фотографий
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, detection))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":  # если скрипт запущен как главная программа, вызывает функцию main()
    main()
