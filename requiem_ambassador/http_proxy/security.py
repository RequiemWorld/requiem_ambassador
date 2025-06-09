from __future__ import annotations
from .requests import HTTPRequest
from .requests import HTTPResponse
from .requests import HTTPRequestExecutor


class MakeRequestSecurelyUseCase:
	"""
	This is the core code for making HTTP requests and having malicious
	content automatically blocked, independently of external code. To make
	a request, it is passed through a request executor which can be injected.

	The logic for what to do with the response which is translated in by the HTTPRequestExecutor
	is encapsulated in this class, and the request executor can be mocked to give bad responses.

	Features:
		- Content-Encoding/Transfer-Encoding removal.
		- SWF scanning/blocking for abnormal/malicious libraries for loaded content.
	"""
	def __init__(self, request_executor: HTTPRequestExecutor):
		self._request_executor = request_executor

	@staticmethod
	def _normalize_header_names_to_title_casing(headers: dict[str, str]) -> dict[str, str]:
		"""
		Takes a dictionary of header names, possibly multiple headers with the same name in different casings,
		builds a new dictionary with the headers in Title-Casing and returns it, getting rid of duplicate headers.
		"""
		new_headers = {}
		for header_name, header_value in headers.items():
			new_header_name = header_name.title()
			if new_header_name not in new_headers:
				new_headers[new_header_name] = header_value
		return new_headers

	async def make_request(self, request: HTTPRequest) -> HTTPResponse:
		"""
		- Normalizes response headers and leaves only one of each in Title-Casing.
		- Removes Transfer-Encoding header (it should never reach here, but if it did, harm seems possible)
		- Removes Content-Encoding header (this has to be dealt with or our scanning could be useless).
		"""
		original_response = await self._request_executor.execute_request(request)
		normalized_headers = self._normalize_header_names_to_title_casing(original_response.headers)
		if "Content-Encoding" in normalized_headers:
			del normalized_headers["Content-Encoding"]
		if "Transfer-Encoding" in normalized_headers:
			del normalized_headers["Transfer-Encoding"]
		return HTTPResponse(original_response.status_code, normalized_headers, b"")