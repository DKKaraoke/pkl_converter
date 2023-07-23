import os

offset = 0x0


class PklHeader:
    global offset

    def __init__(self, init_offset=0x0):
        global offset
        offset = init_offset

    def parse_PklHeader(self, fr):
        self.fileSize = int.from_bytes(fr.read(4), "big")
        self.headersize = int.from_bytes(fr.read(4), "big")
        self.ASVersion = int.from_bytes(fr.read(4), "big")
        fr.seek(4, os.SEEK_CUR)
        fr.seek(4, os.SEEK_CUR)
        fr.seek(4, os.SEEK_CUR)
        self.posTrack = int.from_bytes(fr.read(4), "big")
        self.ver = fr.read(8).decode()
        self.timeunit = int.from_bytes(fr.read(1), "big")
        self.wipeunit = int.from_bytes(fr.read(1), "big")
        fr.seek(6, os.SEEK_CUR)
        self.DKNo = str(int.from_bytes(fr.read(4), "big"))
        self.ReqNo = str(int.from_bytes(fr.read(4), "big"))
        # the code below is not implemented in dam
        fr.seek(8, os.SEEK_CUR)
        self.titleSize = int.from_bytes(fr.read(2), "big")
        self.title = fr.read(self.titleSize).decode("Shift-JIS", "backslashreplace")
        self.artistSize = int.from_bytes(fr.read(2), "big")
        self.artist = fr.read(self.artistSize).decode("Shift-JIS", "backslashreplace")
        self.lyricistSize = int.from_bytes(fr.read(2), "big")
        self.lyricist = fr.read(self.lyricistSize).decode(
            "Shift-JIS", "backslashreplace"
        )
        self.composerSize = int.from_bytes(fr.read(2), "big")
        self.composer = fr.read(self.composerSize).decode(
            "Shift-JIS", "backslashreplace"
        )

    def encode_PklHeader(self, header_dict):
        self.binary = bytearray()
        try:
            self.binary += int(0).to_bytes(4, "big")  # define fileSize on final
            headerSize_pos = len(self.binary)
            self.binary += int(0).to_bytes(4, "big")  # define headersize later
            self.binary += header_dict["ASVersion"].to_bytes(4, "big")
            self.binary += b"\0\0\0\0"
            self.binary += b"\0\0\0\0"
            self.binary += b"\0\0\0\0"
            posTrack_pos = len(self.binary)
            self.binary += int(0).to_bytes(4, "big")  # define posTrack later
            if "ver" in header_dict and header_dict["ver"] != "PKLVER10":
                raise RuntimeError("Unsupported PKL Version: " + header_dict["ver"])
            self.binary += b"PKLVER10"
            if "timeunit" in header_dict:
                self.binary += header_dict["timeunit"].to_bytes(1, "big")
            else:
                self.binary += int(0).to_bytes(1, "big")
            if "wipeunit" in header_dict:
                self.binary += header_dict["wipeunit"].to_bytes(1, "big")
            else:
                self.binary += int(0).to_bytes(1, "big")
            self.binary += b"\0\0\0\0\0\0"
            if "headersize" in header_dict:
                self.binary[headerSize_pos : headerSize_pos + 4] = header_dict[
                    "headersize"
                ].to_bytes(4, "big")
            else:
                self.binary[headerSize_pos : headerSize_pos + 4] = len(
                    self.binary
                ).to_bytes(4, "big")
            self.binary += int(header_dict["DKNo"]).to_bytes(4, "big")
            self.binary += int(header_dict["ReqNo"]).to_bytes(4, "big")
            self.binary += b"\0\0\0\0\0\0\0\0"
            self.title = header_dict["title"].encode("Shift-JIS")
            self.binary += len(self.title).to_bytes(2, "big")
            self.binary += self.title
            self.artist = header_dict["artist"].encode("Shift-JIS")
            self.binary += len(self.artist).to_bytes(2, "big")
            self.binary += self.artist
            self.lyricist = header_dict["lyricist"].encode("Shift-JIS")
            self.binary += len(self.lyricist).to_bytes(2, "big")
            self.binary += self.lyricist
            self.composer = header_dict["composer"].encode("Shift-JIS")
            self.binary += len(self.composer).to_bytes(2, "big")
            self.binary += self.composer
            self.binary += b"\0\0"
            if "posTrack" in header_dict:
                self.binary[posTrack_pos : posTrack_pos + 4] = header_dict[
                    "posTrack"
                ].to_bytes(4, "big")
            else:
                self.binary[posTrack_pos : posTrack_pos + 4] = int(
                    len(self.binary)
                ).to_bytes(4, "big")
        except KeyError as e:
            raise RuntimeError("Required key not found.", e)
