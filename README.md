# Running the software

1. Put the input files into the `./input` directory, and name them `source.txt` and `sink.txt`.
   Ensure that the `./output` directory exists.
1. Start the server by running `server.py`
1. Run the workers by running the script `worker.py` with

### Server

Our server will have two threads:

#### Receiver Thread

This thread receives messages and puts them into the queue.

#### Broadcasting Thread

This thread gets a message from the queue and sends it out to all clients

### Client

Each client will also have 2 threads

#### Reader thread

The reader thread will read threads from a file and send them to the server.

#### Writer Thread

The writer will receive messages from the server and write them to a file.
