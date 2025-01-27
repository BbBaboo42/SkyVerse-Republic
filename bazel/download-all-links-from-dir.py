#!/usr/bin/python3

import os
import re
from alive_progress import alive_it
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import tarfile
import argparse
from commonregex import CommonRegex

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='the path to the file')
    parser.add_argument('download-dir', help='the path of the dir to download to')
    args = parser.parse_args()

    files = []

    path = Path(args.path)
    download_dir = Path(args.download_dir)
    if not path.is_dir():
        download_from_file(path, download_dir)
        return

    for p in path.rglob("*.bzl"):
        files.append(p)

    os.makedirs(download_dir, exist_ok=True)

    for file in files:
        print('downloading from', file)
        download_from_file(file, download_dir)

    with tarfile.open(f'{dir}.tar.gz', "w:gz") as tar:
        tar.add(download_dir, arcname=download_dir)

def download_from_file(path, download_dir):
    with open(path, 'r') as f:
        lines = f.read()

    parsed_text = CommonRegex(lines)
    urls = parsed_text.links

    for url in alive_it(urls):
        file_path = f'{download_dir}/{urlparse(url).netloc}/{urlparse(url).path[1:]}'
        try:
            os.makedirs(Path(file_path).parent, exist_ok=True)
            urllib.request.urlretrieve(url, file_path)
        except:
            print(f'couldn\'t download {file_path}')

if __name__ == '__main__':
    main()