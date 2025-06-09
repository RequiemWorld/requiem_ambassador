from __future__ import annotations
from unittest import IsolatedAsyncioTestCase
from requiem_ambassador.http_proxy.requests import HTTPRequest
from requiem_ambassador.http_proxy.requests import HTTPResponse
from requiem_ambassador.http_proxy.security import MakeRequestSecurelyUseCase
from requiem_ambassador.http_proxy.requests.extra import MockHTTPRequestExecutor


class SecureRequestingUseCaseTestFixture(IsolatedAsyncioTestCase):

	def setUp(self):
		self._request_executor = MockHTTPRequestExecutor()
		self._request_use_case = MakeRequestSecurelyUseCase(self._request_executor)

	def _make_and_set_response_for_url(self,
									   url: str,
									   status: int = 200,
									   headers: dict[str, str] | None = None,
									   content: bytes = b"") -> HTTPResponse:
		headers = headers if headers is not None else {}
		response =  HTTPResponse(status, headers, content)
		self._request_executor.set_response_for_url(url, response)
		return response

	@staticmethod
	def _make_any_request_for_url(url: str) -> HTTPRequest:
		return HTTPRequest("get", url, {}, b"")

	async def _make_any_request_through_use_case_to_url(self, url: str) -> HTTPResponse:
		request = self._make_any_request_for_url(url)
		return await self._request_use_case.make_request(request)

