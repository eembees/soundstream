# coding=utf-8
import datetime
from typing import Tuple
import json


HOST = "localhost"
PORT = 2205
ADDRESS = (HOST, PORT)
BUFFERSIZE = 2048
SLEEPTIME = 0.0001

AUDIO_FORMAT_WRITE = dict(nchannels=1, 
        sampwidth=2, 
        framerate=8000,
        format="WAV",
        subtype="PCM_16"
        )

def decode_message(message: Tuple[bytes, int]) -> Tuple[str, int]:
    """
    Decodes the message from byte to a tuple containing the origin address and the message as a string.
    """
    msg, addr = message
    msg = msg.decode()
    msg_dict = json.loads(msg)
    # addr = int(addr.decode())
    return msg_dict["message"], addr


def encode_message(msg: str) -> bytes:
    """
    Encodes the message to bytes, but as a JSON file so as to ensure transmission of empty packets.
    """
    d = {"time": datetime.datetime.now().strftime("%H:%M:%S"), "message": msg}

    d_json = json.dumps(d)

    return d_json.encode()
