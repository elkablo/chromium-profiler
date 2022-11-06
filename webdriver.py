# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright 2022 Marek Behún <kabel@kernel.org>

from selenium.webdriver import Chrome
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from functools import wraps
from time import sleep

__all__ = ['ProfilerWebDriver']

def repeat_on_error(err=Exception, to_sleep=1, contains=None, repeats=5):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			for i in range(1, repeats + 1):
				try:
					return func(*args, **kwargs)
				except err as e:
					if contains is not None and str(e).find(contains) == -1:
						raise e
					if i == repeats:
						raise e
					sleep(to_sleep)
		return wrapper

	return decorator

repeat_on_unexpected = repeat_on_error(err=WebDriverException, contains='unexpected command response')

class ProfilerWebElement(WebElement):
	@repeat_on_unexpected
	def click(self, *args, **kwargs):
		return super().click(*args, *kwargs)

def wrap_elements(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		elems = func(*args, **kwargs)
		for elem in elems:
			elem.__class__ = ProfilerWebElement
		return elems
	return wrapper

def wrap_element(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		elem = func(*args, **kwargs)
		if elem is None:
			return None
		elif elem.__class__ == WebElement:
			elem.__class__ = ProfilerWebElement
		return elem
	return wrapper

class ProfilerWebDriver(Chrome):
	@repeat_on_unexpected
	def get(self, *args, **kwargs):
		return super().get(*args, *kwargs)

	@repeat_on_unexpected
	def back(self, *args, **kwargs):
		return super().back(*args, *kwargs)

	@wrap_elements
	@repeat_on_unexpected
	def find_elements_by_css_selector(self, *args, **kwargs):
		return super().find_elements_by_css_selector(*args, *kwargs)

	def wait_for_javascript_condition(self, condition, time=10):
		while time > 0:
			if self.execute_script('return !!(%s);' % condition):
				return True
			time -= 1
			sleep(1)

		return False

	@wrap_element
	def wait_for_element(self, selector, time=10):
		if selector.startswith('xpath='):
			method = self.find_elements_by_xpath
			selector = selector[6:]
		else:
			method = self.find_elements_by_css_selector

		while time > 0:
			elems = method(selector)
			if len(elems) > 0:
				return elems[0]
			time -= 1
			sleep(1)

		return None

	def wait_for_element_click(self, selector, time=10):
		elem = self.wait_for_element(selector, time)
		if elem:
			elem.click()

		return elem

	def open_in_new_tab(self, url):
		old_handles = set(self.window_handles)

		self.execute_script('window.open("%s", "_blank");' % (url,))

		new_handles = set(self.window_handles)

		win = list(new_handles - old_handles)[0]

		self.switch_to.window(win)

		return win
