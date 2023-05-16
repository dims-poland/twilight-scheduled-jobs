import sys
import signal

terminate_flag = False
print_terminate_message_files = None


def set_terminate_flag(signum, frame):
    global terminate_flag
    global print_terminate_message_files
    terminate_flag = True

    if print_terminate_message_files:
        for f in print_terminate_message_files:
            print('\n\nTerminate signal received ({:d}), processing will be terminated when current task finishes.\n'.format(
                signum
            ), file=f)
            f.flush()


def init(terminate_signal=signal.SIGTERM, print_term_message_files=[sys.stdout, sys.stderr]):
    signal.signal(terminate_signal, set_terminate_flag)
    global print_terminate_message_files
    print_terminate_message_files = print_term_message_files


def stop(terminate_signal=signal.SIGTERM):
    signal.signal(terminate_signal, signal.SIG_DFL)


class SafelyTerminated(Exception):
    msg = ''
    file = None

    def __init__(self, msg='', file=None):
        self.msg = msg
        self.file = file

    def __str__(self):
        full_msg = 'Safely terminated'
        if self.file:
            full_msg += ' at ' + self.file
        if self.msg:
            full_msg += ': ' + self.msg
        return full_msg
