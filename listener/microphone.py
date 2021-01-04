from speech_recognition import Microphone


def get_microphone(name: str) -> Microphone:
    for index, mic_name in enumerate(Microphone.list_microphone_names()):
        if mic_name.lower() == name.lower():
            return Microphone(index)
    raise Exception(f"Unknown microphone name: {name}")