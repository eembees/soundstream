# coding=utf-8
import argparse
import socket
from pathlib import Path
from threading import Thread
from typing import Union
import wave
import io 


from more_itertools import chunked
import soundfile as sf

from global_constants_and_functions import *


class ReaderThread(Thread):
    """
    Worker's file reading and sending to server part.
    """

    def __init__(
        self, sock: socket.socket, infile: Union[Path, None] = None, *args, **kwargs
    ):
        """
        Initialization, making sure that the input file ends in .txt.
        :param sock:
        :param infile:
        """
        super(ReaderThread, self).__init__(*args, **kwargs)
        self.file_to_read = infile
        self.sock = sock

    def run(self) -> None:
        """
        Starts by registering with the server by sending init message.
        If the infile exists, read lines and send. Could possibly have added sleep statement here too.
        """
        # first thing is to send an alive signal to the server
        print(datetime.datetime.now().strftime("%H:%M:%S") + f" - Now sending: init")
        self.sock.sendto(b"init", ADDRESS)
        if self.file_to_read and self.file_to_read.exists():
            print(f"reading {self.file_to_read}")
            with open(self.file_to_read, "rb") as f:
                bytes_to_send = f.read()

            for bytechunk in chunked(bytes_to_send, BUFFERSIZE):
                # print(
                #     datetime.datetime.now().strftime("%H:%M:%S")
                #     + f" - Now sending: {bytechunk[:15]}"
                # )
                self.sock.sendto(bytes(bytechunk), ADDRESS)


class WriterThread(Thread):
    """
    Thread that listens and writes messages to output file.
    Also prints the output messages to command line to see what happens.
    Erases the given output files before writing.
    """

    def __init__(
        self,
        outfile: Path,
        sock: socket.socket,
        # reader: ReaderThread,
        *args,
        **kwargs,
    ) -> None:
        super(WriterThread, self).__init__(*args, **kwargs)
        self.file_to_write = outfile.with_suffix(".wav")
        # self.reader = reader
        # self.sock = self.reader.sock
        self.sock = sock

        if self.file_to_write.exists():
            self.file_to_write.unlink()
        self.file_to_write.touch()

        with wave.open(str(self.file_to_write), "wb") as f:
            f.setnchannels(AUDIO_FORMAT_WRITE["nchannels"])
            f.setframerate(AUDIO_FORMAT_WRITE["framerate"])
            f.setsampwidth(AUDIO_FORMAT_WRITE["sampwidth"])

    def run(self) -> None:
        """
        Listens and processes all incoming messages.
        Prints the message with timestamp
        """
        while True:
            message = self.sock.recvfrom(BUFFERSIZE)
            msg, addr = message

            print(
                datetime.datetime.now().strftime("%H:%M:%S")
                + f" - Received: {msg[:20]}"
            )

            audio, sr = io_data, io_sr = sf.read(
                io.BytesIO(bytearray(msg)),
                channels=AUDIO_FORMAT_WRITE["nchannels"],
                samplerate=AUDIO_FORMAT_WRITE["framerate"],
                subtype="PCM_16",
                format="RAW",
            )

            print(
                datetime.datetime.now().strftime("%H:%M:%S")
                + " Converted to audio of shape:"
                + str(audio.shape)
            )
            # print(datetime.datetime.now().strftime("%H:%M:%S") + str(audio))

            self.write_message_to_file(msg)

    def write_message_to_file(self, msg: str) -> None:
        """
        The function that actually prints to the file.
        Becase we have a line-by-line sender, we actually need to add the line break and append, not write to the file.
        """
        # if not msg.endswith("\n"): # TODO: remove
        #     msg += "\n"
        # hacky stuff don't do this in prod ever

        with wave.open(str(self.file_to_write), "rb") as f:
            _params = f.getparams()
            _frames = f.readframes(f.getnframes())

        with wave.open(str(self.file_to_write), "wb") as f:
            f.setparams(_params)
            f.writeframes(_frames)
            f.writeframes(msg)


def main(infile: Union[Path, None], outfile: Path) -> None:
    """
    Main worker loop.
    Can be called as a thread so we run multiple workers form one script concurrently.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    reader = ReaderThread(sock=sock, infile=infile)
    writer = WriterThread(sock=sock, outfile=outfile)

    reader.start()
    writer.start()


def parse_arguments() -> Tuple[Path, Union[Path, None]]:
    parser = argparse.ArgumentParser(
        description="Asynchronous UDP chat clients script. "
    )
    parser.add_argument(
        "--sourcefile",
        type=str,
        default="./input/source.raw",
        help="file to be used from the source. Default is input/source.raw",
    )
    parser.add_argument(
        "--sinkfile",
        type=str,
        default="./input/sink.raw",
        help="file to be used if we want the sink to send "
        "something back to the source. Default is None. "
        "Use 'None' for no sink file.",
    )
    args = vars(parser.parse_args())

    sinkfile = None if args["sinkfile"] == "None" else Path(args["sinkfile"])
    sourcefile = Path(args["sourcefile"])

    return sourcefile, sinkfile


if __name__ == "__main__":
    source_infile, sink_infile = parse_arguments()

    sink_outfile = Path("./output/sink.wav")
    source_outfile = Path("./output/source.wav")

    sink_outfile.parent.mkdir(exist_ok=True)

    def main_sink():
        main(infile=sink_infile, outfile=sink_outfile)

    def main_source():
        main(infile=source_infile, outfile=source_outfile)

    sink = Thread(target=main_sink)
    source = Thread(target=main_source)

    sink.start()
    source.start()
