import pytsk3
import pyewf
from pathlib import Path

class ImageSource(pytsk3.Img_Info):
    """
    Custom pytsk3 Img_Info implementation for different evidence sources.
    """
    def __init__(self, image_handle):
        self._image_handle = image_handle
        super(ImageSource, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self._image_handle.close()

    def get_size(self):
        return self._image_handle.get_media_size()

    def read(self, offset, length):
        self._image_handle.seek(offset)
        return self._image_handle.read(length)

class E01Source(ImageSource):
    @classmethod
    def open(cls, path: Path):
        # pyewf expects a list of filenames for split images
        # For simplicity, we assume single file or handle split detection later
        filenames = pyewf.glob(str(path))
        handle = pyewf.handle()
        handle.open(filenames)
        return cls(handle)

class RawSource(pytsk3.Img_Info):
    def __init__(self, path: Path):
        super(RawSource, self).__init__(str(path))
