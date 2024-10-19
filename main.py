import os
import re
import json
from random import choice
from time import time
from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from rosreestr2coord import Area
import geojson2kml

# Загрузка прокси
with open('proxy.json', 'r', encoding='utf-8') as f:
    PROXIES = json.load(f)

# Регулярное выражение для проверки кадастрового номера
CADASTRAL_NUMBER_REGEX = r'^\d{1,2}:\d{1,2}:(\d|\d{6,7}):\d{1,10}$'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка приветственного сообщения."""
    await update.message.reply_text(
        "Здравствуйте! Пожалуйста, введите кадастровый номер.",
        reply_markup=ForceReply(selective=True),
    )

async def handle_cadastral_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка введенного кадастрового номера."""
    cadastral_number = update.message.text

    if not re.match(CADASTRAL_NUMBER_REGEX, cadastral_number):
        await update.message.reply_text("Неверно введен кадастровый номер. Пожалуйста, попробуйте снова.")
        return

    area = Area(cadastral_number, proxy_url=choice(PROXIES))
    filename = str(cadastral_number.replace(":", "_"))
    geojson_path = f"tmp/{filename}.geojson"

    try:
        # Сохранение GeoJSON файла
        with open(geojson_path, "w+", encoding="utf-8") as f:
            f.write(area.to_geojson())
        
        # Конвертация в KML
        geojson2kml.convert_file(geojson_path, "tmp")
        
        # Отправка файлов пользователю
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(geojson_path, 'rb'))
        
        kml_path = f"tmp/{filename}.kml"
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(kml_path, 'rb'))
    
    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка, попробуйте еще раз.")
    
    finally:
        # Удаление временных файлов
        for path in [geojson_path, kml_path]:
            if os.path.exists(path):
                os.remove(path)

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token('YOUR_TELEGRAM_BOT_TOKEN').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cadastral_number))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()