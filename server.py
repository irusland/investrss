import asyncio
import os
from datetime import datetime
import io
import logging
import openai
from dotenv import load_dotenv

from fastapi import FastAPI, Response, Query
from starlette.requests import Request
from starlette.responses import HTMLResponse, FileResponse

from invest.marketdata.sniffer import MarketDataSniffer
from rss.rss import RSSFeeder
from static.path import STATIC_PATH

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

logger = logging.getLogger(__name__)

class RSSServer(FastAPI):
    """Fast API server to serve RSS feed to the client."""

    def __init__(self, feeder: RSSFeeder, market_data_sniffer: MarketDataSniffer):
        super().__init__()
        self._feeder = feeder
        self._market_data_sniffer = market_data_sniffer
        self.add_api_route("/feed", endpoint=self.get_feed, methods=["GET"])
        self.add_api_route("/html_render", endpoint=self.html_render, methods=["GET"])
        self.add_api_route("/get_file", endpoint=self.get_file, methods=["GET"])
        self.add_api_route("/audio", endpoint=self.audio, methods=["POST"])
        # self.on_event("startup")(self.on_startup)
        # self.on_event("shutdown")(self.on_shutdown)

    async def on_startup(self):
        asyncio.create_task(self._market_data_sniffer.run())

    async def on_shutdown(self):
        self._market_data_sniffer.stop()

    async def get_feed(self, request: Request) -> Response:
        feed = await self._feeder.get_feed()
        return Response(content=feed.rss(), media_type="application/xml")

    async def html_render(self, raw_html: str = Query(...)) -> Response:
        return HTMLResponse(content=raw_html)

    async def get_file(self, filename: str = Query(...)) -> Response:
        return FileResponse(STATIC_PATH / filename)

    async def audio(self, request: Request) -> Response:
        try:
            audio_data = await request.body()

            if not audio_data:
                return Response(content="No audio data received", status_code=400)

            audio_dir = "uploaded_audio"
            os.makedirs(audio_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{timestamp}.wav"
            filepath = os.path.join(audio_dir, filename)

            # Save original audio file
            with open(filepath, "wb") as f:
                f.write(audio_data)
            logger.info(f"Original audio saved: {filepath}")

            transcription = ""
            synthesized_audio = audio_data

            try:
                # Step 1: Convert audio to text using Whisper
                audio_file = io.BytesIO(audio_data)
                audio_file.name = filename

                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcription = transcript.text
                logger.info(f"Transcription text: {transcription}")

                # Step 2: Generate chat response using GPT
                chat_response_text = transcription
                if transcription.strip():
                    chat_response = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Ты голосовой помощник. Отвечай кратко и по делу на русском языке."},
                            {"role": "user", "content": transcription}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    chat_response_text = chat_response.choices[0].message.content.strip()
                    logger.info(f"Chat response: {chat_response_text}")

                # Step 3: Convert chat response to audio using TTS
                if chat_response_text.strip():
                    tts_response = openai.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=chat_response_text,
                        response_format="wav"
                    )
                    synthesized_audio = tts_response.content

                    # Save synthesized audio file
                    tts_filename = f"tts_{timestamp}.wav"
                    tts_filepath = os.path.join(audio_dir, tts_filename)
                    with open(tts_filepath, "wb") as f:
                        f.write(synthesized_audio)
                    logger.info(f"Synthesized audio saved: {tts_filepath}")
                    logger.info(f"Original text: {transcription}")
                    logger.info(f"Response text: {chat_response_text}")

            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")

            return Response(content=synthesized_audio, media_type="audio/wav", status_code=200)

        except Exception as e:
            return Response(content=f"Error saving audio: {str(e)}", status_code=500)
