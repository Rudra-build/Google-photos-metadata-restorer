# Google Takeout → iCloud Metadata Fix

When I downloaded my photos from Google Photos using Google Takeout and uploaded them to iCloud, all the dates were wrong.

iCloud was showing the upload date instead of the actual date the photo was taken.

After digging into it, I realised Google stores the real “date taken” inside separate `.json` files. iCloud does not read those files automatically.

So I wrote this small script to fix it.

It reads the metadata from the Takeout JSON files and writes it back into the actual photo or video file before uploading to iCloud.

That way Apple Photos shows the correct timeline.

---

## What this script does

It goes through your Google Takeout folder.

For every photo or video, it looks for the matching `.json` file.

From that JSON file, it extracts:

* The original date the photo was taken
* GPS location (if available)
* Album name (if available)

It then copies the file into a new folder and writes the correct metadata directly into the file using exiftool.

It does not modify your original Takeout folder.

It also avoids overwriting files if two have the same name.

It works for:

* JPG
* JPEG
* HEIC
* PNG
* MP4
* MOV
* M4V

Videos are handled properly so iCloud recognises the correct date.

---

## What you need

Python 3.9 or newer

exiftool installed on your system

On macOS you can install it with:

```
brew install exiftool
```

On Windows or Linux, download it from:
[https://exiftool.org](https://exiftool.org)

---

## How to use it

Step 1:
Download your Google Photos using Google Takeout.

Step 2:
Unzip the Takeout archive.

Step 3:
Run the script:

```
python3 process_google_photos.py
```

Step 4:
The script will ask you two things:

Enter the path to your Google Photos Takeout folder
Enter the destination folder where you want the fixed files saved

Example of a path on macOS:

```
/Users/yourname/Downloads/Takeout/Google Photos
```

After that, the script will process everything and create a new folder with the corrected files.

Upload that processed folder to iCloud instead of the original Takeout folder.

Your timeline should now be correct.

---

## Important

This script does not change your original files.

It creates a separate processed copy.

I recommend testing it on a small album first before running it on your full library.

---

## Why I made this

I was migrating my own photo library and didn’t want to lose years of chronological order.

This script is just a practical fix for that problem.
