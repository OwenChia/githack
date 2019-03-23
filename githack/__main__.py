# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import logging

try:
    from scanner import Scanner
except ModuleNotFoundError:
    from .scanner import Scanner


def parse_args():
    parser = ArgumentParser(
        description='.git/ leakage exploit',
        epilog='OwenChia <https://github.com/OwenChia/githack>')
    parser.add_argument('URI', type=str, help="target uri to exploit (eg. http://example.com/.git)")
    parser.add_argument('-o', '--output', default='site', type=str,
                        help="output dir, all the file will download to this directory")
    parser.add_argument('--level', type=str,
                        choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help="log level (default: INFO)")
    parser.add_argument('-k', '--insecure', action='store_true',
                        help='Ignore ssl verify')

    args = parser.parse_args()

    _level = getattr(logging, args.level)
    logging.basicConfig(level=_level)

    if args.insecure:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context

    return args


def main():
    args = parse_args()
    scanner = Scanner(args.URI, args.output)
    scanner.crawl()
    scanner.restore()


if __name__ == '__main__':
    main()
