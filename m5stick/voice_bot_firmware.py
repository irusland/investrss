import os, sys, io, time, struct
import M5
from M5 import *
try:
    import urequests as requests
except:
    import requests

label0 = None

# ===== CONFIG =====
UPLOAD_URL   = "http://192.168.1.121:8000/audio"   # POST сюда отправляем наш WAV
AUTH_TOKEN   = None                                 # "Bearer abc123" или None
REPLY_PATH   = "/flash/reply.wav"                   # сюда сохраним WAV из ответа

# ===== RECORDING =====
SR = 16000
BITS = 16
CHUNK_MS = 200
BYTES_PER_SAMPLE = 2 if BITS == 16 else 1
CHUNK_SAMPLES = SR * CHUNK_MS // 1000

recording = False
pcm_buf = None
_current_chunk = None
_waiting_chunk = False

def _wav_wrap(pcm_bytes, sr=SR, bits=BITS, ch=1):
    """Собираем минимальный PCM WAV."""
    if bits == 8:
        pcm_bytes = bytes(((b + 128) & 0xFF) for b in pcm_bytes)
    data_size = len(pcm_bytes)
    byte_rate = sr * ch * (bits // 8)
    block_align = ch * (bits // 8)
    header = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
    fmt = (b"fmt " + struct.pack("<IHHIIHH",
                                 16, 1, ch, sr, byte_rate, block_align, bits))
    data_hdr = b"data" + struct.pack("<I", data_size)
    return header + fmt + data_hdr + pcm_bytes

def _post_wav_and_save_reply(wav_bytes, reply_path, chunk_size=4096):
    """
    POST-им WAV на сервер и сохраняем ТЕЛО ОТВЕТА в файл (ожидаем тоже WAV).
    Читаем потоково, чтобы не держать всё в RAM.
    """
    headers = {"Content-Type": "audio/wav"}
    if AUTH_TOKEN:
        headers["Authorization"] = AUTH_TOKEN

    r = None
    try:
        # Некоторые прошивки поддерживают stream=..., некоторые нет — ловим оба варианта
        try:
            r = requests.post(UPLOAD_URL, data=wav_bytes, headers=headers, stream=True)
        except TypeError:
            r = requests.post(UPLOAD_URL, data=wav_bytes, headers=headers)

        status = getattr(r, "status_code", 200)
        if status != 200:
            # Попробуем прочитать текст ошибки (если есть)
            err_txt = ""
            try:
                err_txt = r.text
            except:
                pass
            return False, "HTTP {} {}".format(status, err_txt[:128] if err_txt else "")

        # Сохраняем ответ по кускам
        with open(reply_path, "wb") as f:
            raw = getattr(r, "raw", None)
            if raw is not None:
                while True:
                    buf = raw.read(chunk_size)
                    if not buf:
                        break
                    f.write(buf)
            else:
                # fallback — может занять RAM для больших ответов
                f.write(r.content)
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        try:
            if r:
                r.close()
        except:
            pass

def _start_next_chunk():
    global _current_chunk, _waiting_chunk
    _current_chunk = bytearray(CHUNK_SAMPLES * BYTES_PER_SAMPLE)
    Mic.record(_current_chunk, SR, False)  # неблокирующе
    _waiting_chunk = True

def _poll_chunk_and_append():
    global _current_chunk, _waiting_chunk, pcm_buf
    if _waiting_chunk and not Mic.isRecording():
        pcm_buf.extend(_current_chunk)
        _current_chunk = None
        _waiting_chunk = False

def setup():
    global label0
    M5.begin()
    Widgets.setRotation(1)
    Widgets.fillScreen(0x222222)
    label0 = Widgets.Label("Hold A: REC -> POST -> REPLY", 8, 58, 1.0,
                           0xffffff, 0x222222, Widgets.FONTS.DejaVu18)

def loop():
    global recording, pcm_buf
    M5.update()

    # Старт записи по нажатию A
    if BtnA.wasPressed() and not recording:
        try:
            Speaker.end()
        except:
            pass
        Mic.begin()
        pcm_buf = bytearray()
        recording = True
        label0.setText("rec…")
        _start_next_chunk()

    # Пока пишем — собираем куски
    if recording:
        _poll_chunk_and_append()
        if BtnA.isPressed() and not Mic.isRecording():
            _start_next_chunk()

        # Останов по отпусканию
        if BtnA.wasReleased():
            while Mic.isRecording():
                time.sleep_ms(5)
            _poll_chunk_and_append()
            Mic.end()
            recording = False

            # Выровняем длину для 16-бит
            if BITS == 16 and (len(pcm_buf) & 1):
                pcm_buf[:] = pcm_buf[:-1]

            # Заворачиваем в WAV
            label0.setText("wrap wav…")
            wav_bytes = _wav_wrap(bytes(pcm_buf), SR, BITS, 1)

            # POST -> сохранить ответный WAV в файл
            label0.setText("POST…wait reply")
            ok, err = _post_wav_and_save_reply(wav_bytes, REPLY_PATH, chunk_size=4096)
            if not ok:
                label0.setText("POST/reply err")
                print("POST/reply error:", err)
                time.sleep_ms(1000)
                label0.setText("Hold A again")
                return

            # Проигрываем ИМЕННО файл-ответ сервера
            try:
                label0.setText("play reply…")
                Speaker.begin()
                try:
                    Speaker.setVolumePercentage(80)
                except:
                    pass
                Speaker.playWavFile(REPLY_PATH)
                while Speaker.isPlaying():
                    time.sleep_ms(10)
                label0.setText("done")
            except Exception as e:
                label0.setText("play err")
                print("Playback error:", e)

    time.sleep_ms(5)

if __name__ == '__main__':
    try:
        setup()
        while True:
            loop()
    except (Exception, KeyboardInterrupt) as e:
        print("Error:", e)