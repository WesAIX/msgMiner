import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events

# === Загрузка .env ===
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

# === Конфигурация ===
session_name = 'sessions/my_session'
channels_file = 'channels.json'
messages_dir = 'saved_messages'
log_file = 'app.log'

# === Логирование ===
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# === Убедимся, что нужные папки существуют ===
os.makedirs(messages_dir, exist_ok=True)
os.makedirs(os.path.dirname(session_name), exist_ok=True)

# === Загрузка списка каналов ===
def load_channels():
    try:
        with open(channels_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при загрузке каналов: {e}")
        return []

# === Сохранение сообщений ===
def save_message(channel, message_id, timestamp, text):
    filename = os.path.join(messages_dir, f"{channel.replace('@', '')}.json")
    entry = {
        "id": message_id,
        "date": timestamp,
        "message": text
    }

    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        else:
            messages = []

        # Проверим дубликаты по id
        if any(m["id"] == message_id for m in messages):
            return

        messages.append(entry)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

        logging.info(f"[{channel}] Новое сообщение сохранено: {message_id}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении сообщения {message_id} из {channel}: {e}")

# === Основной скрипт ===
async def main():
    channels = load_channels()
    if not channels:
        logging.warning("Список каналов пуст.")
        return

    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    # Получим entities каналов
    channel_entities = {}
    for channel in channels:
        try:
            entity = await client.get_entity(channel)
            channel_entities[entity.id] = channel
        except Exception as e:
            logging.error(f"Ошибка при загрузке канала {channel}: {e}")

    # === Обработка новых сообщений ===
    @client.on(events.NewMessage(chats=list(channel_entities.keys())))
    async def handler(event):
        try:
            channel_id = event.chat_id
            channel_username = channel_entities.get(channel_id)
            message = event.message

            if message.text:
                timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
                save_message(channel_username, message.id, timestamp, message.text)
        except Exception as e:
            logging.error(f"Ошибка в обработчике события: {e}")

    print("🔌 Бот запущен. Ожидаю новые сообщения... (Ctrl+C для выхода)")
    logging.info("Бот запущен и ожидает новые сообщения")
    await client.run_until_disconnected()

# === Точка входа ===
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
