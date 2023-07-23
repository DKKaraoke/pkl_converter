import argparse
import os
import json
import codecs
from pkl_converter.pkl_header import PklHeader
from pkl_converter.track_data import TrackData
from pkl_converter.track_header import TrackHeader


def main():
    global offset
    parser = argparse.ArgumentParser(description="Adds BGEV to RQIF file without BGEV.")
    parser.add_argument("input", help="Path to input file.")
    parser.add_argument(
        "-p",
        "--parse",
        action="store_true",
        help="Parses a PKL file to JSON file (default)",
    )
    # parser.add_argument('-d', '--details', action='store_true', help="Parses with details in parse mode")
    parser.add_argument(
        "-e", "--encode", action="store_true", help="Encodes PKL file from a JSON file"
    )
    # parser.add_argument("output", help="Path to output file.")
    args = parser.parse_args()
    if args.encode == True:
        try:
            fr = open(args.input, "r", encoding="utf-8")
            json_dict = json.load(fr)
            header = PklHeader()
            header.encode_PklHeader(json_dict["PklHeader"])
            track_header = TrackHeader()
            track_header.encode_TrackHeader(json_dict["TrackHeader"])
            track_data = TrackData()
            track_data.encode_TrackData(
                json_dict["TrackData"], len(header.binary) + len(track_header.binary)
            )
            header.binary[0:4] = (
                len(header.binary) + len(track_header.binary) + len(track_data.binary)
            ).to_bytes(4, "big")
            fw = open(args.input + ".pkl", "wb")
            fw.write(header.binary + track_header.binary + track_data.binary)
            fw.close()
        except KeyError as e:
            raise RuntimeError("Required key not found.", e)
    else:
        fr = open(args.input, "rb")
        offset = 0
        if fr.read(4) == b"SPRC":
            offset = 0x10
        fr.seek(offset, os.SEEK_SET)
        header = PklHeader(offset)
        header.parse_PklHeader(fr)
        fr.seek(header.posTrack + offset, os.SEEK_SET)
        track_header = TrackHeader(offset)
        track_header.parse_TrackHeader(fr)
        track_data = TrackData(offset)
        track_data.parse_TrackData(fr)
        track_data.write_images(args.input)
        returnList = {
            "PklHeader": vars(header),
            "TrackHeader": vars(track_header),
            "TrackData": vars(track_data),
        }
        fw = codecs.open(args.input + ".json", "w", "utf-8")
        json.dump(returnList, fw, indent=2, ensure_ascii=False)
        fw.close()

if __name__ == "__main__":
    main()