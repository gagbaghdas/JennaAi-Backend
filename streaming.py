import threading
import queue
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain


class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration:
            raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)


class ChainStreamHandler(StreamingStdOutCallbackHandler):
    def __init__(self, gen):
        super().__init__()
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)


def llm_thread(g, prompt, llm, memory, params_dict):
    try:
        llm.callbacks = [ChainStreamHandler(g)]
        conversation = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=memory)
        conversation(params_dict)
    finally:
        g.close()


def chain(prompt, llm, memory, params_dict):
    g = ThreadedGenerator()
    threading.Thread(
        target=llm_thread, args=(g, prompt, llm, memory, params_dict)
    ).start()
    return g
