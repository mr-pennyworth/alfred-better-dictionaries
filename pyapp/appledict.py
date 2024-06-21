# -*- coding: utf-8 -*-

import io
import struct
import typing
import zlib


def read_int(f: typing.BinaryIO) -> int:
    return struct.unpack("i", f.read(4))[0]


# original source for parsing the '.dictionary' format:
# https://gist.github.com/josephg/5e134adf70760ee7e49d
class DictBody:
    def __init__(self, body_data_filepath: str):
        self.body_data_filepath = body_data_filepath

    def _sections(self) -> typing.Iterable[bytes]:
        """Return decompressed sections of the dict body.

        Each decompressed chunk contains multiple definitions.
        Each definition is of the format:
          [defn_size (4 bytes (not including itself)),
           XML defn  (defn_size bytes)]
        """
        with open(self.body_data_filepath, "rb") as f:
            # first 64 bytes of a Body.data file are always all-zeroes,
            # skip them
            f.seek(0x40)

            # The next four bytes represent an integer denoting remaining
            # number of bytes in the Body.data file
            limit = 0x40 + read_int(f)

            # TODO: for 'HeapDataCompressionType': 2 (in Info.plist),
            #  we need to skip to byte number 96, but not if it is 1.
            f.seek(0x60)

            while f.tell() < limit:
                # a Body.data file can contain multiple sections with the format:
                # [section_size      (4 bytes (not including itself)),
                #  ???               (4 bytes), (no idea what these are!)
                #  decompressed_size (4 bytes),
                #  compressed_data   (section_size-8 bytes)]
                compressed_size = read_int(f) - 8
                _ = f.read(4)  # no idea about these 4 bytes
                decompressed_size = read_int(f)
                decompressed = zlib.decompress(f.read(compressed_size))
                yield decompressed[:decompressed_size]

    def definitions(self) -> typing.Iterable[str]:
        """Return definitions from the dict in XML format.

        An example definition (just the opening tag):
         <d:entry
           xmlns:d=".apple.com/DTDs/DictionaryService-1.0.rng"
           id="m_en_gbus0134270"
           d:title="apple"
           class="entry">
        """
        for section in self._sections():
            # each decompressed chunk contains multiple definitions
            # each definition is of the format:
            # [defn_size (4 bytes (not including itself)),
            #  XML defn  (defn_size bytes)]
            section_size = len(section)
            section = io.BytesIO(section)  # convert to typing.BinaryIO
            while section.tell() < section_size:
                defn_size = read_int(section)
                yield section.read(defn_size).decode("utf-8")
