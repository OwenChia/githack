from urllib import request
import sys


if len(sys.argv) != 2:
    print("output filename required!", file=sys.stderr)
    sys.exit(1)

FILENAME = sys.argv[1]

req = request.Request('https://raw.githubusercontent.com/sqlmapproject/sqlmap/master/data/txt/user-agents.txt')
with request.urlopen(req) as res, open(FILENAME, 'w') as fd:
    fd.write('user_agents = [\n')
    for line in res:
        if line.strip() == b'':
            continue
        if not line.startswith(b'#'):
            fd.write("    '{}',\n".format(line.decode().strip()))
    fd.write(']')
