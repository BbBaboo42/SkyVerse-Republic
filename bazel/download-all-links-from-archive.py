#!/usr/bin/python3

from datetime import datetime
import os
from typing import List
from alive_progress import alive_it
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import tarfile
import argparse
from commonregex import CommonRegex

DOWNLOADS_DIR = Path('downloads')
TARS_DIR = Path('tars')


def download_links(links: List[str], download_dir: Path) -> None:
    for url in alive_it(links):
        file_path = f'{download_dir}/{urlparse(url).netloc}/{urlparse(url).path[1:]}'
        try:
            os.makedirs(Path(file_path).parent, exist_ok=True)
            urllib.request.urlretrieve(url, file_path)
        except Exception as e:
            print(f'couldn\'t download {file_path}: {e}')


def get_links_from_text(text: str) -> List[str]:
    parsed_text = CommonRegex(text)
    parsed_links = parsed_text.links

    if not isinstance(parsed_links, list):
        print(f'Error in parsing links!\n{parsed_links}')
        return []

    return [url for url in parsed_links if (url.startswith('http://') or url.startswith('https://'))]


def get_links_from_tar(file: Path) -> List[str]:
    links = []

    print(f'Collecting links from {file}')

    with tarfile.open(file, 'r:gz') as tar:
        for member in tar.getmembers():
            if not (member.isfile() and member.name.endswith('.bzl')):
                continue

            file_content = tar.extractfile(member)

            if not file_content:
                print(f'File seems to be empty: {member.name}')
                continue

            if member.size > 20000:
                print(f'File is too large: {member.name}')
                continue
        
            try:
                text = file_content.read().decode('utf-8')
            except:
                print(f'Failed reading from file: {member.name}')
                continue

            links.extend(get_links_from_text(text))

            links[:] = list(set(links))

    if len(links) > 100:
        print(f'{file.name}: Found more than 100 links ({len(links)}), skipping...')
        return []
    
    print(f'Found {len(links)} links')

    return links


def tar_all(path: Path) -> None:
    print(f'Creating tar.gz archive with downloads: {path}')

    os.makedirs(TARS_DIR, exist_ok=True)
    with tarfile.open(Path(TARS_DIR, f'{path.name}.tar.gz'), "w:gz") as tar:
        tar.add(path, arcname=path.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', help='the path to an archive or a directory with archives', type=Path)
    args = parser.parse_args()

    downloads_dir = Path(
        DOWNLOADS_DIR, f'deps-{datetime.now().strftime("%Y%m%d%H")}')
    os.makedirs(downloads_dir, exist_ok=True)

    if not args.path.is_dir():
        if not args.path.name.endswith('.tar.gz'):
            raise TypeError('Only directories or .tar.gz files are supported')

        links = get_links_from_tar(args.path)

        print(f'Downloading links from {args.path}')
        download_links(links, downloads_dir)
        return

    links = []

    print(f'Collecting links from all archives in {args.path}:')
    for file in alive_it(args.path.rglob('*.tar.gz')):
        links.extend(get_links_from_tar(file))

    print(f'Downloading found links:')
    download_links(set(links), downloads_dir)

    tar_all(downloads_dir)


if __name__ == '__main__':
    main()
