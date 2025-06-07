from __future__ import annotations
import aiohttp
from unittest import IsolatedAsyncioTestCase
from wiremock.constants import Config
from wiremock.client import Mapping
from wiremock.client import MappingRequest
from wiremock.client import MappingResponse
from wiremock.resources.mappings import HttpMethods
from wiremock.resources.mappings.resource import Mappings
from wiremock.testing.testcontainer import WireMockContainer
from requiem_ambassador.http_proxy.requests import HTTPResponse, HTTPRequest
from requiem_ambassador.http_proxy.aiohttp import AiohttpHTTPRequestExecutor


class AiohttpRequestExecutorIntegrationTestFixture(IsolatedAsyncioTestCase):
	""""
	A fixture for aiding in testing that the AiohttpHTTPRequestExecutor will return
	the correct results and make requests to http servers correctly enough.
	"""
	# certain wiremock stuff refuses to work without a running event loop
	async def asyncSetUp(self):
		self._wiremock_container = WireMockContainer(secure=False)
		self._wiremock_container.start()
		# stuff for adding wiremock mappings uses global class state for knowing
		# where the wiremock admin thing is to interact with.
		Config.base_url = self._wiremock_container.get_url("__admin")

		# An instance of the request executor to have on hand for making requests through
		self._aiohttp_client = aiohttp.ClientSession()
		self._request_executor = AiohttpHTTPRequestExecutor(self._aiohttp_client)

	async def asyncTearDown(self):
		# to keep this simple while we learn more about wiremock, a new
		# container will be created for every test.
		self._wiremock_container.stop()

	# Making wiremock match a request and give a response is a decent chunk to write out,
	# so this simple method is provided for filling in details, and making it shorter.
	@staticmethod  # wiremock uses global state class, so this can just be a static method
	def _add_simple_mapping(
			path: str,
			status_code: int = 200,
			body: str = "",
			http_method: str = HttpMethods.ANY):
		"""
		Adds a mapping to the running wiremock container, at the given path, for
		a response with the given status code, body, and for requests matching the http method.
		"""
		mapping = Mapping(
			request=MappingRequest(method=http_method, url=path),
			response=MappingResponse(status=status_code, body=body))
		Mappings.create_mapping(mapping)

	async def _make_http_request(self,
								 path: str,
								 method: str,
								 headers: dict[str, str] | None = None,
								 content: bytes= b"") -> HTTPResponse:
		"""
		:param path: the relative path on the wiremock container to send a request to
		:param method: the method to use on the request sent to the wiremock container.
		:param headers: the headers to include in the request.
		:param content: the content to include in the request. Not sure how to put binary data in the response yet.
		"""
		# we take a relative path to request, because the entire basis of being able to test
		# this is having a single wiremock container up and running to set responses on for paths.
		url = self._wiremock_container.get_url(path)
		request = HTTPRequest(method, url, headers or {}, content)
		return await self._request_executor.execute_request(request)
