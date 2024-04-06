from dotenv import load_dotenv

from telegram_notifier_settings import TelegramNotifierSettings
import requests

if __name__ == "__main__":
    load_dotenv()
    telegram_notifier_settings = TelegramNotifierSettings(chat_id="FAKE")
    url = f"https://api.telegram.org/bot{telegram_notifier_settings.token}/getUpdates"

    response = requests.get(url)
    print(response.json())
