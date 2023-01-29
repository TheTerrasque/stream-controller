from io import BytesIO
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.conf import settings

class ChunkedUploadHandler(TemporaryFileUploadHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = BytesIO()
        self.chunk_size = getattr(settings, "CHUNKED_UPLOADER_HANDLER_CHUNK_SIZE") or 1024 * 1024

    def receive_data_chunk(self, raw_data, start):
        self.buffer.write(raw_data)
        if self.buffer.tell() > self.chunk_size:
            self.flush_buffer()

    def flush_buffer(self):
        self.file.write(self.buffer.getvalue())
        self.buffer.seek(0)
        self.buffer.truncate()

    def file_complete(self, file_size):
        self.flush_buffer()
        self.file.seek(0)
        self.file.size = file_size
        return self.file
