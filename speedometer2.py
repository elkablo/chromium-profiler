# SPDX-License-Identifier: BSD-3-Clause
#
# Apple's Speedometer 2 case for profiling Chromium
#
# Copyright 2014 The Chromium Authors.
#
# Modified for chromium-profiler by Marek Behún <kabel@kernel.org>
#
# This code is based on Chromium's own perf code from file
#   tools/perf/page_sets/speedometer2_pages.py
# in Chromium sources (Chromium version 94.0.4606.41).
#
# Basically the code does almost the same things, but:
# - it is rewritten to use our ChromeProfileDriver (from profilers.py)
# - it does not do benchmark measurements, since we don't need them

from time import sleep
from case_drivers import CaseDriverWithHttpServer

class speedometer2(CaseDriverWithHttpServer):
	directory='speedometer'
	timeout = 100
	computes_score = True

	def __str__(self):
		return 'speedometer2'

	def case_run(self):
		self.driver.get(self.url)

		# uncomment this to enable only first suite
		# self.driver.execute_script('Suites=Suites.slice(0,1);')

		self.driver.execute_script('startTest();')

		result_number = self.driver.wait_for_element('#result-number')
		info = self.driver.wait_for_element('#info')

		timeout = self.timeout
		while len(result_number.text) == 0 and timeout > 0:
			print(info.text)
			sleep(1)
			timeout -= 1

		self.score = float(result_number.text)

def all_cases():
	return [speedometer2()]
