#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


PHOTO_EXTS = {".jpg", ".jpeg", ".heic", ".png"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
ALL_EXTS = PHOTO_EXTS | VIDEO_EXTS


# make sure exiftool is installed
def check_exiftool():
    try:
        subprocess.run(["exiftool", "-ver"], check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except:
        print("❌ exiftool not found. Install it first.")
        exit(1)


# simple folder name clean up
def clean_name(name):
    if not name:
        return "Unknown Album"
    name = re.sub(r'[\\/:*?"<>|]', "-", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name.rstrip(". ")


# avoid overwriting files
def unique_path(path):
    if not path.exists():
        return path

    i = 1
    while True:
        new_path = path.with_stem(f"{path.stem} ({i})")
        if not new_path.exists():
            return new_path
        i += 1


# extract taken time from json
def get_taken_time(meta, tz_name, use_utc):
    ts = meta.get("photoTakenTime", {}).get("timestamp")
    if not ts:
        return None

    dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)

    if use_utc:
        return dt_utc.replace(tzinfo=None)

    try:
        local = dt_utc.astimezone(ZoneInfo(tz_name))
        return local.replace(tzinfo=None)
    except:
        return dt_utc.replace(tzinfo=None)


# extract gps if available
def get_gps(meta):
    geo = meta.get("geoData", {})
    lat = geo.get("latitude", 0)
    lon = geo.get("longitude", 0)

    if lat == 0 and lon == 0:
        return None, None

    return lat, lon


# write metadata using exiftool
def write_metadata(file_path, dt, lat, lon, is_video, dry):
    date_str = dt.strftime("%Y:%m:%d %H:%M:%S")

    cmd = ["exiftool", "-overwrite_original", "-q", "-q"]

    if is_video:
        # videos need these for iCloud
        cmd += [
            f"-CreateDate={date_str}",
            f"-MediaCreateDate={date_str}",
            f"-TrackCreateDate={date_str}",
            f"-ModifyDate={date_str}",
        ]
    else:
        cmd += [
            f"-DateTimeOriginal={date_str}",
            f"-CreateDate={date_str}",
            f"-ModifyDate={date_str}",
        ]

    if lat is not None and lon is not None:
        cmd += [
            f"-GPSLatitude={lat}",
            f"-GPSLongitude={lon}",
            f"-GPSLatitudeRef={'N' if lat >= 0 else 'S'}",
            f"-GPSLongitudeRef={'E' if lon >= 0 else 'W'}",
        ]

    cmd.append(str(file_path))

    if not dry:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # also set filesystem time
        epoch = int(dt.replace(tzinfo=timezone.utc).timestamp())
        os.utime(file_path, (epoch, epoch))


def main():
    print("Google Takeout → iCloud Date Fix")
    print("----------------------------------")

    source_input = input("Enter path to your Google Photos Takeout folder:\n> ").strip()
    dest_input = input("Enter destination folder for processed files:\n> ").strip()

    src = Path(source_input).expanduser()
    dest = Path(dest_input).expanduser()

    if not src.exists():
        print("❌ Source folder not found.")
        return

    check_exiftool()
    dest.mkdir(parents=True, exist_ok=True)

    print("\nProcessing...\n")

    for root, _, files in os.walk(src):
        for file in files:
            path = Path(root) / file

            if path.suffix.lower() not in ALL_EXTS:
                continue

            json_path = path.with_suffix(path.suffix + ".json")
            if not json_path.exists():
                continue

            try:
                with open(json_path, "r") as f:
                    meta = json.load(f)

                dt = get_taken_time(meta, "Europe/London", False)
                if not dt:
                    continue

                lat, lon = get_gps(meta)

                album = meta.get("albumTitles", [])
                if album:
                    folder = clean_name(album[0])
                else:
                    folder = clean_name(path.parent.name)

                dest_folder = dest / folder
                dest_folder.mkdir(parents=True, exist_ok=True)

                new_path = unique_path(dest_folder / path.name)

                shutil.copy2(path, new_path)

                write_metadata(
                    new_path,
                    dt,
                    lat,
                    lon,
                    path.suffix.lower() in VIDEO_EXTS,
                    False
                )

                print(f"✓ {path.name}")

            except Exception as e:
                print(f"✗ {path.name} ({e})")

    print("\nDone.")


if __name__ == "__main__":
    main()