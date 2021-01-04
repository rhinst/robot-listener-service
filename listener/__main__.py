import os
from itertools import cycle
from time import sleep
from typing import Dict
from tempfile import NamedTemporaryFile
import json

from redis import Redis
from redis.client import PubSub
from speech_recognition import Microphone, Recognizer, AudioData, UnknownValueError

from listener.config import load_config
from listener.logging import logger, initialize_logger
from listener.microphone import get_microphone


def on_record_timed(message: Dict, microphone: Microphone, recognizer: Recognizer) -> AudioData:
    duration = message['duration']
    logger.debug(f"Recording {duration}s of audio")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(microphone)
        return recognizer.record(source, duration=float(duration))


def on_record_phrase(message, microphone: Microphone, recognizer: Recognizer) -> AudioData:
    logger.debug("Listening for a phrase")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(microphone)
        return recognizer.listen(source, phrase_time_limit=10)


def transcribe(audio: AudioData, recognizer: Recognizer) -> str:
    try:
        return recognizer.recognize_google(audio)
    except UnknownValueError:
        logger.warning("Unintelligible audio")
        return ""


def main():
    environment: str = os.getenv("ENVIRONMENT", "dev")
    config: Dict = load_config(environment)
    initialize_logger(level=config['logging']['level'], filename=config['logging']['filename'])
    redis_host = config['redis']['host']
    redis_port = config['redis']['port']
    logger.debug(f"Connecting to redis at {redis_host}:{redis_port}")
    redis_client: Redis = Redis(
        host=redis_host, port=redis_port, db=0
    )
    pubsub: PubSub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("subsystem.listener.command")
    handlers = {
        "timed": on_record_timed,
        "phrase": on_record_phrase
    }
    microphone = get_microphone(config['microphone']['name'])
    recognizer = Recognizer()
    try:
        while cycle([True]):
            # see if there is a command for me to execute
            if redis_message := pubsub.get_message():
                cmd_message = json.loads(redis_message['data'])
                audio = handlers[cmd_message['mode']](cmd_message, microphone, recognizer)
                f = NamedTemporaryFile(delete=False, mode="wb")
                f.write(audio.get_wav_data())
                f.close()
                request_id = cmd_message["request_id"]
                transcription = transcribe(audio, recognizer)
                out_message = {
                    "request_id": request_id,
                    "wav_file": f.name,
                    "transcription": transcription
                }
                logger.debug(f"Fulfilled request ID #{request_id}")
                if transcription:
                    logger.debug(f"Transcription was '{transcription}'")
                redis_client.publish("subsystem.listener.recording", json.dumps(out_message))
            sleep(0.1)
    except Exception:
        logger.exception("Something bad happened")
    finally:
        pubsub.close()
        redis_client.close()


if __name__ == '__main__':
    main()
