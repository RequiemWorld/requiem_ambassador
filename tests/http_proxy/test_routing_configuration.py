from unittest import TestCase
from requiem_ambassador.http_proxy.routing import RoutingConfiguration


class TestGetUpstreamUrlMethod(TestCase):
	def setUp(self):
		self._config = RoutingConfiguration(
			main_api_base_url="http://main-api.example.com/",
			main_cdn_base_url="http://main-cdn.example.com/",
			image_cdn_base_url="http://image-cdn.example.com/",
			game_image_cdn_base_url="http://game-image-cdn.example.com/",
			cdn_dynamic_base_url="http://cdn-dynamic.example.com/",
			cdn_dynamic_common_base_url="http://cdn-dynamic-common.example.com/")

	def test_should_return_upstream_url_for_main_api_path_roughly_as_expected(self):
		upstream_url = self._config.get_upstream_url_for_path("/main-api/1/2/3")
		self.assertEqual("http://main-api.example.com/1/2/3", upstream_url)

	def test_should_return_upstream_url_for_main_cdn_path_roughly_as_expected(self):
		upstream_url = self._config.get_upstream_url_for_path("/main-cdn/4/5/6")
		self.assertEqual("http://main-cdn.example.com/4/5/6", upstream_url)

	def test_should_return_upstream_url_for_image_cdn_path_roughly_as_expected(self):
		upstream_url = self._config.get_upstream_url_for_path("/image-cdn/7/8/9")
		self.assertEqual("http://image-cdn.example.com/7/8/9", upstream_url)

	def test_should_return_upstream_url_for_game_image_path_roughly_as_expected(self):
		upstream_url = self._config.get_upstream_url_for_path("/game-image-cdn/10/11/12")
		self.assertEqual("http://game-image-cdn.example.com/10/11/12", upstream_url)

	def test_should_return_upstream_url_for_cdn_dynamic_path_roughly_as_expected(self):
		upstream_url = self._config.get_upstream_url_for_path("/cdn-dynamic/13/14/15")
		self.assertEqual("http://cdn-dynamic.example.com/13/14/15", upstream_url)

	def test_should_return_upstream_url_for_cdn_dynamic_common_path_roughly_as_expected(self):
		upstream_url = self._config.get_upstream_url_for_path("/cdn-dynamic-common/16/17/18")
		self.assertEqual("http://cdn-dynamic-common.example.com/16/17/18", upstream_url)