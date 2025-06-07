import aiohttp
import unittest
from wiremock.client import HttpMethods
from . import AiohttpRequestExecutorIntegrationTestFixture


class TestSimpleRequestsAndResponses(AiohttpRequestExecutorIntegrationTestFixture):
	async def test_should_return_response_with_correct_content_under_normal_circumstances(self):
		self._add_simple_mapping("/hello-world", body="Hello World123")
		# the methods we explicitly care about working for now
		for method in ["get", "post"]:
			response = await self._make_http_request("/hello-world", method)
			self.assertEqual(b"Hello World123", response.content)

	async def test_should_return_result_with_correct_status_code_under_normal_circumstances(self):
		self._add_simple_mapping("/status-code", status_code=500)
		# the methods we explicitly care about working for now
		for method in ["get", "post"]:
			response = await self._make_http_request("/status-code", method)
			self.assertEqual(500, response.status_code)

class TestPostRequestSending(AiohttpRequestExecutorIntegrationTestFixture):
	async def test_should_return_result_with_content_from_url_that_only_responds_to_post(self):
		self._add_simple_mapping("/post-body", body="response-data-post", http_method=HttpMethods.POST)
		response = await self._make_http_request("/post-body", method="post")
		self.assertEqual(b"response-data-post", response.content)