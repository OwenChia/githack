# -*- coding: utf-8 -*-
import logging
import queue
import re
import sys
import threading
from concurrent import futures
from pathlib import Path
from urllib import parse, request

try:
    from parse import parse_object, parse_index
    from useragents import get_random_ua
except ModuleNotFoundError:
    from .parse import parse_object, parse_index
    from .useragents import get_random_ua

RE_PATTERN_SHA1 = re.compile(rb'[0-9a-fA-F]{40}')
RE_PATTERN_TREE_OBJECT = re.compile(rb'''(?P<mode>\d+)\x20
                                         (?P<filename>[^\x00]+)\x00
                                         (?P<hash>.{20})''',
                                    re.VERBOSE | re.DOTALL)
USER_AGENT = get_random_ua()


class Scanner:
    def __init__(self, uri: str, workdir: str):
        self.log = logging.getLogger(__name__)
        self.workdir = Path(workdir)
        self.uri = self._check_uri(uri)
        self.lock = threading.Lock()
        self._crawled = set()
        self._queue = queue.Queue()

    def _check_uri(self, uri):
        parsed = parse.urlparse(uri)
        if parsed.scheme not in ('http', 'https'):
            self.log.critical('Invalid URL format, try add http:// or https://')
            sys.exit(1)

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

    def _check_duplicate(self, item):
        with self.lock:
            if item in self._crawled:
                return True
            else:
                self._crawled.add(item)
                return False

    def _fetch(self, uri):
        headers = {
            'User-Agent': USER_AGENT
        }
        req = request.Request(uri, headers=headers)
        try:
            res = request.urlopen(req)
            return res.read()
        except Exception as ex:
            self.log.error(f'{ex}: {uri}')

    def _save(self, filename, content):
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True, exist_ok=True)
        if content is not None:
            filename.write_bytes(content)

    def _prepare(self):
        ''' download metadata, put seed to queue
        HEAD
        ====
        ref: refs/heads/master

        refs/heads/master
        ====
        <hashvalue>
        '''
        workdir = self.workdir / '.git'
        ref = 'refs/heads/master'

        head = self._fetch(self.uri + 'HEAD')
        if head is not None:
            self._save(workdir / 'HEAD', head)
            ref = head.split()[1].decode()

        DOWNLOAD = {'index', 'config', 'logs/refs/heads/master',
                    'logs/HEAD', f'logs/{ref}', 'logs/refs/stash'}
        for filename in DOWNLOAD:
            content = self._fetch(self.uri + filename)
            self._save(workdir / filename, content)

        SEED = {'ORIG_HEAD', 'refs/heads/master',
                'refs/stash', 'refs/remotes/origin/master',
                ref, ref.replace('heads', 'remotes/origin')}
        seeds = set()
        for filename in SEED:
            seed = self._fetch(self.uri + filename)
            if seed is None:
                continue
            self._save(workdir / filename, seed)
            seeds.add(seed.decode().strip())

        if len(seeds) == 0:
            self.log.critical('No seed found, please check your network setting.')
            sys.exit(1)

        for seed in seeds:
            self._queue.put(seed)

    def _process(self, item):
        self.log.debug(f'processing: {item}')
        if self._check_duplicate(item):
            return

        filepath = '/'.join(['objects', item[:2], item[2:]])
        objects = self._fetch(self.uri + filepath)
        if objects is None:
            return

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
            # RE_PATTERN_TREE_OBJECT (mode, filename, hash)
            for it in RE_PATTERN_TREE_OBJECT.finditer(content):
                self._queue.put(it['hash'].hex())

    def _restore_object(self, name, sha1, mode):
        objects = self.workdir / '.git' / 'objects' / sha1[:2] / sha1[2:]
        filetype, content = parse_object(objects.read_bytes())
        filename = self.workdir / name
        self._save(filename, content)

        # mode can only be 0o100755 or 0o100644
        filename.chmod(mode - 0o100000)
        return sha1, filetype.decode()

    def crawl(self):
        self._prepare()
        with futures.ThreadPoolExecutor() as executor:
            item = self._queue.get()
            future_to_crawl = {executor.submit(self._process, item): item}
            while future_to_crawl:
                done, not_done = futures.wait(future_to_crawl, return_when=futures.FIRST_COMPLETED)
                while not self._queue.empty():
                    item = self._queue.get()
                    future_to_crawl[executor.submit(self._process, item)] = item
                for future in done:
                    it = future_to_crawl[future]
                    try:
                        future.result()
                    except Exception as ex:
                        self.log.error(f'[ERROR] {it}: {repr(ex)}')
                    del future_to_crawl[future]

    def restore(self):
        index = self.workdir / '.git' / 'index'
        if not index.exists():
            self.log.error('index file not found, please use `git reset` to revocer it')
            return

        with open(index, 'rb') as fd:
            _parser = parse_index(fd)
            total = next(_parser)
            self.log.info(f"Total: {total}")

            with futures.ThreadPoolExecutor() as executor:
                futures_to_restore = {executor.submit(self._restore_object, e.name, e.sha1, e.mode): e.name
                                      for e in _parser}

        for future in futures.as_completed(futures_to_restore):
            e = futures_to_restore[future]
            try:
                result = future.result()
            except Exception as exc:
                self.log.error(f'[ERROR] {e}: {repr(exc)}')
            else:
                self.log.info(f'[OK] {e}: {result}')
