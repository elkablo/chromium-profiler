#!/usr/bin/env python
# SPDX-License-Identifier: BSD-3-Clause
#
# Utility to test some web page cases in Chromium,
# meant to profile Chromium for PGO.
#
# Copyright 2022 Marek Behún <kabel@kernel.org>

import argparse, pathlib, sys, os.path
from fnmatch import fnmatchcase
import case_drivers

def available_cases(benchmark=False):
	import speedometer2, webrtc_cases, desktop_cases, stress_cases
	res = []
	for module in speedometer2, webrtc_cases, desktop_cases, stress_cases:
		for case in module.all_cases():
			if not benchmark or case.computes_score:
				res.append(case)

	return res

def die(msg):
	print('%s: error: %s' % (os.path.basename(sys.argv[0]), msg), file=sys.stderr)
	sys.exit(1)

parser = argparse.ArgumentParser(
	description='Utility to test some web page cases in Chromium, meant to profile Chromium for PGO',
	usage='''chromium_profiler.py --list-cases
       chromium_profiler.py --chrome-executable /path/to/chrome --chromedriver-executable /path/to/chromedriver [--case CASE] [--case CASE] ...''',
	epilog='Written in 2022 by Marek Behún <kabel@kernel.org>, license: BSD-3-Clause'
)
parser.add_argument('--chrome-executable', type=pathlib.Path, help='path to chrome executable')
parser.add_argument('--chromedriver-executable', type=pathlib.Path, help='path to chromedriver executable')
parser.add_argument('--list-cases', action='store_true', help='list available profile cases')
parser.add_argument('--case', action='append', help='case to run, glob-style. May be used multiple times. Default: * (all)')
parser.add_argument('--tries', type=int, help='Number of tries for each case in the case a run fails, or to average score when benchmarking. Default: 3')
parser.add_argument('--profile-output', type=pathlib.Path, help='where to save LLVM profile data. Needs the llvm-profdata utility')
parser.add_argument('--add-arg', action='append', type=str, help='additional command line argument for Chromium')
parser.add_argument('--benchmark', action='store_true', help='run benchmark cases and print results')

if __name__ == '__main__':
	args = parser.parse_args()

	if args.list_cases:
		for case in available_cases(args.benchmark):
			print(case)
		exit(0)

	if args.chrome_executable is None or args.chromedriver_executable is None:
		die('--chrome-executable and --chromedriver-executable are required')

	if not args.chrome_executable.is_file():
		die('invalid chrome executable: %s' % args.chrome_executable)
	case_drivers.CHROME_PATH = str(args.chrome_executable.absolute())

	if not args.chromedriver_executable.is_file():
		die('invalid chromedriver executable: %s' % args.chromedriver_executable)
	case_drivers.CHROMEDRIVER_PATH = str(args.chromedriver_executable.absolute())

	if args.profile_output:
		profile = str(args.profile_output.absolute())
		if os.path.exists(profile):
			die('profile output already exists: %s' % args.profile_output)
	else:
		profile = None

	if args.tries is not None:
		if args.tries < 1:
			die('invalid value for --tries option: %s' % args.tries)
		tries = args.tries
	else:
		tries = 3

	if not args.add_arg:
		args.add_arg = []

	for arg in args.add_arg:
		if arg.startswith('--'):
			arg = arg[2:]
		case_drivers.ADDITIONAL_ARGUMENTS.append(arg)

	if not args.case:
		args.case = ['*']

	cases_to_run_names = []
	cases_to_run = []
	for arg in args.case:
		i = 0
		for case in available_cases(args.benchmark):
			case_name = str(case)
			if fnmatchcase(case_name, arg) and case_name not in cases_to_run_names:
				cases_to_run_names.append(case_name)
				cases_to_run.append(case)
				i += 1
		if i == 0:
			die('no cases found matching `%s\'' % arg)

	for case in cases_to_run:
		if args.benchmark:
			print('Benchmarking %s' % case)

			score_sum = 0.0
			for i in range(tries):
				case.run(profile)
				score_sum += case.score
				del case.score
			average_score = score_sum / tries

			print('BENCHMARK_RESULT[%s] = %f' % (case, average_score))
		else:
			print('Running case %s' % case)
			for i in range(1, tries + 1):
				try:
					case.run(profile)
					break
				except Exception as e:
					print('Run %d/%d failed: %s' % (i, tries, repr(e)))
					if i < tries:
						print('Running case %s again' % case)
