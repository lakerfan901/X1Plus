import os, sys, time

class TailLog:
    def __init__(self, filepath, seek_end = True, interval = 1.0):
        self.filepath = filepath
        self.fd = None
        self.ino = None
        self.seek_end = seek_end
        self.buf = ""
        self.interval = interval

    def readline(self):
        """
        Read a line, non-blocking (returns None if no line is ready).
        """
        
        # Has the inode changed (i.e., the logs have rotated?)
        try:
            ino = os.stat(self.filepath).st_ino
        except FileNotFoundError:
            # the log is in the middle of being rotated (renamed away, but
            # not recreated yet); come back and look again in a moment
            return None
        if ino != self.ino:
            if self.fd:
                self.buf += self.fd.read() + "\n"
                self.fd.close()
            print(f"TailLog: reopened {self.filepath} and finished up {len(self.buf)} bytes", file = sys.stderr)
            self.fd = open(self.filepath, "r", encoding="utf-8", errors="replace")
            self.ino = os.fstat(self.fd.fileno()).st_ino

        # Grab some data from the buffer; if it's the first go-around, throw
        # all the data out, though.
        self.buf += self.fd.read()
        if self.seek_end:
            self.buf = ""
            self.seek_end = False
        
        # Grab the first line if there is one, and leave everything else
        # behind.
        if "\n" not in self.buf:
            return None
        line, self.buf = self.buf.split("\n", 1)
        return line
    
    def lines(self):
        """
        Generator to infinitely tail a log file.
        """
        while True:
            line = self.readline()
            if line is None:
                # (None means "nothing to read yet"; an empty string is just
                # a blank line in the log, and is not a reason to nap)
                time.sleep(self.interval)
            else:
                yield line
