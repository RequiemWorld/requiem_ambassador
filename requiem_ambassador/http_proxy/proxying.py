from __future__ import annotations
from .routing import RoutingConfiguration
from .requests import HTTPRequest
from .requests import HTTPResponse
from .security import MakeRequestSecurelyUseCase


class ReverseProxyHTTPRequestUseCase:
	def __init__(self,
				 routing_config: RoutingConfiguration,
				 request_use_case: MakeRequestSecurelyUseCase):
		self._request_use_case = request_use_case
		self._routing_configuration = routing_config

	async def proxy_request_for_path(self, method: str, path: str, headers: dict[str, str], content: bytes) -> HTTPResponse:
		headers_to_proxy = {}
		for header_name, header_value in headers.items():
			if header_name.lower() not in ["content-length", "host"]:
				headers_to_proxy[header_name] = header_value
		upstream_url = self._routing_configuration.get_upstream_url_for_path(path)
		request = HTTPRequest(method, upstream_url, headers_to_proxy, content)
		return await self._request_use_case.make_request(request)