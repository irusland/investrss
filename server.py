import asyncio
import os
from datetime import datetime
import io
import logging
import openai

from fastapi import FastAPI, Response, Query
from starlette.requests import Request
from starlette.responses import HTMLResponse, FileResponse

from invest.marketdata.sniffer import MarketDataSniffer
from rss.rss import RSSFeeder
from static.path import STATIC_PATH
from m5stick.settings import OpenAISettings, AudioSettings

logger = logging.getLogger(__name__)


class RSSServer(FastAPI):
    """Fast API server to serve RSS feed to the client."""

    def __init__(
        self,
        feeder: RSSFeeder,
        market_data_sniffer: MarketDataSniffer,
        openai_settings: OpenAISettings,
        audio_settings: AudioSettings,
    ):
        super().__init__()
        self._feeder = feeder
        self._market_data_sniffer = market_data_sniffer
        self._openai_settings = openai_settings
        self._audio_settings = audio_settings

        openai.api_key = self._openai_settings.api_key

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

            # Create upload directory
            os.makedirs(self._audio_settings.upload_dir, exist_ok=True)

            # Generate filenames with timestamp
            timestamp = datetime.now().strftime(self._audio_settings.timestamp_format)
            filename = f"{self._audio_settings.filename_prefix}_{timestamp}.wav"
            filepath = os.path.join(self._audio_settings.upload_dir, filename)

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
                    model=self._openai_settings.whisper_model, file=audio_file
                )
                transcription = transcript.text
                logger.info(f"Transcription text: {transcription}")

                # Step 2: Generate chat response using GPT
                chat_response_text = transcription
                if transcription.strip():
                    chat_response = openai.chat.completions.create(
                        model=self._openai_settings.chat_model,
                        messages=[
                            {
                                "role": "system",
                                "content": self._openai_settings.system_prompt,
                            },
                            {"role": "user", "content": transcription},
                        ],
                        max_tokens=self._openai_settings.max_tokens,
                        temperature=self._openai_settings.temperature,
                    )
                    chat_response_text = chat_response.choices[
                        0
                    ].message.content.strip()
                    logger.info(f"Chat response: {chat_response_text}")

                # Step 3: Convert chat response to audio using TTS
                if chat_response_text.strip():
                    tts_response = openai.audio.speech.create(
                        model=self._openai_settings.tts_model,
                        voice=self._openai_settings.tts_voice,
                        instructions=self._openai_settings.tts_instructions,
                        input=chat_response_text,
                        response_format=self._openai_settings.response_format,
                    )
                    synthesized_audio = tts_response.content

                    # Save synthesized audio file
                    tts_filename = (
                        f"{self._audio_settings.tts_filename_prefix}_{timestamp}.wav"
                    )
                    tts_filepath = os.path.join(
                        self._audio_settings.upload_dir, tts_filename
                    )
                    with open(tts_filepath, "wb") as f:
                        f.write(synthesized_audio)
                    logger.info(f"Synthesized audio saved: {tts_filepath}")
                    logger.info(f"Original text: {transcription}")
                    logger.info(f"Response text: {chat_response_text}")

            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")

            return Response(
                content=synthesized_audio, media_type="audio/wav", status_code=200
            )

        except Exception as e:
            return Response(content=f"Error saving audio: {str(e)}", status_code=500)
