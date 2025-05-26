import time
from pathlib import Path

import requests

from smalltv.random_image import generate_image


class SmallTV:
    def upload_image(self, file_path: Path, server='http://192.168.1.153', directory='/image/'):
        url = f"{server}/doUpload"
        params = {'dir': directory}
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'image/jpeg')
            }
            headers = {
                'Origin': server,
                'Referer': f"{server}/image.html",
                'X-Requested-With': 'XMLHttpRequest',
            }
            try:
                resp = requests.post(url, params=params, files=files, headers=headers)
                resp.raise_for_status()
                print('Upload successful:', resp.text)
            except requests.exceptions.InvalidHeader as e:
                print('Warning: InvalidHeader skipped:', e)

    def clear(self, server='http://192.168.1.153', directory='image'):
        resp = requests.get(
            f"{server}/set",
            params={'clear': f"{directory}"}
        )
        resp.raise_for_status()

    def set_image(self, directory, output_path, server):
        try:
            resp = requests.get(
                f"{server}/set",
                params={'img': f"{directory}{output_path.name}"}
            )
            resp.raise_for_status()
            print('Set image successful:', resp.text)
        except Exception as e:
            print('Set image failed:', e)

def main():
    server = 'http://192.168.1.153'
    directory = '/image/'
    i = 0
    smalltv = SmallTV()
    while True:
        output_path = generate_image()
        if i % 10 == 0:
            smalltv.clear()
            i = 0
        smalltv.upload_image(output_path, server=server, directory=directory)
        smalltv.set_image(directory, output_path, server)
        time.sleep(1)
        i += 1


if __name__ == '__main__':
    main()
