# -*- coding: utf-8 -*-
from argparse import ArgumentParser
try:
    from scanner import Scanner
except ModuleNotFoundError:
    from .scanner import Scanner


def parse_args():
    parser = ArgumentParser(description='.git/ leakage exploit')
    parser.add_argument('URI', type=str, help="target uri to exploit eg. http://example.com/.git")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    scanner = Scanner(args.URI)
    scanner.crawl()
    scanner.restore()


if __name__ == '__main__':
    main()
