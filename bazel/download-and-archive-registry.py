#!/usr/bin/python3

import os
import shutil
import subprocess
from alive_progress import alive_it
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import tarfile
from git import Repo
from datetime import datetime

DOWNLOADS_DIR = Path('downloads')
TARS_DIR = Path('tars')


def setup_registry():
    if not Path('bazel-central-registry').exists():
        print('Cloning bazel-central-registry...')
        Repo.clone_from(
            'https://github.com/bazelbuild/bazel-central-registry.git',
            'bazel-central-registry'
        )
        return

    print('Pulling latest commits from bazel-central-registry\'s main...')
    repo = Repo('bazel-central-registry')
    repo.git.checkout('main')
    repo.remotes.origin.pull()


def get_module_urls() -> list:
    print('Collecting src URLs from registry...')
    bazel_module_urls = subprocess.run(
        ['bazel', 'run', '//tools:print_all_src_urls'],
        capture_output=True,
        cwd='bazel-central-registry'
    )

    return bazel_module_urls.stdout.decode('utf-8').splitlines()


def download_urls(path: Path, urls: list) -> list:
    downloaded_urls = []
    download_path = Path(path, 'downloads')

    print(f'Downloading files to {download_path}:')
    for module_url in alive_it(urls):
        module_path = Path(
            download_path, f'{urlparse(module_url).netloc}/{urlparse(module_url).path[1:]}')
        os.makedirs(module_path.parent, exist_ok=True)
        # try:
        urllib.request.urlretrieve(module_url, module_path)
        downloaded_urls.append(module_url)
        # except:
        #     print(f'couldn\'t download {module_url}')

    return downloaded_urls


def tar_all(path: Path) -> None:
    tar_path = Path(TARS_DIR, f'{path.name}.tar.gz')

    print(f'Creating tar.gz archive with downloads: {tar_path}')

    if not Path(path, 'bazel-central-registry').exists():
        shutil.copytree('bazel-central-registry',
                        Path(path, 'bazel-central-registry'))

    os.makedirs(TARS_DIR, exist_ok=True)
    with tarfile.open(tar_path, 'w:gz') as tar:
        tar.add(path, arcname=path.name)


def update_downloaded(path: Path, downloaded_urls: list) -> None:
    print('Logging downloaded file URLs to prevent redownloads')

    with open(Path(path, 'downloaded_urls.txt'), 'a+') as f:
        f.write('\n'.join(downloaded_urls) + '\n')


def subtract_downloaded(module_urls: list) -> list:
    downloaded_urls = []
    for file in DOWNLOADS_DIR.rglob('downloaded_urls.txt'):
        with open(file) as f:
            downloaded_urls.extend(f.read().splitlines())

    return list(set(module_urls) - set(downloaded_urls))


def main() -> None:
    setup_registry()

    module_urls = get_module_urls()
    module_urls = subtract_downloaded(module_urls)

    if not module_urls:
        print('No new downloads were found. Exiting...')
        return

    download_dir = Path(DOWNLOADS_DIR, datetime.now().strftime('%Y%m%d%H'))
    os.makedirs(download_dir, exist_ok=True)

    downloaded_urls = download_urls(download_dir, module_urls)
    update_downloaded(download_dir, downloaded_urls)

    tar_all(download_dir)


if __name__ == '__main__':
    main()
