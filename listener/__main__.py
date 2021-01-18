import os
from itertools import cycle
from typing import Dict

from redis import Redis
import pyaudio
from pocketsphinx.pocketsphinx import Decoder

from listener.config import load_config
from listener.logging import logger, initialize_logger


MODELDIR = os.path.join(os.path.dirname(__file__), "../model")


def main():
    environment: str = os.getenv("ENVIRONMENT", "dev")
    config: Dict = load_config(environment)
    initialize_logger(
        level=config["logging"]["level"], filename=config["logging"]["filename"]
    )
    redis_host = config["redis"]["host"]
    redis_port = config["redis"]["port"]
    logger.debug(f"Connecting to redis at {redis_host}:{redis_port}")
    redis_client: Redis = Redis(host=redis_host, port=redis_port, db=0)

    logger.debug("Initializing PyAudio interface")
    audio = pyaudio.PyAudio()
    logger.debug("Intializing pocketsphinx Decoder")
    decoder_config = Decoder.default_config()
    decoder_config.set_string("-hmm", os.path.join(MODELDIR, "en-us/en-us"))
    decoder_config.set_string("-lm", os.path.join(MODELDIR, "en-us/en-us.lm.bin"))
    decoder_config.set_string(
        "-dict", os.path.join(MODELDIR, "en-us/cmudict-en-us.dict")
    )
    decoder = Decoder(decoder_config)

    logger.debug("Opening audio stream")
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024,
        input_device_index=config["microphone"]["card_index"],
    )
    stream.start_stream()

    in_speech_bf = False
    decoder.start_utt()

    try:
        logger.debug("Starting decoder loop")
        while cycle([True]):
            buf = stream.read(1024)
            if buf:
                logger.debug("Decoding raw audio")
                decoder.process_raw(buf, False, False)
                if decoder.get_in_speech() != in_speech_bf:
                    logger.debug("GOT HERE")
                    in_speech_bf = decoder.get_in_speech()
                    if not in_speech_bf:
                        decoder.end_utt()
                        transcription = decoder.hyp().hypstr
                        logger.debug(f"Result: {transcription}")
                        redis_client.publish(
                            "subsystem.listener.recording", transcription
                        )
                        decoder.start_utt()
            else:
                logger.debug("Buffer closed. Ending")
                break
        decoder.end_utt()
    except Exception:
        logger.exception("Something bad happened")
    finally:
        redis_client.close()


if __name__ == "__main__":
    main()
