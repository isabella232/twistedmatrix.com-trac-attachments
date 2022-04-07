#!/usr/bin/env python3

from pathlib import Path
import re
import sys

from sphinx.ext.intersphinx import fetch_inventory


docs_dir = Path('docs')
apidocs_dir = Path('apidocs')


def load_inventory(filename: str) -> None:
    # This is a modified version of sphinx.ext.intersphinx.inspect_main().

    class MockConfig:
        intersphinx_timeout = None  # type: int
        tls_verify = False
        user_agent = None

    class MockApp:
        srcdir = ''
        config = MockConfig()

        def warn(self, msg: str) -> None:
            print(msg, file=sys.stderr)

    try:
        return fetch_inventory(MockApp(), '', filename)  # type: ignore
    except ValueError as exc:
        print(exc.args[0] % exc.args[1:])
    except Exception as exc:
        print('Unknown error: %r' % exc)
    sys.exit(1)

re_apilink = re.compile(r':api:`([^ <`]*)(?: <([^>`]*)>)?`')

def find_name(invdata, name):
    for category, names in invdata.items():
        if name in names:
            return category
    raise KeyError(name)

def convert(line, invdata):
    while True:
        match = re_apilink.search(line)
        if not match:
            break
        target, label = match.groups()
        if label is None:
            label = target
        try:
            category = find_name(invdata, target)
        except KeyError:
            print("  not found:", target)
            break
        # For some reason inventories uses slightly different names than
        # the document sources.
        category = {
            'py:attribute': 'py:attr',
            'py:class': 'py:class',
            'py:function': 'py:func',
            'py:method': 'py:meth',
            'py:module': 'py:mod',
            }[category]
        if label == target:
            link = f':{category}:`{target}`'
        else:
            link = f':{category}:`{label} <{target}>`'
        line = line[:match.start()] + link + line[match.end():]
    return line

def main():
    invdata = load_inventory(str(apidocs_dir / 'objects.inv'))
    assert invdata

    for doc_path in docs_dir.glob('**/*.rst'):
        out_path = doc_path.with_suffix('.rst.tmp')
        print(doc_path)
        with doc_path.open() as inp:
            with out_path.open('w') as out:
                for line in inp:
                    out.write(convert(line, invdata))
        out_path.replace(doc_path)

if __name__ == '__main__':
    main()
