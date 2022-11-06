# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright 2022 Marek Behún <kabel@kernel.org>

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import socket, multiprocessing, subprocess, signal, sys
from functools import partial
from time import sleep, strftime
import pathlib, os
from shutil import copyfile
from random import sample
from glob import glob
from tempfile import TemporaryDirectory
from selenium.webdriver import ChromeOptions
from webdriver import ProfilerWebDriver

__all__ = ['CaseDriver', 'CaseDriverWithHttpServer', 'CaseDriverWprRecord', 'CaseDriverWprReplay', 'CHROME_PATH', 'CHROMEDRIVER_PATH', 'ADDITIONAL_ARGUMENTS']

module_path = pathlib.Path(__file__)

def relative_to_here(path):
	if path[0] == '/':
		return path
	else:
		return str(module_path.parent / path)

CHROME_PATH = None
CHROMEDRIVER_PATH = None

ADDITIONAL_ARGUMENTS = []

class CaseDriver:
	computes_score = False

	def browser_args(self):
		return [
			#'start-maximized',
			'window-size=1280,1024',
			'user-data-dir=%s' % self.userdatadir.name,
			'disable-notifications',
		] + ADDITIONAL_ARGUMENTS

	def enable_backend(self):
		pass

	def disable_backend(self):
		pass

	def __str__(self):
		return "%s.%s" % (self.__class__.__module__, self.__class__.__name__)

	def merge_profile(self, profile):
		print('Merging profile with llvm-profile')

		inputs = glob('%s/*.profdata' % self.profiledir.name, recursive=True) + \
			 glob('%s/*.profraw' % self.profiledir.name, recursive=True)

		if len(inputs) == 0:
			raise Exception('no profile data generated')

		temp_output = '%s/temp-merged.profdata' % self.profiledir.name

		args = ['llvm-profdata', 'merge', '-output', temp_output]
		args += inputs
		if os.path.isfile(profile):
			args.append(profile)

		result = subprocess.run(args)
		if result.returncode != 0:
			raise Exception('Profile merging failed [return code %d]' % result.returncode)

		if os.path.exists(profile):
			os.unlink(profile)
		try:
			os.rename(temp_output, profile)
		except OSError:
			copyfile(temp_output, profile)

	def run(self, profile=None):
		if CHROME_PATH is None or CHROMEDRIVER_PATH is None:
			raise RuntimeError('CHROME_PATH or CHROMEDRIVER_PATH unset')

		self.enable_backend()

		self.userdatadir = TemporaryDirectory()
		self.profiledir = TemporaryDirectory()

		opts = ChromeOptions()
		opts.binary_location = CHROME_PATH

		for arg in self.browser_args():
			opts.add_argument(arg)

		try:
			os.environ['LLVM_PROFILE_FILE'] = '%s/%%h-%%p.profdata' % self.profiledir.name

			self.driver = ProfilerWebDriver(
				executable_path=CHROMEDRIVER_PATH,
				options=opts
			)

			self.case_run()

			self.driver.quit()
			self.userdatadir.cleanup()
			if profile:
				self.merge_profile(profile)
			self.profiledir.cleanup()
		except Exception as e:
			self.driver.quit()
			self.userdatadir.cleanup()
			self.profiledir.cleanup()
			self.disable_backend()
			raise e

		self.disable_backend()

class CaseDriverWithHttpServer(CaseDriver):
	def __init__(self, addr=None):
		if addr is None:
			addr = ('127.0.0.1', 0)
		self._addr = addr

	def enable_backend(self):
		ThreadingHTTPServer.address_family = socket.AddressFamily.AF_INET
		request_handler = partial(SimpleHTTPRequestHandler, directory=relative_to_here(self.directory))
		self._httpd = ThreadingHTTPServer(self._addr, request_handler)
		self.port = self._httpd.socket.getsockname()[1]
		self.url = 'http://localhost:%u' % (self.port,)
		self._serving_process = multiprocessing.Process(target=self._httpd.serve_forever)
		self._serving_process.start()

	def disable_backend(self):
		self._serving_process.terminate()
		self._serving_process.join()

class CaseDriverWprBase(CaseDriver):
	def browser_args(self):
		return super().browser_args() + [
			'host-resolver-rules=MAP *:443 127.0.0.1:%d,EXCLUDE localhost' % self.https_port,
			'ignore-certificate-errors-spki-list=PhrPvGIaAMmd29hj8BCZOq096yj7uMpRNHpn5PDxI6I=',
			'proxy-server=http=https://127.0.0.1:%d' % self.https_to_http_port,
			'trusted-spdy-proxy=127.0.0.1:%d' % self.https_to_http_port,
		]

	def try_enable_backend(self):
		args = [
			'wpr',
			self.method,
			'--https_port=%d' % self.https_port,
			'--https_to_http_port=%d' % self.https_to_http_port,
			relative_to_here('web-page-records/' + str(self) + '.wprgo')
		]

		self._wpr = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
					     stderr=subprocess.PIPE)
		started_ports = 0
		for line in self._wpr.stderr:
			for port in [self.https_to_http_port, self.https_port]:
				if line.find(b'Starting server on https://127.0.0.1:%d\n' % port) >= 0:
					started_ports += 1
				elif line.find(b'Failed to start server on https://localhost:%d:' % port) >= 0:
					self._wpr.send_signal(signal.SIGINT)
					self._wpr.wait(10)
					del self._wpr
					return False

			if started_ports == 2:
				break

		self._wpr_communicator = multiprocessing.Process(target=self.throw_away_stderr)
		self._wpr_communicator.start()

		return True

	def throw_away_stderr(self):
		for line in self._wpr.stderr:
			if self._wpr.poll():
				return

	def enable_backend(self):
		for i in range(10):
			self.https_to_http_port, self.https_port = tuple(sample(range(30000, 60000), 2))
			if self.try_enable_backend():
				return

		raise Exception('Failed starting wpr (tried 10 times)')

	def disable_backend(self):
		self._wpr.send_signal(signal.SIGINT)
		self._wpr.wait(10)
		del self._wpr
		self._wpr_communicator.terminate()
		self._wpr_communicator.join()
		del self._wpr_communicator

class CaseDriverWprRecord(CaseDriverWprBase):
	method = 'record'

class CaseDriverWprReplay(CaseDriverWprBase):
	method = 'replay'
