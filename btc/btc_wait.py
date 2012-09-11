#! /usr/bin/env python

import argparse
import btclient
import sys
import time
from btc import encoder, decoder, error, list_to_dict, dict_to_list, client

_description = 'wait for torrents or files download to complete'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default="127.0.0.1")
    parser.add_argument('-P', '--port', default=8080)
    parser.add_argument('-r', '--refresh-s', default=1)
    args = parser.parse_args()

    if sys.stdin.isatty():
        error('no input')
    torrents = sys.stdin.read()

    if len(torrents.strip()) == 0:
        exit(0)

    try:
        torrents = decoder.decode(torrents)
    except ValueError:
        error('unexpected input: %s' % torrents)

    hashes = [t['hash'] for t in torrents if 'fileid' not in t]
    fileids = [(t['fileid'], t['hash'], t['sid']) for t in torrents
               if 'fileid' in t]

    while True:
        if len(fileids) == 0:
            break

        d = list_to_dict(client.list_torrents(), 'hash')

        all_finished = True

        for h in hashes:
            if d[h]['state'] != 'FINISHED' and d[h]['state'] != 'SEEDING':
                all_finished = False
                break

        files = client.torrent_files([f[1] for f in fileids],
                                     [f[2] for f in fileids])

        files_hashes = set([f['hash'] for f in files])
        files_dict = dict([(h, dict()) for h in files_hashes])
        for f in files:
            files_dict[f['hash']][f['fileid']] = f

        for (fileid, h, sid) in fileids:
            f = files_dict[h][fileid]
            complete = float(f['downloaded']) / float(f['size']) * 100
            if complete < 100.0:
                all_finished = False
                break

        if all_finished:
            break
        time.sleep(args.refresh_s)

    if not sys.stdout.isatty():
        d = list_to_dict(client.list_torrents(), 'hash')
        d = dict((h, d[h]) for h in hashes if h in d)
        print encoder.encode(dict_to_list(d))

if __name__ == '__main__':
    main()