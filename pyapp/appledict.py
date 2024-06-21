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

            # There seem to be two distinct formats of the header.
            # One where the body begins at 0x60, and another where
            # the body begins at 0x44.
            #
            # Look at these two examples:
            # "New Oxford American Dictionary.dictionary" that comes
            # pre-installed on macOS
            # ❯ xxd Body.data | head
            #    ... skipped ...
            # 00000030: 0000 0000 0000 0000 0000 0000 0000 0000
            # 00000040: d39b 8001 0000 0000 ffff ffff 2000 0000
            # 00000050: 0000 0000 fa02 0000 ffff ffff ffff ffff
            # 00000060: 6880 0000 6480 0000 0959 0400 78da ecbd
            #
            # "Littré.dictionary" found at
            # https://www.competencemac.com/Bureautique-Dictionnaires-en-francais_a1737.html
            # ❯ xxd Body.data | head
            #    ... skipped ...
            # 00000030: 0000 0000 0000 0000 0000 0000 0000 0000
            # 00000040: 46a2 af02 9103 0000 8d03 0000 3906 0000
            # 00000050: 789c 6d55 db6e db46 107d 8ebf 62a0 1725
            # 00000060: a84c d67d 5469 0272 8c02 058a a040 9abc
            #
            # Based on the above two examples, and looking at the function
            # guessFileOffsetLimit the pyglossary project,
            # (https://github.com/ilius/pyglossary/blob/b41161d3f38a7e6523d315f4b8555083ef196e71/pyglossary/plugins/appledict_bin/appledict_file_tools.py#L58)
            # looking for 0000 0000 ffff ffff at 0x44 seems to be a
            # reliable enough (?) way to distinguish between these two
            if (read_int(f), read_int(f)) == (0, -1):
                f.seek(0x60)
            else:
                f.seek(0x44)

            while f.tell() < limit:
                # Body.data file can contain multiple sections with the format:
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
            # each decompressed chunk:
            # 1) either contains one single definition,
            # 2) or multiple definitions of the format:
            #    [defn_size (4 bytes (not including itself)),
            #     XML defn  (defn_size bytes)]
            opening_tag = b"<d:entry"
            if section[: len(opening_tag)] == opening_tag:
                yield section.decode("utf-8")
            else:
                section_size = len(section)
                section = io.BytesIO(section)  # convert to typing.BinaryIO
                while section.tell() < section_size:
                    defn_size = read_int(section)
                    yield section.read(defn_size).decode("utf-8")
