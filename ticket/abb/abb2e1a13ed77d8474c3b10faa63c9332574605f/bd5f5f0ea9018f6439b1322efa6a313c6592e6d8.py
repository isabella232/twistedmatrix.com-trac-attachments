from sys import argv

from twisted.python.filepath import FilePath

def skipSubversion(path):
    return path.basename() != '.svn'


def main(root):
    for path in root.walk(skipSubversion):
        if path.isdir():
            continue
        if path.basename().endswith('.pyc'):
            continue
        if path.basename().endswith('~'):
            continue
        content = path.getContent()
        lines = content.splitlines()
        for i in range(min(len(lines), 10)):
            if lines[i].startswith('# Copyright (c) 2') and 'Twisted Matrix Laboratories' in lines[i]:
                if lines[i + 1] == '# See LICENSE for details.':
                    lines[i] = '# Copyright (c) Twisted Matrix Laboratories.'
                    path.setContent('\n'.join(lines) + '\n')
                    break


if __name__ == '__main__':
    main(FilePath(argv[1]))
