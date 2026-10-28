#!/usr/bin/env python3
# Copyright (c) 2026 Igalia
# SPDX-License-Identifier: MIT
import argparse
import collections
import re
import signal
import sys

# Exit quietly when the output is piped into head, less, etc.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

parser = argparse.ArgumentParser(description='Print the result of each test case in TestResults.qpa files as CSV.')
parser.add_argument('--summary', action='store_true', help='print the number of cases per result after the list')
parser.add_argument('files', nargs='*', help='qpa files to read (default: stdin)')
args = parser.parse_args()

result_re = re.compile(r'<Result StatusCode="(.*?)"')

# Indexed by case name, the value is the code. When a case appears in several
# files, the result from the last file wins (e.g. a rerun overrides the first
# run).
results = dict()

def parse(stream):
    case_name = None
    code = 'Unknown'
    for line in stream:
        if line.startswith('#beginTestCaseResult'):
            if case_name is not None:
                # The previous case was never closed.
                results[case_name] = 'Incomplete'
            case_name = line.split()[1]
            code = 'Unknown'
        elif case_name is None:
            continue
        elif line.startswith('#endTestCaseResult'):
            results[case_name] = code
            case_name = None
        elif line.startswith('#terminateTestCaseResult'):
            # Crash, Timeout, etc.
            results[case_name] = line.split()[1]
            case_name = None
        else:
            match = result_re.search(line)
            if match is not None:
                code = match.group(1)
    if case_name is not None:
        # Truncated log, e.g. the process was killed.
        results[case_name] = 'Incomplete'

if len(args.files) == 0:
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
    parse(sys.stdin)
else:
    for f in args.files:
        try:
            with open(f, 'r', encoding='utf-8', errors='replace') as stream:
                parse(stream)
        except OSError as e:
            print('ERROR: Unable to open %s: %s' % (f, e.strerror), file=sys.stderr)
            sys.exit(1)

for name, code in sorted(results.items()):
    print('%s,%s' % (name, code))

if args.summary:
    counts = collections.Counter(results.values())
    print()
    for code, count in counts.most_common():
        print('%s: %d' % (code, count))
    print('Total: %d' % (len(results),))
