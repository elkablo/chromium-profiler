# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright 2022 Marek Behún <kabel@kernel.org>
#
# Here are some common cases, meant to profile various web pages.

from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException, ElementClickInterceptedException, StaleElementReferenceException
from time import sleep
from case_drivers import CaseDriverWprReplay
from webdriver import repeat_on_error

class Scroll(CaseDriverWprReplay):
	def __init__(self, name, url, time=10, elem=None, by=30, period=50):
		self.name = name
		self.url = url
		self.time = time
		self.elem = ('document.querySelector("%s")' % elem) if elem else 'window'
		self.by = by
		self.period = period

	def __str__(self):
		return super().__str__() + '.%s' % self.name

	def case_run(self):
		self.driver.get(self.url)
		self.driver.execute_script('function scr(){%s.scrollBy(0,%d);setTimeout(scr,%d);}scr();' % (self.elem, self.by, self.period))
		sleep(self.time)

class Browse(CaseDriverWprReplay):
	def __init__(self, name, url, item_selector, browse_items=4, wait=1, go_back=True, before_browsing=None):
		self.name = name
		self.url = url
		self.item_selector = item_selector
		self.browse_items = browse_items
		self.wait = wait
		self.go_back = go_back
		self.before_browsing = before_browsing

	def __str__(self):
		return super().__str__() + '.%s' % self.name

	def before_browsing(self):
		pass

	@staticmethod
	def try_click(elem, tries=5):
		for i in range(tries):
			try:
				elem.click()
				return True
			except (ElementNotInteractableException, ElementClickInterceptedException):
				sleep(1)

		return False

	@repeat_on_error(err=StaleElementReferenceException)
	def goto_item(self, i):
		elems = self.driver.find_elements_by_css_selector(self.item_selector)
		if len(elems) == 0:
			return False

		return Browse.try_click(elems[i % len(elems)])

	def case_run(self):
		self.driver.get(self.url)

		if self.before_browsing:
			self.before_browsing(self)

		for i in range(self.browse_items):
			if self.goto_item(i):
				if self.wait:
					sleep(self.wait)
				if self.go_back:
					self.driver.back()
					sleep(1)

	@staticmethod
	def accept_cookies_fb(self):
		# Currenlty searches for "Accept all" in Czech and clicks
		agree = self.driver.wait_for_element('xpath=//span[text()="Přijmout vše"]')
		ActionChains(self.driver).\
			move_by_offset(agree.location['x'], agree.location['y']).click().perform()

	@staticmethod
	def accept_cookies_reddit(self):
		self.driver.wait_for_element('xpath=//button[text()="Accept all"]').click()

class BrowseWithArrowRight(Browse):
	def goto_item(self, i):
		ActionChains(self.driver).send_keys(Keys.ARROW_RIGHT).perform()
		return True

class Tumblr(CaseDriverWprReplay):
	def case_run(self):
		self.driver.get('https://tumblr.com/search/gifs')

		self.driver.wait_for_element('input[name="email"]').send_keys('user@email.com')
		self.driver.wait_for_element('input[name="password"]').send_keys('some password')
		self.driver.wait_for_element('button[aria-label="Log in"]').click()

		sleep(2)
		self.driver.get('https://tumblr.com/search/gifs')

		self.driver.execute_script('function scr(){window.scrollBy(0,500);setTimeout(scr,2000);}scr();')
		sleep(10)

def all_cases():
	return [
		Browse('amazon', 'https://www.amazon.com.br/s/?k=telefone+celular', '.a-size-base-plus'),
		Browse('hackernews', 'https://news.ycombinator.com', '.athing .title > a', wait=3),
		Browse('reddit_news', 'https://www.reddit.com/r/news/top/?sort=top&t=week', 'article h3',
			wait=5, before_browsing=Browse.accept_cookies_reddit),
		BrowseWithArrowRight('facebook_rihanna_photos',
				     'https://www.facebook.com/photo/?fbid=10156761246686676&set=a.10152251658271676',
				     'div[aria-label="Další fotka"]',
				      browse_items=10, wait=1, go_back=False, before_browsing=Browse.accept_cookies_fb),
		Scroll('9gag', 'https://9gag.com'),
		Scroll('twitter_nasa', 'https://twitter.com/nasa'),
		Scroll('amazon_pixel', 'https://www.amazon.com/s?k=pixel', 5),
		Scroll('google_docs', 'https://docs.google.com/document/d/14sZMXhI1NljEDSFfxhgA4FNI2_rSImxx3tZ4YsNRUdU/preview?safe=true&Debug=true',
			elem='.kix-appview-editor'),
		Tumblr(),
	]
