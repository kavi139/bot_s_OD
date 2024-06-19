"""
телеграмм бот для определения объектов на фото
"""
import os
import shutil
import asyncio
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from dotenv import load_dotenv
from TerraYolo.TerraYolo import TerraYoloV5

load_dotenv()
TOKEN = os.environ.get("TOKEN")
WORK_DIR = r"D:\vscode\bot_s_OD\sozdanie_pervogo_bota_s_OD\yolo"
os.makedirs(WORK_DIR, exist_ok=True)
yolov5 = TerraYoloV5(work_dir=WORK_DIR)

async def start(update, context): # "Создайте telegram-bot. Используя учебный код"
    """стартовая команда"""
    custom_keyboard = [['/start']]
    reply_markup = ReplyKeyboardMarkup(
        custom_keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    keyboard = [
        [
            InlineKeyboardButton("Распознать на фото", callback_data="detection")
        ]
    ]
    inline_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Работаю с форматами jpg, jpeg или png.",
        reply_markup=reply_markup
    )
    await update.message.reply_text(
        "Нажми на кнопку ниже, чтобы задать параметры для распознования.",
        reply_markup=inline_markup
    )
    _ = context

# "кнопки для выбора одного из нескольких видов объектов для распознавания"
async def button(update, context):
    """установка парметров распознования"""
    query = update.callback_query
    data = query.data

    if data == "detection":
        await query.answer()
        
        keyboard = [
            [ # "Распознавание с различным уровнем достоверности conf = [0.01, 0.5, 0.99]"
                InlineKeyboardButton("conf 0.01", callback_data="conf_0.01"),
                InlineKeyboardButton("conf 0.5", callback_data="conf_0.5"),
                InlineKeyboardButton("conf 0.99", callback_data="conf_0.99")
            ],
            [# "c различным уровнем метрики “пересечения на объединение”  iou = [0.01, 0.5, 0.99]"
                InlineKeyboardButton("iou 0.01", callback_data="iou_0.01"),
                InlineKeyboardButton("iou 0.5", callback_data="iou_0.5"),
                InlineKeyboardButton("iou 0.99", callback_data="iou_0.99")
            ],
            [# "определенных предобученных классов, например, только людей"
                InlineKeyboardButton("только люди", callback_data="classes_0"),
                InlineKeyboardButton("только бутылки", callback_data="classes_39"),
                InlineKeyboardButton("только машины", callback_data="classes_2")
            ],
            [
                InlineKeyboardButton("Продолжить", callback_data="proceed")
            ]
        ]
        reply_markup_parametr = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text("""*conf-Распознавание с различным уровнем достоверности
*iou-Уровень метрики "пересечения на объединение"
*Если не обозначить никакой класс, то будут распознаны все классы.""",
                                      reply_markup=reply_markup_parametr)

        context.user_data["parametrs"] = {}

    elif data.startswith("conf_"):
        conf = float(data.stplit("_")[1])
        context.user_data["parametrs"]["conf"] = conf
        await query.answer(f"Установлен уровень достоверности (conf) на {conf}")
    elif data.startswith("iou_"):
        iou = float(data.split("_")[1])
        context.user_data["parametrs"]["iou"] = iou
        await query.answer(
            f"Установлен уровень метрики пересечения (iou) на {iou}"
        )
    elif data.startswith("classes_"):
        classes = int(data.split("_")[1])
        context.user_data["parametrs"]["classes"] = classes
        await query.answer(f"Установлен фильтр по классу на {classes}")
    elif data == "proceed":
        if not context.user_data.get("parametrs"):
            await query.answer("Пожалуйста, выбери параметры распознования")
            return

        context.user_data["proceed"] = True
        await query.answer("Параметры приняты. Пришлите фото для распознования.")
        await asyncio.sleep(3)
        await query.message.delete()

async def delete_param_message_and_set_proceed(update, context):
    """удаление сообщения с параметрами и установка "флага" продолжения"""
    query = update.callback_query
    await query.message.delete()
    context.user_data["proceed"] = True

async def detection(update, context):
    """загрузка и обработка фотографий"""
    try:
        shutil.rmtree("images")
        shutil.rmtree(f"{WORK_DIR}\\yolov5\\runs")
    except FileNotFoundError:
        pass

    if update.message and (update.message.photo or update.message.document):
        if update.message.document and update.message.document.mime_type not in [
            "image/jpeg", "image/png"
            ]:
            await update.message.reply_text(
                "Пожалуйста, отправь изображение в формате jpg или png."
            )
            return
        parametrs = context.user_data.get("parametrs", {})
        conf = parametrs.get("conf", 0.5)
        iou = parametrs.get("iou", 0.5)
        classes = parametrs.get("classes", -1)
        if update.message.photo:
            new_file = await update.message.photo[-1].get_file()
            my_message = await update.message.reply_text(
                "Мы получили от тебя фото. Идет распознавание объектов..."
            )
        elif update.message.document:
            new_file = await update.message.photo[-1].get_file()
            my_message = await update.message.reply_rext(
                "Мы получили фото. Идет распознование объектов..."
            )
        os.makedirs("images", exist_ok=True)
        image_name = str(new_file.file_path).rsplit("/", maxsplit=1)[-1]
        image_path = os.path.join("images", image_name)
        await new_file.download_to_drive(image_path)

        dict1 = dict()
        dict1["weights"] = (
            "yolov5s.pt"
            )
        dict1["source"] = (
            image_path
            )
        if conf != 0.5:
            dict1["conf"] = conf
        if iou != 0.5:
            dict1["iou"] = iou
        if classes != -1:
            dict1["classes"] = classes
        yolov5.run(dict1, exp_type="test")
        await context.bot.delete_message(
            message_id=my_message.message_id, chat_id=update.message.chat_id
        )
        await update.message.reply_text(
            "Распознование объектов завершено."
        )
        output_image_path = f"{WORK_DIR}\\yolov5\\runs\\detect\\exp\\{image_name}"
        await update.message.reply_photo(
            open(output_image_path, "rb")
        )
    else:
        await update.message.reply_text(
            "Нужно отправить фото в формате jpg, jpeg или png"
            )

def main():
    """точка запуска бота"""
    application = Application.builder().token(TOKEN).build()
    print("Бот запущен...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    # "обработчик для случая, если пользователь подаст изображение не в сжатом виде"
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, detection))
    application.run_polling()

if __name__ == "__main__":
    main()
