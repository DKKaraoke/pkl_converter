offset = 0x0


class TrackHeader:
    global offset

    def __init__(self, init_offset=0x0):
        global offset
        offset = init_offset

    def parse_TrackHeader(self, fr):
        trackDataHeaderSize = int.from_bytes(fr.read(1), "big")
        if trackDataHeaderSize == 8:
            self.flags = int.from_bytes(fr.read(1), "big")
            self.time2CFO = int.from_bytes(fr.read(4), "big")
            self.nPaletteCnt = int.from_bytes(fr.read(1), "big")
            self.nAttributeCnt = int.from_bytes(fr.read(1), "big")
            self.paletteList = []
            for i in range(self.nPaletteCnt):
                self.paletteList.append(
                    {
                        "chRed": int.from_bytes(fr.read(1), "big"),
                        "chGreen": int.from_bytes(fr.read(1), "big"),
                        "chBlue": int.from_bytes(fr.read(1), "big"),
                        "chAlpha": int.from_bytes(fr.read(1), "big"),
                    }
                )
            self.pAttributeList = []
            for i in range(self.nAttributeCnt):
                self.pAttributeList.append(
                    {
                        "chBeforeWipeFont": int.from_bytes(fr.read(1), "big"),
                        "chBeforeWipeEdge": int.from_bytes(fr.read(1), "big"),
                        "chAfterWipeFont": int.from_bytes(fr.read(1), "big"),
                        "chAfterWipeEdge": int.from_bytes(fr.read(1), "big"),
                    }
                )
        else:
            raise RuntimeError(
                f"[sng] Bad Trackdata header size [{trackDataHeaderSize}]"
            )

    def encode_TrackHeader(self, trackheader_dict):
        self.binary = bytearray()
        try:
            if (
                "trackDataHeaderSize" in trackheader_dict
                and trackheader_dict["trackDataHeaderSize"] != 8
            ):
                raise RuntimeError(
                    f"Bad Trackdata header size [{trackheader_dict['trackDataHeaderSize']}]"
                )
            self.binary += int(0x8).to_bytes(1, "big")
            self.binary += trackheader_dict["flags"].to_bytes(1, "big")
            self.binary += trackheader_dict["time2CFO"].to_bytes(4, "big")
            if "nPaletteCnt" in trackheader_dict:
                self.binary += trackheader_dict["nPaletteCnt"].to_bytes(1, "big")
            else:
                self.binary += len(trackheader_dict["paletteList"]).to_bytes(1, "big")
            if "nAttributeCnt" in trackheader_dict:
                self.binary += trackheader_dict["nAttributeCnt"].to_bytes(1, "big")
            else:
                self.binary += len(trackheader_dict["pAttributeList"]).to_bytes(
                    1, "big"
                )
            for palette in trackheader_dict["paletteList"]:
                self.binary += palette["chRed"].to_bytes(1, "big")
                self.binary += palette["chGreen"].to_bytes(1, "big")
                self.binary += palette["chBlue"].to_bytes(1, "big")
                self.binary += palette["chAlpha"].to_bytes(1, "big")
            for attribute in trackheader_dict["pAttributeList"]:
                self.binary += attribute["chBeforeWipeFont"].to_bytes(1, "big")
                self.binary += attribute["chBeforeWipeEdge"].to_bytes(1, "big")
                self.binary += attribute["chAfterWipeFont"].to_bytes(1, "big")
                self.binary += attribute["chAfterWipeEdge"].to_bytes(1, "big")
        except KeyError as e:
            raise RuntimeError("Required key not found.", e)
