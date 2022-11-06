# SPDX-License-Identifier: BSD-3-Clause
#
# WebRTC cases for profiling Chromium
#
# Copyright 2014 The Chromium Authors.
#
# Modified for chromium-profiler by Marek Behún <kabel@kernel.org>
#
# This code is based on Chromium's own perf code from file
#   tools/perf/page_sets/webrtc_cases.py
# in Chromium sources (Chromium version 94.0.4606.41).
#
# Basically the code does almost the same things, but:
# - it is rewritten to use our ChromeProfileDriver (from profilers.py)
# - it does not do benchmark measurements, since we don't need them

from time import sleep
from case_drivers import CaseDriverWithHttpServer

class WebRTCBase(CaseDriverWithHttpServer):
	directory='webrtc_cases'

	def browser_args(self):
		return super().browser_args() + [
			'use-fake-device-for-media-stream',
			'use-fake-ui-for-media-stream',
		]

class GetUserMedia(WebRTCBase):
	def case_run(self):
		self.driver.get(self.url + '/resolution.html')
		if self.driver.wait_for_element_click('button[id="hd"]') is not None:
			sleep(10)

class DataChannel(WebRTCBase):
	def case_run(self):
		self.driver.get(self.url + '/datatransfer.html')
		self.driver.execute_script('megsToSend.value = 100;')
		if self.driver.wait_for_element_click('button[id="sendTheData"]') is not None:
			sleep(10)

class CanvasCapturePeerConnection(WebRTCBase):
	def case_run(self):
		self.driver.get(self.url + '/canvas-capture.html')
		if self.driver.wait_for_element_click('button[id="startButton"]') is not None:
			sleep(10)

class VideoCodecConstraints(WebRTCBase):
	def __init__(self, codec):
		super().__init__()
		self.codec = codec

	def __str__(self):
		return super().__str__() + '.%s' % self.codec

	def case_run(self):
		self.driver.get(self.url + '/codec_constraints.html')

		self.driver.wait_for_element_click('input[id="%s"]' % self.codec)
		self.driver.wait_for_element_click('button[id="startButton"]')
		self.driver.wait_for_element('button[id="callButton"]:enabled')
		self.driver.wait_for_element_click('button[id="callButton"]')
		sleep(20)
		self.driver.wait_for_element_click('button[id="hangupButton"]')

class MultiplePeerConnections(WebRTCBase):
	def case_run(self):
		self.driver.get(self.url + '/multiple-peerconnections.html')
		self.driver.execute_script('document.getElementById("num-peerconnections").value=10;')
		self.driver.execute_script('document.getElementById("cpuoveruse-detection").checked=false;')
		if self.driver.wait_for_element_click('button[id="start-test"]') is not None:
			sleep(20)

class PausePlayPeerConnections(WebRTCBase):
	def case_run(self):
		self.driver.get(self.url + '/pause-play.html')
		self.driver.execute_script('startTest(20, 10, 20, "video");')
		sleep(20)

class InsertableStreamsAudioProcessing(WebRTCBase):
	def browser_args(self):
		return super().browser_args() + [
			'enable-blink-features=WebCodecs,MediaStreamInsertableStreams',
		]

	def case_run(self):
		self.driver.get(self.url + '/audio-processing.html')
		supported = self.driver.execute_script('''
  try {
    new MediaStreamTrackGenerator('audio');
    return true;
  } catch (e) {
    return false;
  }
''')
		if supported:
			self.driver.wait_for_javascript_condition('audio')
			self.driver.execute_script('start();')
			sleep(10)

class InsertableStreamsVideoProcessing(WebRTCBase):
	def __init__(self, source, transform, sink):
		super().__init__()
		self.source = source
		self.transform = transform
		self.sink = sink

	def __str__(self):
		return super().__str__() + '.%s-%s-%s' % (self.source, self.transform, self.sink)

	def browser_args(self):
		return super().browser_args() + [
			'enable-blink-features=WebCodecs,MediaStreamInsertableStreams',
		]

	def case_run(self):
		self.driver.get(self.url + '/video-processing.html')
		supported = self.driver.execute_script(
			'return (typeof MediaStreamTrackProcessor !== "undefined" && typeof MediaStreamTrackGenerator !== "undefined");')

		if supported:
			self.driver.wait_for_element('select[id="sourceSelector"]:enabled')
			self.driver.execute_script('document.getElementById("sourceSelector").value="%s";' % self.source)
			self.driver.wait_for_element('select[id="transformSelector"]:enabled')
			self.driver.execute_script('document.getElementById("transformSelector").value="%s";' % self.transform)
			self.driver.wait_for_element('select[id="sinkSelector"]:enabled')
			self.driver.execute_script('document.getElementById("sinkSelector").value="%s";' % self.sink)
			self.driver.execute_script('document.getElementById("sourceSelector").dispatchEvent(new InputEvent("input", {}));')
			self.driver.wait_for_element('.sinkVideo')
			sleep(10)

			frame_count = self.driver.execute_script('return document.querySelector(".sinkVideo").webkitDecodedFrameCount;')
			print('webkitDecodedFrameCount = %d' % frame_count)

class NegotiateTiming(WebRTCBase):
	def case_run(self):
		self.driver.get(self.url + '/negotiate-timing.html')

		self.driver.execute_script('start();')
		self.driver.wait_for_javascript_condition('!callButton.disabled')
		self.driver.execute_script('call();')
		self.driver.wait_for_javascript_condition('!renegotiateButton.disabled')
		# Due to suspicion of renegotiate activating too early:
		sleep(1)
		# Negotiate 50 transceivers, then negotiate back to 1, simulating Meet "pin"
		self.driver.execute_script('videoSectionsField.value = 50;')
		self.driver.execute_script('renegotiate();')
		self.driver.wait_for_javascript_condition('!renegotiateButton.disabled')
		self.driver.execute_script('videoSectionsField.value = 1;')
		self.driver.execute_script('renegotiate();')
		self.driver.wait_for_javascript_condition('!renegotiateButton.disabled')
		# Negotiate back up to 50, simulating Meet "unpin". This is what gets measured.
		self.driver.execute_script('videoSectionsField.value = 50;')
		self.driver.execute_script('renegotiate();')
		self.driver.wait_for_javascript_condition('!renegotiateButton.disabled')

def all_cases():
	return [
		GetUserMedia(),
		DataChannel(),
		CanvasCapturePeerConnection(),
		VideoCodecConstraints('VP8'),
		VideoCodecConstraints('VP9'),
		VideoCodecConstraints('H264'),
		MultiplePeerConnections(),
		PausePlayPeerConnections(),
		InsertableStreamsAudioProcessing(),
		InsertableStreamsVideoProcessing('camera', 'webgl', 'video'),
		InsertableStreamsVideoProcessing('video', 'webgl', 'video'),
		InsertableStreamsVideoProcessing('pc', 'webgl', 'video'),
		InsertableStreamsVideoProcessing('camera', 'canvas2d', 'video'),
		InsertableStreamsVideoProcessing('camera', 'noop', 'video'),
		InsertableStreamsVideoProcessing('camera', 'webgl', 'pc'),
	]
