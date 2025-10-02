import os, sys, io, time, struct, machine, gc
import M5
from M5 import *
try:
    import urequests as requests
except:
    import requests
try:
    import usocket as socket
except:
    import socket  # fallback

label0 = None

# ===== CONFIG =====
UPLOAD_URL   = "http://192.168.1.121:8000/audio"
AUTH_TOKEN   = None
REPLY_PATH   = "/flash/reply.wav"

# --- сетевые «предохранители»
HTTP_TIMEOUT_S        = 7          # таймаут на соединение/чтение сокета (глобально)
REPLY_MAX_BYTES       = 2 * 1024 * 1024  # 2 MB максимум файла-ответа
REPLY_READ_CHUNK      = 4096       # размер куска при чтении ответа
REPLY_INACTIVITY_MS   = 5000       # если столько нет байтов — прерываем чтение

# --- watchdog
WDT_TIMEOUT_MS        = 10000      # если main-loop «встал» >10с — хард ребут

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
wdt = None

def _net_init_timeouts():
    # Глобальный таймаут для всех новых сокетов (работает внутри urequests)
    try:
        socket.setdefaulttimeout(HTTP_TIMEOUT_S)
    except Exception as e:
        print("setdefaulttimeout err:", e)

def _start_wdt():
    global wdt
    try:
        wdt = machine.WDT(timeout=WDT_TIMEOUT_MS)
    except Exception as e:
        print("WDT init err:", e)

def _feed_wdt():
    try:
        if wdt:
            wdt.feed()
    except:
        pass

def _wav_wrap(pcm_bytes, sr=SR, bits=BITS, ch=1):
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

def _post_wav_and_save_reply(wav_bytes, reply_path):
    """
    POST -> сохранить тело ответа в файл, с таймаутами и лимитами.
    Возвращает (ok, err_msg | None)
    """
    headers = {"Content-Type": "audio/wav"}
    if AUTH_TOKEN:
        headers["Authorization"] = AUTH_TOKEN

    r = None
    wrote = 0
    last_rx_ms = time.ticks_ms()
    try:
        # попытка со stream=True; если прошивка не поддерживает — обычный post
        try:
            r = requests.post(UPLOAD_URL, data=wav_bytes, headers=headers, stream=True)
        except TypeError:
            r = requests.post(UPLOAD_URL, data=wav_bytes, headers=headers)

        status = getattr(r, "status_code", 200)
        if status != 200:
            err_txt = ""
            try: err_txt = r.text
            except: pass
            return False, "HTTP {} {}".format(status, (err_txt or "")[:128])

        # если сервер указал Content-Length, можно проверить «заранее»
        try:
            clen = r.headers.get("Content-Length")
            if clen and int(clen) > REPLY_MAX_BYTES:
                return False, "Reply too big: {} bytes".format(clen)
        except:
            pass

        # потоковое чтение
        with open(reply_path, "wb") as f:
            raw = getattr(r, "raw", None)
            if raw is not None:
                while True:
                    _feed_wdt()
                    chunk = raw.read(REPLY_READ_CHUNK)
                    now = time.ticks_ms()

                    if chunk:
                        f.write(chunk)
                        wrote += len(chunk)
                        last_rx_ms = now
                        if wrote > REPLY_MAX_BYTES:
                            return False, "Reply exceeded {} bytes".format(REPLY_MAX_BYTES)
                    else:
                        # нет данных — проверим «молчание» по времени
                        if time.ticks_diff(now, last_rx_ms) > REPLY_INACTIVITY_MS:
                            return False, "Reply read timeout"
                        # маленькая пауза, чтобы не крутить CPU
                        time.sleep_ms(20)
                        continue

                    # если пришёл последний кусок (обычно .read() вернёт b"" после конца)
                    if len(chunk) < REPLY_READ_CHUNK:
                        break
            else:
                # fallback (может занять RAM на больших ответах)
                content = r.content
                wrote = len(content)
                if wrote > REPLY_MAX_BYTES:
                    return False, "Reply exceeded {} bytes".format(REPLY_MAX_BYTES)
                f.write(content)

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        try:
            if r: r.close()
        except:
            pass
        gc.collect()

def _start_next_chunk():
    global _current_chunk, _waiting_chunk
    _current_chunk = bytearray(CHUNK_SAMPLES * BYTES_PER_SAMPLE)
    Mic.record(_current_chunk, SR, False)
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
    label0 = Widgets.Label("A: rec/post | B: reboot", 8, 58, 1.0,
                           0xffffff, 0x222222, Widgets.FONTS.DejaVu18)
    _net_init_timeouts()
    _start_wdt()

def loop():
    global recording, pcm_buf
    M5.update()
    _feed_wdt()

    # жёсткий ребут по BtnB
    if BtnB.wasClicked():
        label0.setText("reboot…")
        time.sleep_ms(150)
        machine.reset()

    # старт записи
    if BtnA.wasPressed() and not recording:
        try: Speaker.end()
        except: pass
        Mic.begin()
        pcm_buf = bytearray()
        recording = True
        label0.setText("rec…")
        _start_next_chunk()

    # запись идёт
    if recording:
        _poll_chunk_and_append()
        if BtnA.isPressed() and not Mic.isRecording():
            _start_next_chunk()

        # стоп по отпусканию
        if BtnA.wasReleased():
            # ждём завершение НЕ дольше, чем 1 сек (мягкий таймаут)
            t0 = time.ticks_ms()
            while Mic.isRecording():
                _feed_wdt()
                if time.ticks_diff(time.ticks_ms(), t0) > 1000:
                    break
                time.sleep_ms(5)
            _poll_chunk_and_append()
            Mic.end()
            recording = False

            # выравниваем 16-бит
            if BITS == 16 and (len(pcm_buf) & 1):
                pcm_buf[:] = pcm_buf[:-1]

            label0.setText("wrap wav…")
            wav_bytes = _wav_wrap(bytes(pcm_buf), SR, BITS, 1)
            gc.collect()

            # POST -> ответ сохраняем в файл (с таймаутами)
            label0.setText("POST…reply")
            ok, err = _post_wav_and_save_reply(wav_bytes, REPLY_PATH)
            if not ok:
                label0.setText("POST err")
                print("POST/reply error:", err)
                # даём пользователю шанс ребутнуть кнопкой B, иначе WDT сам перезапустит
                time.sleep_ms(1200)
                label0.setText("A: rec/post | B: reboot")
                return

            # проигрываем только файл-ответ
            try:
                label0.setText("play reply…")
                Speaker.begin()
                try: Speaker.setVolumePercentage(80)
                except: pass

                # безопасное ожидание проигрывания (мягкий таймаут 30с)
                Speaker.playWavFile(REPLY_PATH)
                t0 = time.ticks_ms()
                while Speaker.isPlaying():
                    _feed_wdt()
                    if time.ticks_diff(time.ticks_ms(), t0) > 30000:
                        print("play timeout; stopping")
                        break
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
        # в крайнем случае — форс-ребут, чтобы не зависнуть в traceback
        try:
            time.sleep_ms(200)
            machine.reset()
        except:
            pass