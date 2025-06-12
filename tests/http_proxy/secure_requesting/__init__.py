from __future__ import annotations
import os
from unittest import IsolatedAsyncioTestCase
from requiem_ambassador.http_proxy.requests import HTTPResponse, HTTPRequest
from requiem_ambassador.http_proxy.requests.extra import MockHTTPRequestExecutor
from requiem_ambassador.http_proxy.security import MakeRequestSecurelyUseCase


def get_swf_sample_path(sample_file_name: str) -> str:
	file_path = os.path.join(os.path.dirname(__file__), "../../swf_samples", sample_file_name)
	file_path = os.path.abspath(file_path)
	assert os.path.exists(file_path) and os.path.isfile(file_path)
	return file_path


def get_swf_sample_content(sample_file_name: str) -> bytes:
	sample_file_path = get_swf_sample_path(sample_file_name)
	with open(sample_file_path, "rb") as f:
		return f.read()


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

	def _make_and_set_response_for_url_from_swf_sample(self,
													   url: str,
													   sample_file_name: str,
													   headers: dict[str, str] | None = None) -> None:
		file_content = get_swf_sample_content(sample_file_name)
		self._make_and_set_response_for_url(url, content=file_content, headers=headers)

	@staticmethod
	def _make_any_request_for_url(url: str) -> HTTPRequest:
		return HTTPRequest("get", url, {}, b"")

	async def _make_any_request_through_use_case_to_url(self, url: str) -> HTTPResponse:
		request = self._make_any_request_for_url(url)
		return await self._request_use_case.make_request(request)

	async def _verifyUseCaseWillBlockResponseWithSwfSampleFile(self, swf_sample_file: str):
		self._make_and_set_response_for_url_from_swf_sample(
			url="http://example.com/bad_file.swf",
			sample_file_name=swf_sample_file)
		response = await self._make_any_request_through_use_case_to_url("http://example.com/bad_file.swf")
		self.assertResponseMeansSwfBlocked(response)


	def assertResponseMeansSwfBlocked(self, response: HTTPResponse):
		self.assertEqual(response.content, b"bad swf blocked")
		self.assertEqual(response.status_code, 403)