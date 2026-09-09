from requiem_ambassador.http_proxy.routing import RoutingConfiguration
from ..http_proxy.secure_requesting import SecureRequestingUseCaseTestFixture
from requiem_ambassador.http_proxy.proxying import ReverseProxyHTTPRequestUseCase


class TestReverseProxyHeaderSanitization(SecureRequestingUseCaseTestFixture):
	def setUp(self):
		super().setUp()
		# values don't matter, the mock doesn't actually send requests anywhere.
		self._routing_config = RoutingConfiguration(
			main_api_base_url="http://127.1.2.3/",
			main_cdn_base_url="http://127.1.2.3/",
			cdn_dynamic_base_url="http://127.1.2.3/",
			image_cdn_base_url="http://127.1.2.3/",
			game_image_cdn_base_url="http://127.1.2.3/",
			cdn_dynamic_common_base_url="http://127.1.2.3/")
		self._proxy_use_case = ReverseProxyHTTPRequestUseCase(self._routing_config, self._request_use_case)

	async def test_host_header_should_not_be_present_request_sent_to_executor_regardless_of_casing(self):
		headers = {"Host": "a", "HoSt": "b", "Other-Header": "d"}
		await self._proxy_use_case.proxy_request_for_path("get", "/i/some/path", headers, b"")
		self.assertEqual({"Other-Header": "d"}, self._request_executor.get_only_request_sent().headers)

	async def test_content_length_should_not_be_present_in_request_passed_to_executor_regardless_of_casing(self):
		headers = {"Content-Length": "1", "ConTenT-LeNgth": "b", "Some-Name": "e"}
		await self._proxy_use_case.proxy_request_for_path("get", "/i/some/path", headers, b"")
		self.assertEqual({"Some-Name": "e"}, self._request_executor.get_only_request_sent().headers)
