from __future__ import annotations
from . import HTTPResponse, HTTPRequest
from . import HTTPRequestExecutor


class MockHTTPRequestExecutor(HTTPRequestExecutor):

	def __init__(self):
		self._url_to_response_map: dict[str, HTTPResponse] = dict()
		self._default_response: HTTPResponse = HTTPResponse(404, {}, b"")
		self._requests_executed: list[HTTPRequest] = list()

	def set_response_for_url(self, url: str, response: HTTPResponse):
		self._url_to_response_map[url] = response

	def set_default_response(self, response: HTTPResponse):
		# TODO Make this a copy/add copy functionality to core response class.
		self._default_response = response

	def get_default_response(self):
		return self._default_response

	def assert_any_request_sent_to_url(self, url: str):
		for executed_request in self._requests_executed:
			if executed_request.url == url:
				return
		raise AssertionError(f"no request for {url} was executed")

	def assert_exactly_one_request_sent(self):
		amount_of_requests_sent = len(self._requests_executed)
		if amount_of_requests_sent < 1:
			raise AssertionError("no requests were executed")
		if amount_of_requests_sent > 1:
			raise AssertionError(f"more than one request was sent, {amount_of_requests_sent} were")

	async def execute_request(self, request: HTTPRequest) -> HTTPResponse:
		self._requests_executed.append(request)
		if request.url in self._url_to_response_map:
			return self._url_to_response_map[request.url]
		return self._default_response