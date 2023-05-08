import sys
from logging import getLogger, Formatter, StreamHandler, DEBUG, WARNING
import argparse
import os
import json
import codecs
import binascii

global offset

class PklHeader:
    global offset
    def parse_PklHeader(self, fr):
        self.fileSize = hex(int.from_bytes(fr.read(4), 'big'))
        self.headersize = hex(int.from_bytes(fr.read(4), 'big'))
        self.ASVersion = hex(int.from_bytes(fr.read(4), 'big'))
        fr.seek(4, os.SEEK_CUR)
        fr.seek(4, os.SEEK_CUR)
        fr.seek(4, os.SEEK_CUR)
        self.posTrack = int.from_bytes(fr.read(4), 'big')
        self.ver = fr.read(8).decode()
        self.timeunit = hex(int.from_bytes(fr.read(1), 'big'))
        self.wipeunit = hex(int.from_bytes(fr.read(1), 'big'))
        fr.seek(6, os.SEEK_CUR)
        self.DKNo = str(int.from_bytes(fr.read(4), 'big'))
        self.ReqNo = str(int.from_bytes(fr.read(4), 'big'))
        # the code below is not implemented in dam
        fr.seek(8, os.SEEK_CUR)
        self.titleSize = int.from_bytes(fr.read(2), 'big')
        self.title = fr.read(self.titleSize).decode('Shift-JIS', 'backslashreplace')
        self.artistSize = int.from_bytes(fr.read(2), 'big')
        self.artist = fr.read(self.artistSize).decode('Shift-JIS', 'backslashreplace')
        self.lyricistSize = int.from_bytes(fr.read(2), 'big')
        self.lyricist = fr.read(self.lyricistSize).decode('Shift-JIS', 'backslashreplace')
        self.composerSize = int.from_bytes(fr.read(2), 'big')
        self.composer = fr.read(self.composerSize).decode('Shift-JIS', 'backslashreplace')

class TrackHeader:
    global offset
    def parse_TrackHeader(self, fr):
        trackDataHeaderSize = int.from_bytes(fr.read(1), 'big')
        if trackDataHeaderSize == 8:
            self.flags = hex(int.from_bytes(fr.read(1), 'big'))
            self.time2CFO = hex(int.from_bytes(fr.read(4), 'big'))
            self.nPaletteCnt = int.from_bytes(fr.read(1), 'big')
            self.nAttributeCnt = int.from_bytes(fr.read(1), 'big')
            self.paletteList = []
            for i in range(self.nPaletteCnt):
                self.paletteList.append(
                    {'chRed': int.from_bytes(fr.read(1), 'big'),
                    'chGreen': int.from_bytes(fr.read(1), 'big'),
                    'chBlue': int.from_bytes(fr.read(1), 'big'),
                    'chAlpha': int.from_bytes(fr.read(1), 'big')})
            self.pAttributeList = []
            for i in range(self.nAttributeCnt):
                self.pAttributeList.append(
                    {'chBeforeWipeFont': int.from_bytes(fr.read(1), 'big'),
                    'chBeforeWipeEdge': int.from_bytes(fr.read(1), 'big'),
                    'chAfterWipeFont': int.from_bytes(fr.read(1), 'big'),
                    'chAfterWipeEdge': int.from_bytes(fr.read(1), 'big')})
        else:
            raise RuntimeError(f"[sng] Bad Trackdata header size [{trackDataHeaderSize}]")

class TrackData:
    global offset
    def parse_TrackData(self, fr):
        print("[sng] stpdc_sngdatReadTrackData start")
        numofpage = 0
        topoftrackdata = fr.tell()
        while True:
            nextPageBlock = int.from_bytes(fr.read(4), 'big')
            numofpage += 1
            fr.seek(nextPageBlock + offset, os.SEEK_SET)
            if nextPageBlock == 0:
                break
        if numofpage == 0:
            raise RuntimeError("[sng] Invalid data.0 Page")
        self.pageCnt = numofpage
        self.pPageList = []
        for i in range(numofpage):
            self.pPageList.append({
                'lDispTime': 0,
                'lEraseTime': 0,
                'lineCnt': 0,
                'pLineList': [],
                'bScroll': 0,
                'pageNo': 0,
                'cHWFadeFlag': 0,
                'no': 0,
                'scroll': {'lBeforeScrollTime': 0, 'lScrollTime': 0, 'lAfterScrollTime': 0, 'lScrollDistance': 0}
            })
        for i in range(numofpage):
            self.pPageList[i]['scroll']['lScrollDistance'] = 0
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
    
    def parse_Page(self, fr, data_page, nextPos):
        linenum = 0
        lPageDispTime = 0x7fffffff
        lPageEraseTime = 0
        
        nextPos = int.from_bytes(fr.read(4), 'big')
        pageDataSize = int.from_bytes(fr.read(1), 'big')
        if pageDataSize == 8:
            fr.seek(3, os.SEEK_CUR)
            data_page['pageNo'] = hex(int.from_bytes(fr.read(2), 'big'))
            data_page['cHWFadeFlag'] = hex(int.from_bytes(fr.read(1), 'big'))
            self.parse_ScrollInfo(fr, data_page)
            topline = fr.tell()
            
            while True:
                tempUInt = int.from_bytes(fr.read(4), 'big')
                linenum += 1
                if tempUInt == 0:
                    data_page['lineCnt'] = linenum
                    for j in range(linenum):   
                        data_page['pLineList'].append({
                            'nCharCnt': 0,
                            'pCharList': [],
                            'pPicture': None,
                            'nDispType': 0,
                            'nTop': 0,
                            'nLineNum': 0,
                            'nLastAlpha': 0,
                            'nLastAlphaTmp': 0,
                            'nAlpha': 0,
                            'pParentPage': None,
                            'rubyFlag': 0,
                            'wipeFlag': 0,
                            'telopFlag': 0,
                            'mutegrp': 0,
                            'no': 0,
                            'id': 0,
                            'lineNumber': 0,
                            'lineTime': {'lDisplayTime': 0, 'lFadeInTime': 0, 'lEraseTime': 0, 'lFadeOutTime': 0, 'lDisplayTimeCalced': 0, 'lEraseTimeCalced': 0}
                        })
                    fr.seek(topline, os.SEEK_SET)
                    nextLine = 0
                    i = 0
                    while True:
                        if linenum <= i:
                            data_page['lDispTime'] = lPageDispTime
                            data_page['lEraseTime'] = lPageEraseTime
                            return nextPos
                        lPageDispTime, lPageEraseTime, nextLine = self.parse_Line(fr, data_page['pLineList'][i], lPageDispTime, lPageEraseTime, nextLine)
                        #data_page['pLineList'][i]['pParentPage'] = data_page
                        data_page['pLineList'][i]['nLineNum'] = i + 1
                        if nextLine != 0:
                            fr.seek(nextLine + offset, os.SEEK_SET)
                        i += 1
                fr.seek(tempUInt + offset, os.SEEK_SET)
        else:
            raise RuntimeError(f"[sng] wrong page data size [{pageDataSize}]")
                    
    def parse_ScrollInfo(self, fr, data_page):
        tempUChar = fr.read(1)
        data_page['bScroll'] = 1 if tempUChar != b'\0' else 0
        if tempUChar == b"\0" or tempUChar == b"\f":
            if data_page['bScroll'] == 0:
                return
            data_page['scroll']['lBeforeScrollTime'] = hex(int.from_bytes(fr.read(2), 'big'))
            data_page['scroll']['lScrollTime'] = hex(int.from_bytes(fr.read(4), 'big'))
            data_page['scroll']['lAfterScrollTime'] = hex(int.from_bytes(fr.read(2), 'big'))
            data_page['scroll']['lScrollDistance'] = hex(int.from_bytes(fr.read(2), 'big'))
            fr.seek(2, os.SEEK_CUR)
        else:
            raise RuntimeError(f"[sng] wrong scroll data size [{tempUChar}]")
        print("[sng] stpdc_sngdatReadScrollinfo end")

    def parse_Line(self, fr, data_line, lPageDispTime, lPageEraseTime, nextline):
        nTop = 0x7fffffff
        pos = 0
        buffer = fr.read(10)
        nextline = int.from_bytes(buffer[0:4], 'big') # pointer
        tempUChar = buffer[4:5]
        if tempUChar == b'\x14':
            data_line['lineNumber'] = hex(int.from_bytes(buffer[8:9], 'big'))
            tempUChar = buffer[9:10]
            lPageDispTime, lPageEraseTime = self.parse_LineDispTime(fr, data_line['lineTime'], lPageDispTime, lPageEraseTime)
            if tempUChar == b"\0":
                data_line['nDispType'] = 0
                data_line['nCharCnt'] = int.from_bytes(fr.read(1), 'big')
                tempUInt = hex(int.from_bytes(fr.read(3), 'big'))
                for i in range(data_line['nCharCnt']):
                    data_line['pCharList'].append({
                        'bWipe': 0,
                        'width': 0,
                        'height': 0,
                        'charData': {
                            'bitmapFontAddress': 0,
                            'chCharCode': "",
                            'fontID': 0,
                            'sCharAttribute': 0,
                            'chCharSize': 0,
                            'flags': 0,
                            'sCharPosX': 0,
                            'sCharPosY': 0,
                            'lWipeStartTime': 0,
                            'lWipeLastTime': 0,
                            'chWipeTime': []
                        }
                        })
                for i in range(data_line['nCharCnt']):
                    nTop = self.parse_Chara(fr, data_line['pCharList'][i], nTop)
                data_line['nTop'] = nTop
                data_line['nLastAlpha'] = -1
                data_line['nLastAlphaTmp'] = -1
            else:
                data_line['nDispType'] = 1
                data_line['pPicture'] = {'pictureData':
                    {
                        'chPictureType': 0,
                        'chTBD': [0, 0, 0],
                        'sTitlePosX': 0,
                        'sTitlePosY': 0,
                        'pictureDataSize': 0,
                        'pImageData': None,
                        'pExpandedData': None,
                        'w': 0,
                        'h': 0
                    }
                }
                self.parse_Image(fr, data_line)
            return lPageDispTime, lPageEraseTime, nextline
        else:
            raise RuntimeError(f"[sng] wrong line data size{tempUChar}")
        
    def parse_LineDispTime(self, fr, linetime, lPageDispTime, lPageEraseTime):
        linetime['lFadeInTime'] = hex(int.from_bytes(fr.read(2), 'big'))
        linetime['lFadeOutTime'] = hex(int.from_bytes(fr.read(2), 'big'))
        linetime['lDisplayTime'] = int.from_bytes(fr.read(4), 'big')
        if linetime['lDisplayTime'] < lPageDispTime:
            lPageDispTime = linetime['lDisplayTime'] # pointer
        linetime['lEraseTime'] = int.from_bytes(fr.read(4), 'big')
        if lPageEraseTime < linetime['lEraseTime']:
            lPageEraseTime = linetime['lEraseTime']
        int.from_bytes(fr.read(2), 'big')
        return lPageDispTime, lPageEraseTime
    
    def parse_Chara(self, fr, data_char, nTop):
        charSize = int.from_bytes(fr.read(2), 'big')
        if (charSize == 0x2c):
            charCode = fr.read(2)
            data_char['charData']['chCharCode'] = charCode.decode("EUC-JP", 'backslashreplace')
            data_char['charData']['bitmapFontAddress'] = hex(int.from_bytes(fr.read(4), 'big'))
            data_char['charData']['fontID'] = hex(int.from_bytes(fr.read(1), 'big'))
            data_char['charData']['sCharAttribute'] = hex(int.from_bytes(fr.read(1), 'big'))
            data_char['charData']['chCharSize'] = hex(int.from_bytes(fr.read(1), 'big'))
            data_char['charData']['flags'] = hex(int.from_bytes(fr.read(1), 'big'))
            data_char['charData']['sCharPosX'] = int.from_bytes(fr.read(2), 'big')
            if data_char['charData']['sCharPosX'] < 0:
                raise RuntimeError("[sng] Char.x < 0")
            data_char['charData']['sCharPosY'] = int.from_bytes(fr.read(2), 'big')
            if data_char['charData']['sCharPosY'] < 0:
                raise RuntimeError("[sng] Char.y < 0")
            if data_char['charData']['sCharPosY'] < nTop:
                nTop = data_char['charData']['sCharPosY']
            data_char['charData']['lWipeStartTime'] = hex(int.from_bytes(fr.read(4), 'big'))
            buf = fr.read(24)
            for i in range(24):
                data_char['charData']['chWipeTime'].append(int.from_bytes(buf[i:i+1], 'big'))
            # fontData = stpdc_fntcchGetFontData()
            # data_char['width'] = fontData['width']
            # data_char['height'] = fontData['height']
            return nTop
        else:
            raise RuntimeError(f"[sng] wrong character data header size [{charSize}]")

    def parse_Image(self, fr, data_line):
        picture = data_line['pPicture']
        tempUShort = int.from_bytes(fr.read(2), 'big')
        if tempUShort == 0xc:
            picture['pictureData']['chPictureType'] = hex(int.from_bytes(fr.read(1), 'big'))
            fr.seek(1, os.SEEK_CUR)
            picture['pictureData']['sTitlePosX'] = hex(int.from_bytes(fr.read(2), 'big'))
            picture['pictureData']['sTitlePosY'] = hex(int.from_bytes(fr.read(2), 'big'))
            picture['pictureData']['pictureDataSize'] = int.from_bytes(fr.read(4), 'big')
            if picture['pictureData']['pictureDataSize'] == 0:
                return
            picture['pictureData']['pImageData'] = "0x" + binascii.hexlify(fr.read(picture['pictureData']['pictureDataSize'])).decode()
        else:
            raise RuntimeError(f"[sng] Wrong Image data header size({tempUShort}).")

def main():
    global offset
    parser = argparse.ArgumentParser(description="Adds BGEV to RQIF file without BGEV.")
    parser.add_argument("input", help="Path to input file.")
    #parser.add_argument("output", help="Path to output file.")
    args = parser.parse_args()
    fr = open(args.input, 'rb')
    offset = 0
    if fr.read(4) == b'SPRC':
        offset = 0x10
    fr.seek(offset, os.SEEK_SET)
    header = PklHeader()
    header.parse_PklHeader(fr)
    fr.seek(header.posTrack + offset, os.SEEK_SET)
    track_header = TrackHeader()
    track_header.parse_TrackHeader(fr)
    track_data = TrackData()
    track_data.parse_TrackData(fr)
    returnList = {'PklHeader': vars(header), 'TrackHeader': vars(track_header), 'TrackData': vars(track_data)}
    fw = codecs.open(args.input + ".json", 'w', 'utf-8')
    json.dump(returnList, fw, indent=2, ensure_ascii=False)
    fw.close()


if __name__ == '__main__':
    main()