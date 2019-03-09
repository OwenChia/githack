# -*- coding: utf-8 -*-
from concurrent import futures
from pathlib import Path
from urllib import parse, request
import io
import logging
import sys
import re
import queue

try:
    from parse import parse_object, parse_index
except ModuleNotFoundError:
    from .parse import parse_object, parse_index

logging.basicConfig(level=logging.INFO)

RE_PATTERN_SHA1 = re.compile(rb'[0-9a-fA-F]{40}')
RE_PATTERN_TREE_OBJECT = re.compile(rb'(\d+) ([^\x00]+)\x00(.{20})', re.DOTALL)


class Scanner:
    def __init__(self, uri: str):
        self.log = logging.getLogger(__name__)
        self.workdir = Path('site')
        self.uri = self._check_uri(uri)
        self._queue = queue.Queue()

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
        if not uri.endswith('/'):
            uri += '/'
        self.log.info(f'Target: {uri}')
        return uri

    def _fetch(self, uri):
        req = request.Request(uri)
        res = request.urlopen(req)
        return res.read()

    def _save(self, filename, content):
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_bytes(content)

    def _prepare(self):
        '''HEAD
        ref: refs/heads/master
        '''
        workdir = self.workdir / '.git'

        for filename in ['index', 'config']:
            content = self._fetch(self.uri + filename)
            self._save(workdir / filename, content)

        head = self._fetch(self.uri + 'HEAD')
        self._save(workdir / 'HEAD', head)
        ref = head.split()[1].decode()
        seed = self._fetch(self.uri + ref)
        self._save(workdir / ref, seed)
        self._queue.put(seed.decode().strip())

    def _process(self, item):
        # self.log.info(f'Processing {item}')
        filepath = '/'.join(['objects', item[:2], item[2:]])
        objects = self._fetch(self.uri + filepath)
        self._save(self.workdir / '.git' / filepath, objects)

        filetype, content = parse_object(objects)
        if filetype == b'blob':
            self.log.info(f'Blob: {item}')
            return
        elif filetype == b'commit':
            self.log.info(f'commit: {item}')
            for it in RE_PATTERN_SHA1.finditer(content):
                self._queue.put(it.group().decode())
        elif filetype == b'tree':
            self.log.info(f'tree: {item}')
            for it in RE_PATTERN_TREE_OBJECT.finditer(content):
                self._queue.put(it.groups()[2].hex())

    def _get_index(self):
        uri = self.uri + '/index'
        content = self._fetch(uri)
        return io.BytesIO(content)

    def _get_object(self, name, sha1):
        uri = '/'.join([self.uri, 'objects', sha1[:2], sha1[2:]])
        content = self._fetch(uri)
        filetype, content = parse_object(content)
        filename = self.workdir / name
        self._save(filename, content)
        return sha1, filetype.decode()

    def crawl(self):
        self._prepare()
        with futures.ThreadPoolExecutor() as executor:
            item = self._queue.get()
            future = {executor.submit(self._process, item): item}
            while future:
                done, not_done = futures.wait(future, return_when=futures.FIRST_COMPLETED)
                while not self._queue.empty():
                    item = self._queue.get()
                    future[executor.submit(self._process, item)] = item
                for f in done:
                    it = future[f]
                    try:
                        f.result()
                    except Exception as ex:
                        self.log.error(f'\x1b[3m[ERROR] {it}: {repr(ex)}\x1b[0m')
                    del future[f]

    def restore(self):
        index_file = self._get_index()
        _parser = parse_index(index_file)
        total = next(_parser)
        self.log.info(f"Total: {total}")

        with futures.ThreadPoolExecutor() as executor:
            futures_to_restore = {executor.submit(self._get_object, e.name, e.sha1): e.name for e in _parser}

        for future in futures.as_completed(futures_to_restore):
            e = futures_to_restore[future]
            try:
                result = future.result()
            except Exception as exc:
                self.log.exception(f'\x1b[31;1m[ERROR]\x1b[0m {e} : {repr(exc)}')
            else:
                self.log.info(f'\x1b[32m[OK]\x1b[0m {e} : {result}')
