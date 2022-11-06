# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright 2022 Marek Behún <kabel@kernel.org>
#
# Here are some cases meant to stress various thing: JavaScript, WebGL,
# WebAssembly code, video playback.

from time import sleep
from case_drivers import CaseDriverWprReplay
import urllib.parse
import json

class Aquarium(CaseDriverWprReplay):
	def case_run(self):
		self.driver.get('https://webglsamples.org/aquarium/aquarium.html')
		sleep(10)

class Kraken(CaseDriverWprReplay):
	url = 'https://mozilla.github.io/krakenbenchmark.mozilla.org/kraken-1.1/driver.html'
	result_url_prefix = 'https://mozilla.github.io/krakenbenchmark.mozilla.org/kraken-1.1/results.html?'
	computes_score = True

	def case_run(self):
		self.driver.get(self.url)

		limit = 300
		while self.driver.current_url == self.url and limit > 0:
			sleep(1)
			limit -= 1

		# don't compute score if we reached limit of 5 min
		if limit == 0:
			return

		if not self.driver.current_url.startswith(self.result_url_prefix):
			raise Exception('Invalid URL after Kraken test')

		self.score = 0.0
		for key, value in json.loads(urllib.parse.unquote(self.driver.current_url[len(self.result_url_prefix):])).items():
			if key == 'v' or not isinstance(value, list):
				continue
			self.score += sum(value) / 10.0

class PSPDFKit(CaseDriverWprReplay):
	computes_score = True

	def case_run(self):
		self.driver.get('https://pspdfkit.com/webassembly-benchmark/')

		error = self.driver.wait_for_element('div[class="Error"]', time=10)
		if error is not None:
			raise Exception(error.text)

		score = self.driver.wait_for_element('div[class="Score-value"]', time=290)
		if score is None:
			return

		self.score = float(score.text)

class BellardPCEmu(CaseDriverWprReplay):
	def case_run(self):
		self.driver.get('https://bellard.org/jslinux/vm.html?url=win2k.cfg&mem=192&graphic=1&w=1024&h=768')

		canvas = self.driver.wait_for_element('#term_container > canvas')
		if not canvas:
			return

		sleep(30)

		try:
			from PIL import Image
			from io import BytesIO

			# 120 seconds to try to find Start button
			time = 120
			while time > 0:
				sleep(5)
				img = Image.open(BytesIO(canvas.screenshot_as_png))
				img = img.crop((10, 750, 25, 752))
				img = img.convert(mode='RGB')
				if list(img.getdata()) == [(212, 208, 200), (212, 208, 200), (0, 0, 0), (0, 0, 0), (0, 0, 0), (255, 0, 0), (0, 0, 0), (0, 0, 0), (0, 255, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (212, 208, 200), (212, 208, 200), (212, 208, 200), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 0), (0, 0, 0), (0, 255, 0), (0, 255, 0), (0, 0, 0), (0, 0, 0), (212, 208, 200), (212, 208, 200), (212, 208, 200)]:
					break
				time -= 5
		except (ImportError, ModuleNotFoundError) as e:
			print(e)
			# if we don't have PIL library, just wait 120 seconds
			sleep(120)

class YouTubeVideo(CaseDriverWprReplay):
	def case_run(self):
		self.driver.get('https://www.youtube.com/watch?v=gNtJ4HdMavo')

		if self.driver.wait_for_element_click('#content > div.body.style-scope.ytd-consent-bump-v2-lightbox > div.footer.style-scope.ytd-consent-bump-v2-lightbox > div.buttons.style-scope.ytd-consent-bump-v2-lightbox > ytd-button-renderer:nth-child(2) > a') is not None:
			sleep(15)

class SpreadSheet(CaseDriverWprReplay):
	def case_run(self):
		self.driver.get('https://docs.google.com/spreadsheets/d/16jfsJs14QrWKhsbxpdJXgoYumxNpnDt08DTK82Puc2A/edit#gid=896027318&range=C:C')

def all_cases():
	return [
		Aquarium(),
		Kraken(),
		PSPDFKit(),
		BellardPCEmu(),
		YouTubeVideo(),
		SpreadSheet(),
	]
