#!/usr/bin/env python
# Copyright 2026 Igalia
# SPDX-License-Identifier: MIT
import re
import sys

files = sys.argv[1:]
if len(files) == 0:
    files = ['/dev/stdin']

class State(object):
    def __init__(self):
        self.case_name = None
        self.code = 'Unknown'

result_re = re.compile(r'<Result StatusCode="(.*?)"')
results = dict() # Indexed by case name, the value is the code.

for f in files:
    try:
        with open(f, 'r') as stream:
            state = State()
            for line in stream:
                if state.case_name is not None:
                    if line.startswith('#endTestCaseResult'):
                        results[state.case_name] = state.code
                        state = State()
                    else:
                        match = result_re.search(line)
                        if match is not None:
                            state.code = match.group(1)
                else:
                    if line.startswith('#beginTestCaseResult'):
                        state.case_name = line.split()[1]
    except IOError:
        print('ERROR: Unable to open %s' % (f,), file=sys.stderr)
        sys.exit(1)

for k in sorted(results.keys()):
    print('%s,%s' % (k, results[k]))

sys.exit()