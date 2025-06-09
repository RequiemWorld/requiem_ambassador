import unittest
from requiem_ambassador.http_proxy.requests import HTTPRequest
from requiem_ambassador.http_proxy.requests import HTTPResponse
from requiem_ambassador.http_proxy.requests.extra import MockHTTPRequestExecutor


class MockHTTPRequestExecutorTestFixture(unittest.IsolatedAsyncioTestCase):
	def setUp(self):
		self._mock_executor = MockHTTPRequestExecutor()

	@staticmethod
	def _get_any_request_for_url(url: str) -> HTTPRequest:
		request = HTTPRequest("get", url, {}, b"")
		return request

	@staticmethod
	def _get_any_response() -> HTTPResponse:
		return HTTPResponse(200, {}, b"")


class TestMockHTTPRequestExecutorGetDefaultResponseMethod(MockHTTPRequestExecutorTestFixture):

	async def test_should_return_same_response_that_is_returned_by_default_from_execute_request(self):
		# we haven't set any response for the url on this request, so it'll give us the default response.
		arbitrary_request = self._get_any_request_for_url("http://127.5.5.5/some/path")
		get_default_response_result = self._mock_executor.get_default_response()
		self.assertIs(await self._mock_executor.execute_request(arbitrary_request), get_default_response_result)

	async def test_should_return_new_response_set_by_the_set_default_response_method(self):
		new_default_response = self._get_any_response()
		self._mock_executor.set_default_response(new_default_response)
		get_default_response_result = self._mock_executor.get_default_response()
		self.assertEqual(new_default_response, get_default_response_result)


class TestMockHTTPRequestExecutorSetDefaultResponseMethod(MockHTTPRequestExecutorTestFixture):

	async def test_should_change_response_given_when_executing_requests_for_urls_with_no_set_responses(self):
		new_default_response = HTTPResponse(200, {}, b"content")
		self._mock_executor.set_default_response(new_default_response)
		arbitrary_request = self._get_any_request_for_url("http://127.13.14.15/some/path")
		self.assertIs(new_default_response, await self._mock_executor.execute_request(arbitrary_request))


class TestMockHTTPRequestExecutorSetResponseForUrlMethod(MockHTTPRequestExecutorTestFixture):

	async def test_should_return_set_response_on_call_to_execute_request_with_given_url(self):
		request = self._get_any_request_for_url("http://127.151.152.153/path")
		response = HTTPResponse(200, {}, b"")
		self._mock_executor.set_response_for_url("http://127.151.152.153/path", response)
		self.assertIs(response, await self._mock_executor.execute_request(request))


class TestMockHTTPRequestExecutorExactlyOneRequestSentAssertion(MockHTTPRequestExecutorTestFixture):

	def test_should_raise_assertion_error_when_no_requests_were_executed(self):
		with self.assertRaises(AssertionError):
			self._mock_executor.assert_exactly_one_request_sent()

	async def test_should_raise_assertion_error_when_more_than_one_request_executed(self):
		request = self._get_any_request_for_url("http://127.199.222.133")
		await self._mock_executor.execute_request(request)
		await self._mock_executor.execute_request(request)
		with self.assertRaises(AssertionError):
			self._mock_executor.assert_exactly_one_request_sent()

	async def test_should_not_raise_any_error_when_exactly_one_request_was_executed(self):
		request = self._get_any_request_for_url("http://127.70.80.90")
		await self._mock_executor.execute_request(request)
		self._mock_executor.assert_exactly_one_request_sent()


class TestMockHTTPRequestExecutorRequestSentToUrlAssertion(MockHTTPRequestExecutorTestFixture):

	async def test_should_raise_assertion_error_when_no_requests_sent_to_url(self):
		with self.assertRaises(AssertionError):
			self._mock_executor.assert_any_request_sent_to_url("http://127.0.0.20")

	async def test_should_not_raise_any_error_when_single_request_sent_to_url(self):
		request = self._get_any_request_for_url("http://127.6.1.1")
		await self._mock_executor.execute_request(request)
		self._mock_executor.assert_any_request_sent_to_url("http://127.6.1.1")

	async def test_should_not_raise_any_error_when_multiple_requests_sent_to_url(self):
		request = self._get_any_request_for_url("http://127.0.1.1")
		await self._mock_executor.execute_request(request)
		await self._mock_executor.execute_request(request)
		self._mock_executor.assert_any_request_sent_to_url("http://127.0.1.1")
