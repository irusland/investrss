import logging
import os
import openai
import datetime
from dotenv import load_dotenv
from openai._legacy_response import LegacyAPIResponse
from openai.types import ImagesResponse

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()



TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise EnvironmentError("Please set TELEGRAM_TOKEN and OPENAI_API_KEY in your environment variables.")

openai.api_key = OPENAI_API_KEY

def get_prompt():
    return f"""Дата: {datetime.datetime.now().strftime('%Y-%m-%d')} 
    Создай сводку новостей для меня. Напиши основные события в политике, экономике и науке, а также главные успехи и проблемы на глобальном уровне. Сформулируй так, чтобы текст был сжатым и понятным, передавая основное за день. Поделись информацией об изменениях валютных курсов к рублю или других значимых рыночных событиях, если они есть. 
    """

# Function to get news completion using OpenAI's chat-based API
def get_openai_news(prompt):
    previous_day = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    input_prompt = f"Generate a news summary for {previous_day}: {prompt}"
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты ассистент, который ищет актуальные новости в интернете"},
            {"role": "user", "content": input_prompt}
        ],
        max_tokens=4000,
        temperature=0.7
    )
    logger.info(response)
    logger.info(dir(response))

    return response.choices[0].message.content.strip()

# Function to get OpenAI image
def get_openai_image(prompt):
    response: ImagesResponse = openai.images.generate(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )

    logger.info(response)
    logger.info(dir(response))

    return response.data[0].url


# Asynchronous function to handle sending news
async def send_news(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    prompt = get_prompt()
    try:
        news_summary = get_openai_news(prompt)
        await context.bot.send_message(chat_id=chat_id, text=news_summary)

        # Generate and send image
        image_url = get_openai_image(f"Новости дня: {news_summary} Нарисуй сгенерируй картинку, которая отражает суть новостей за день. ")
        await context.bot.send_message(chat_id=chat_id, text=f"Image for the news:\n{image_url}")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Error generating news or image: {e}")
        logger.exception("Error generating news or image")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('news', send_news))
    app.run_polling()

if __name__ == '__main__':
    main()