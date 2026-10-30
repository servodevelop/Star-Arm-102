"""Keep third-party runtime output out of this version's sessions."""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import logging
import os

@contextmanager
def quiet_output():
    previous=logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with open(os.devnull,'w') as sink, redirect_stdout(sink), redirect_stderr(sink):
            yield
    finally:
        logging.disable(previous)
