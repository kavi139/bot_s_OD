import os
import shutil
from typing import Union
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardRemove,
    CallbackQuery
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext
)
from dotenv import load_dotenv
from TerraYolo.TerraYolo import TerraYoloV5

# Загрузка переменных окружения из .env
load_dotenv()

# Получение токена бота
TOKEN = os.environ.get("TOKEN")

# Инициализация класса YOLO
WORK_DIR = r"D:\vscode\bot_s_OD\sozdanie_pervogo_bota_s_OD\yolo"
os.makedirs(WORK_DIR, exist_ok=True)
yolov5 = TerraYoloV5(work_dir=WORK_DIR)

async def start(update: Update, context: CallbackContext):
    reply_markup_parametr = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Распознать на фото", callback_data="detection")]]
    )
    await update.message.reply_text(
        """Привет, я умею распознавать объекты на фотографиях.
Работаю с форматами jpg, jpeg или png.""",
        reply_markup=reply_markup_parametr
    )


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "detection":
        await query.answer()

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

        reply_markup_parametr = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text('''*conf-Распознавание с различным уровнем достоверности
*iou-Уровень метрики “пересечения на объединение”
*если не выбрать параметры, то будут использованы все классы, conf=0.5, iou=0.5''',
                                       reply_markup=reply_markup_parametr)

        context.user_data["parameters"] = {}

    elif data.startswith("conf_"):
        conf = float(data.split("_")[1])
        context.user_data["parameters"]["conf"] = conf
        await query.answer(f"Установлен уровень достоверности (conf) на {conf}")

    elif data.startswith("classes_"):
        classes = int(data.split("_")[1])
        context.user_data["parameters"]["classes"] = classes
        await query.answer(f"Установлен фильтр по классу на {classes}")

    elif data.startswith("iou_"):
        iou = float(data.split("_")[1])
        context.user_data["parameters"]["iou"] = iou
        await query.answer(f"Установлено значение метрики 'пересечения на объединение' (iou) на {iou}")

    elif data == "proceed":
        if not context.user_data.get("parameters"):
            await query.answer("Пожалуйста, выберите параметры распознавания.")
            return

        context.user_data["proceed"] = True
        await query.answer("Параметры приняты. Теперь отправьте фото для распознавания.")
        await query.message.delete()

    else:
        # Обработка нажатий на другие кнопки параметров
        pass


async def delete_param_message_and_set_proceed(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.delete()
    context.user_data["proceed"] = True

async def detection(update: Update, context: CallbackContext):
    try:
        shutil.rmtree("images")
        shutil.rmtree(f"{WORK_DIR}\\yolov5\\runs")
    except FileNotFoundError:
        pass

    if update.message and (update.message.photo or update.message.document):
        if update.message.document and update.message.document.mime_type not in ['image/jpeg', 'image/png']:
            await update.message.reply_text("Пожалуйста, отправьте изображение в формате JPEG или PNG.")
            return

        # получаем параметры из context.user_data
        parameters = context.user_data.get("parameters", {})
        conf = parameters.get("conf", 0.5)
        classes = parameters.get("classes", -1)
        iou = parameters.get("iou", 0.5)

        if update.message.photo:
            # получение файла из сообщения
            new_file = await update.message.photo[-1].get_file()
        elif update.message.document:
            # получение файла из сообщения
            new_file = await update.message.document.get_file()

        # имя файла на сервере
        os.makedirs("images", exist_ok=True)
        image_name = str(new_file.file_path).rsplit("/", maxsplit=1)[-1]
        image_path = os.path.join("images", image_name)
        # скачиваем файл с сервера Telegram в папку images
        await new_file.download_to_drive(image_path)

        # создаем словарь с параметрами
        test_dict = dict()
        test_dict["weights"] = (
            "yolov5x.pt"
        )
        test_dict["source"] = (
            image_path  # папка, в которую загружается присланное в бота изображение
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

        # отправляем пользователю результат
        output_image_path = f"{WORK_DIR}\\yolov5\\runs\\detect\\exp\\{image_name}"
        await update.message.reply_photo(
            open(output_image_path, "rb")
        )

    else:
        await update.message.reply_text("Пожалуйста, отправьте фотографию.")




def main():
    # Создаем объект класса Application
    global application
    application = Application.builder().token(TOKEN).build()
    print("Бот запущен...")

    # Добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавляем обработчик нажатия Inline кнопок
    application.add_handler(CallbackQueryHandler(button))

    # Добавляем новый обработчик для удаления сообщения с выбором параметров и установки флага "proceed" в True
    application.add_handler(CallbackQueryHandler(delete_param_message_and_set_proceed, pattern="delete_param_and_set_proceed"))

    # Добавляем обработчик фотографий
    application.add_handler(MessageHandler(filters.PHOTO, detection))

    # Запускаем бота
    application.run_polling()




if __name__ == "__main__":
    main()
