import binascii
import os

offset = 0x0


class TrackData:
    global offset

    def __init__(self, init_offset=0x0):
        global offset
        offset = init_offset

    def parse_TrackData(self, fr):
        print("[sng] stpdc_sngdatReadTrackData start")
        numofpage = 0
        topoftrackdata = fr.tell()
        while True:
            nextPageBlock = int.from_bytes(fr.read(4), "big")
            numofpage += 1
            fr.seek(nextPageBlock + offset, os.SEEK_SET)
            if nextPageBlock == 0:
                break
        if numofpage == 0:
            raise RuntimeError("[sng] Invalid data.0 Page")
        self.pageCnt = numofpage
        self.pPageList = []
        for i in range(numofpage):
            self.pPageList.append(
                {
                    "lDispTime": 0,
                    "lEraseTime": 0,
                    "lineCnt": 0,
                    "pLineList": [],
                    "bScroll": 0,
                    "pageNo": 0,
                    "cHWFadeFlag": 0,
                    "no": 0,
                    "scroll": {
                        "lBeforeScrollTime": 0,
                        "lScrollTime": 0,
                        "lAfterScrollTime": 0,
                        "lScrollDistance": 0,
                    },
                }
            )
        for i in range(numofpage):
            self.pPageList[i]["scroll"]["lScrollDistance"] = 0
        fr.seek(topoftrackdata, os.SEEK_SET)

        nextPage = 0
        i = 0
        while True:
            if numofpage <= i:
                print("[sng] stpdc_sngdatReadTrackData end")
                return
            nextPage = self.parse_Page(fr, self.pPageList[i], nextPage)
            if nextPage != 0:
                fr.seek(nextPage + offset, os.SEEK_SET)
            i += 1

    def encode_TrackData(self, track_dict, topoftrackdata):
        self.binary = bytearray()
        for i in range(len(track_dict["pPageList"])):
            self.encode_Page(
                track_dict["pPageList"][i],
                i + 1,
                len(track_dict["pPageList"]),
                topoftrackdata,
            )

    def parse_Page(self, fr, data_page, nextPos):
        linenum = 0
        lPageDispTime = 0x7FFFFFFF
        lPageEraseTime = 0

        nextPos = int.from_bytes(fr.read(4), "big")
        pageDataSize = int.from_bytes(fr.read(1), "big")
        if pageDataSize == 8:
            fr.seek(3, os.SEEK_CUR)
            data_page["pageNo"] = int.from_bytes(fr.read(2), "big")
            data_page["cHWFadeFlag"] = int.from_bytes(fr.read(1), "big")
            self.parse_ScrollInfo(fr, data_page)
            topline = fr.tell()

            while True:
                tempUInt = int.from_bytes(fr.read(4), "big")
                linenum += 1
                if tempUInt == 0:
                    data_page["lineCnt"] = linenum
                    for j in range(linenum):
                        data_page["pLineList"].append(
                            {
                                "nCharCnt": 0,
                                "pCharList": [],
                                "pPicture": None,
                                "nDispType": 0,
                                "nTop": 0,
                                "nLineNum": 0,
                                "nLastAlpha": 0,
                                "nLastAlphaTmp": 0,
                                "nAlpha": 0,
                                "pParentPage": None,
                                "rubyFlag": 0,
                                "wipeFlag": 0,
                                "telopFlag": 0,
                                "mutegrp": 0,
                                "no": 0,
                                "id": 0,
                                "lineNumber": 0,
                                "lineTime": {
                                    "lDisplayTime": 0,
                                    "lFadeInTime": 0,
                                    "lEraseTime": 0,
                                    "lFadeOutTime": 0,
                                    "lDisplayTimeCalced": 0,
                                    "lEraseTimeCalced": 0,
                                },
                            }
                        )
                    fr.seek(topline, os.SEEK_SET)
                    nextLine = 0
                    i = 0
                    while True:
                        if linenum <= i:
                            data_page["lDispTime"] = lPageDispTime
                            data_page["lEraseTime"] = lPageEraseTime
                            return nextPos
                        lPageDispTime, lPageEraseTime, nextLine = self.parse_Line(
                            fr,
                            data_page["pLineList"][i],
                            lPageDispTime,
                            lPageEraseTime,
                            nextLine,
                        )
                        # data_page['pLineList'][i]['pParentPage'] = data_page
                        data_page["pLineList"][i]["nLineNum"] = i + 1
                        if nextLine != 0:
                            fr.seek(nextLine + offset, os.SEEK_SET)
                        i += 1
                fr.seek(tempUInt + offset, os.SEEK_SET)
        else:
            raise RuntimeError(f"[sng] wrong page data size [{pageDataSize}]")

    def encode_Page(self, page_dict, pageNo, page_len, topoftrackdata):
        try:
            nextPos_pos = len(self.binary)
            self.binary += int(0).to_bytes(4, "big")  # define nextPos later
            if "pageDataSize" in page_dict and page_dict["pageDataSize"] != 8:
                raise RuntimeError(
                    f"wrong page data size [{page_dict['pageDataSize']}]"
                )
            self.binary += int(0x8).to_bytes(1, "big")  # pageDataSize
            self.binary += b"\0\0\0"
            if "pageNo" in page_dict:
                self.binary += page_dict["pageNo"].to_bytes(2, "big")
            else:
                self.binary += pageNo.to_bytes(2, "big")
            self.binary += page_dict["cHWFadeFlag"].to_bytes(1, "big")
            self.encode_ScrollInfo(page_dict)

            for i in range(len(page_dict["pLineList"])):
                self.encode_Line(
                    page_dict["pLineList"][i],
                    i + 1,
                    len(page_dict["pLineList"]),
                    topoftrackdata,
                )
            self.binary[nextPos_pos : nextPos_pos + 4] = (
                (len(self.binary) + topoftrackdata).to_bytes(4, "big")
                if page_len > pageNo
                else b"\0\0\0\0"
            )
        except KeyError as e:
            raise RuntimeError("Required key not found.", e)

    def parse_ScrollInfo(self, fr, data_page):
        tempUChar = fr.read(1)
        data_page["bScroll"] = 1 if tempUChar != b"\0" else 0
        if tempUChar == b"\0" or tempUChar == b"\f":
            if data_page["bScroll"] == 0:
                return
            data_page["scroll"]["lBeforeScrollTime"] = int.from_bytes(fr.read(2), "big")
            data_page["scroll"]["lScrollTime"] = int.from_bytes(fr.read(4), "big")
            data_page["scroll"]["lAfterScrollTime"] = int.from_bytes(fr.read(2), "big")
            data_page["scroll"]["lScrollDistance"] = int.from_bytes(fr.read(2), "big")
            fr.seek(2, os.SEEK_CUR)
        else:
            raise RuntimeError(f"[sng] wrong scroll data size [{tempUChar}]")
        print("[sng] stpdc_sngdatReadScrollinfo end")

    def encode_ScrollInfo(self, page_dict):
        # tempUChar
        if page_dict["bScroll"] == 1:
            self.binary += int(0xF).to_bytes(1, "big")
        elif page_dict["bScroll"] == 0:
            self.binary += int(0).to_bytes(1, "big")
            return
        else:
            raise RuntimeError(f"wrong scroll data")
        self.binary += page_dict["scroll"]["lBeforeScrollTime"].to_bytes(2, "big")
        self.binary += page_dict["scroll"]["lScrollTime"].to_bytes(4, "big")
        self.binary += page_dict["scroll"]["lAfterScrollTime"].to_bytes(2, "big")
        self.binary += page_dict["scroll"]["lScrollDistance"].to_bytes(2, "big")
        self.binary += b"\0\0"

    def parse_Line(self, fr, data_line, lPageDispTime, lPageEraseTime, nextline):
        nTop = 0x7FFFFFFF
        pos = 0
        buffer = fr.read(10)
        nextline = int.from_bytes(buffer[0:4], "big")  # pointer
        tempUChar = buffer[4:5]
        if tempUChar == b"\x14":
            data_line["lineNumber"] = int.from_bytes(buffer[8:9], "big")
            tempUChar = buffer[9:10]
            lPageDispTime, lPageEraseTime = self.parse_LineDispTime(
                fr, data_line["lineTime"], lPageDispTime, lPageEraseTime
            )
            if tempUChar == b"\0":
                data_line["nDispType"] = 0
                data_line["nCharCnt"] = int.from_bytes(fr.read(1), "big")
                tempUInt = int.from_bytes(fr.read(3), "big")
                for i in range(data_line["nCharCnt"]):
                    data_line["pCharList"].append(
                        {
                            "bWipe": 0,
                            "width": 0,
                            "height": 0,
                            "charData": {
                                "bitmapFontAddress": 0,
                                "chCharCode": "",
                                "fontID": 0,
                                "sCharAttribute": 0,
                                "chCharSize": 0,
                                "flags": 0,
                                "sCharPosX": 0,
                                "sCharPosY": 0,
                                "lWipeStartTime": 0,
                                "lWipeLastTime": 0,
                                "chWipeTime": [],
                            },
                        }
                    )
                for i in range(data_line["nCharCnt"]):
                    nTop = self.parse_Chara(fr, data_line["pCharList"][i], nTop)
                data_line["nTop"] = nTop
                data_line["nLastAlpha"] = -1
                data_line["nLastAlphaTmp"] = -1
            else:
                data_line["nDispType"] = 1
                data_line["pPicture"] = {
                    "pictureData": {
                        "chPictureType": 0,
                        "chTBD": [0, 0, 0],
                        "sTitlePosX": 0,
                        "sTitlePosY": 0,
                        "pictureDataSize": 0,
                        "pImageData": None,
                        "pExpandedData": None,
                        "w": 0,
                        "h": 0,
                    }
                }
                self.parse_Image(fr, data_line)
            return lPageDispTime, lPageEraseTime, nextline
        else:
            raise RuntimeError(f"[sng] wrong line data size{tempUChar}")

    def encode_Line(self, line_dict, lineNumber, line_len, topoftrackdata):
        nextLine_pos = len(self.binary)
        self.binary += int(0).to_bytes(4, "big")  # define nextLine later
        self.binary += b"\x14"  # tempUChar
        self.binary += b"\0\0\0"
        if "lineNumber" in line_dict:
            self.binary += line_dict["lineNumber"].to_bytes(1, "big")
        else:
            self.binary += int(lineNumber).to_bytes(1, "big")

        if line_dict["nDispType"] == 0:
            self.binary += int(0x0).to_bytes(1, "big")  # tempUChar
            self.encode_LineDispTime(line_dict["lineTime"])
            if "nCharCnt" in line_dict:
                self.binary += line_dict["nCharCnt"].to_bytes(1, "big")
            else:
                self.binary += len(line_dict["pCharList"]).to_bytes(1, "big")
            self.binary += b"\0\0\0"  # tempUInt
            for char_dict in line_dict["pCharList"]:
                self.encode_Chara(char_dict)
        elif line_dict["nDispType"] == 1:
            self.binary += int(0x1).to_bytes(1, "big")  # tempUChar
            self.encode_LineDispTime(line_dict["lineTime"])
            self.encode_Image(line_dict)
        self.binary[nextLine_pos : nextLine_pos + 4] = (
            (len(self.binary) + topoftrackdata).to_bytes(4, "big")
            if line_len > lineNumber
            else b"\0\0\0\0"
        )  # nextLine

    def parse_LineDispTime(self, fr, linetime, lPageDispTime, lPageEraseTime):
        linetime["lFadeInTime"] = int.from_bytes(fr.read(2), "big")
        linetime["lFadeOutTime"] = int.from_bytes(fr.read(2), "big")
        linetime["lDisplayTime"] = int.from_bytes(fr.read(4), "big")
        if linetime["lDisplayTime"] < lPageDispTime:
            lPageDispTime = linetime["lDisplayTime"]  # pointer
        linetime["lEraseTime"] = int.from_bytes(fr.read(4), "big")
        if lPageEraseTime < linetime["lEraseTime"]:
            lPageEraseTime = linetime["lEraseTime"]
        int.from_bytes(fr.read(2), "big")
        return lPageDispTime, lPageEraseTime

    def encode_LineDispTime(self, linetime_dict):
        self.binary += linetime_dict["lFadeInTime"].to_bytes(2, "big")
        self.binary += linetime_dict["lFadeOutTime"].to_bytes(2, "big")
        self.binary += linetime_dict["lDisplayTime"].to_bytes(4, "big")
        self.binary += linetime_dict["lEraseTime"].to_bytes(4, "big")
        self.binary += b"\0\0"

    def parse_Chara(self, fr, data_char, nTop):
        charSize = int.from_bytes(fr.read(2), "big")
        if charSize == 0x2C:
            charCode = fr.read(2)
            data_char["charData"]["chCharCode"] = charCode.decode(
                "EUC-JP", "backslashreplace"
            )
            data_char["charData"]["bitmapFontAddress"] = int.from_bytes(
                fr.read(4), "big"
            )
            data_char["charData"]["fontID"] = int.from_bytes(fr.read(1), "big")
            data_char["charData"]["sCharAttribute"] = int.from_bytes(fr.read(1), "big")
            data_char["charData"]["chCharSize"] = int.from_bytes(fr.read(1), "big")
            data_char["charData"]["flags"] = int.from_bytes(fr.read(1), "big")
            data_char["charData"]["sCharPosX"] = int.from_bytes(fr.read(2), "big")
            if data_char["charData"]["sCharPosX"] < 0:
                raise RuntimeError("[sng] Char.x < 0")
            data_char["charData"]["sCharPosY"] = int.from_bytes(fr.read(2), "big")
            if data_char["charData"]["sCharPosY"] < 0:
                raise RuntimeError("[sng] Char.y < 0")
            if data_char["charData"]["sCharPosY"] < nTop:
                nTop = data_char["charData"]["sCharPosY"]
            data_char["charData"]["lWipeStartTime"] = int.from_bytes(fr.read(4), "big")
            buf = fr.read(24)
            for i in range(24):
                data_char["charData"]["chWipeTime"].append(
                    int.from_bytes(buf[i : i + 1], "big")
                )
            # fontData = stpdc_fntcchGetFontData()
            # data_char['width'] = fontData['width']
            # data_char['height'] = fontData['height']
            return nTop
        else:
            raise RuntimeError(f"[sng] wrong character data header size [{charSize}]")

    def encode_Chara(self, char_dict):
        self.binary += int(0x2C).to_bytes(2, "big")  # charSize
        original_charCode = char_dict["charData"]["chCharCode"].encode(
            "EUC-JP", "backslashreplace"
        )
        charCode = bytearray(2)
        charCode_offset = 0
        for i in range(2):
            if (
                original_charCode[i : i + 1] == b"\\"
                and len(original_charCode) > i + 3
                and original_charCode[i + 1 : i + 2] == b"x"
            ):
                charCode[i : i + 1] = int(
                    "0"
                    + original_charCode[
                        i + charCode_offset + 1 : i + charCode_offset + 4
                    ].decode("utf-8"),
                    16,
                ).to_bytes(
                    1, "big"
                )  # escaped characters like \x91
                charCode_offset += 3
            else:
                charCode[i : i + 1] = original_charCode[
                    i + charCode_offset : i + charCode_offset + 1
                ]
        self.binary += charCode[0:2] if len(charCode) > 1 else b"\0" + charCode
        self.binary += char_dict["charData"]["bitmapFontAddress"].to_bytes(4, "big")
        self.binary += char_dict["charData"]["fontID"].to_bytes(1, "big")
        self.binary += char_dict["charData"]["sCharAttribute"].to_bytes(1, "big")
        self.binary += char_dict["charData"]["chCharSize"].to_bytes(1, "big")
        self.binary += char_dict["charData"]["flags"].to_bytes(1, "big")
        self.binary += char_dict["charData"]["sCharPosX"].to_bytes(2, "big")
        self.binary += char_dict["charData"]["sCharPosY"].to_bytes(2, "big")
        self.binary += char_dict["charData"]["lWipeStartTime"].to_bytes(4, "big")
        for chWipeTime in char_dict["charData"]["chWipeTime"]:
            self.binary += chWipeTime.to_bytes(1, "big")

    def parse_Image(self, fr, data_line):
        picture = data_line["pPicture"]
        tempUShort = int.from_bytes(fr.read(2), "big")
        if tempUShort == 0xC:
            picture["pictureData"]["chPictureType"] = int.from_bytes(fr.read(1), "big")
            fr.seek(1, os.SEEK_CUR)
            picture["pictureData"]["sTitlePosX"] = int.from_bytes(fr.read(2), "big")
            picture["pictureData"]["sTitlePosY"] = int.from_bytes(fr.read(2), "big")
            picture["pictureData"]["pictureDataSize"] = int.from_bytes(
                fr.read(4), "big"
            )
            if picture["pictureData"]["pictureDataSize"] == 0:
                return
            picture["pictureData"]["pImageData"] = (
                "0x"
                + binascii.hexlify(
                    fr.read(picture["pictureData"]["pictureDataSize"])
                ).decode()
            )
        else:
            raise RuntimeError(f"[sng] Wrong Image data header size({tempUShort}).")

    def encode_Image(self, line_dict):
        picture = line_dict["pPicture"]
        self.binary += int(0xC).to_bytes(2, "big")
        self.binary += picture["pictureData"]["chPictureType"].to_bytes(1, "big")
        self.binary += b"\0"
        self.binary += picture["pictureData"]["sTitlePosX"].to_bytes(2, "big")
        self.binary += picture["pictureData"]["sTitlePosY"].to_bytes(2, "big")
        image_data = binascii.unhexlify(picture["pictureData"]["pImageData"][2:])
        if "pictureDataSize" in picture["pictureData"] and False:
            self.binary += picture["pictureData"]["pictureDataSize"].to_bytes(4, "big")
        else:
            self.binary += int(len(image_data)).to_bytes(4, "big")
        self.binary += image_data
