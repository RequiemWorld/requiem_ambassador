import aiohttp
from ..requests import HTTPRequest
from ..requests import HTTPResponse
from ..requests import HTTPRequestExecutor


async def _aiohttp_response_to_core_response(response: aiohttp.ClientResponse) -> HTTPResponse:
	status_code = response.status
	headers = dict(response.headers)
	content = await response.content.read()
	return HTTPResponse(status_code, headers, content)


class AiohttpHTTPRequestExecutor(HTTPRequestExecutor):
	def __init__(self, client: aiohttp.ClientSession):
		self._client = client

	async def execute_request(self, request: HTTPRequest) -> HTTPResponse:
		aiohttp_response = await self._client.request(request.method, request.url)
		return await _aiohttp_response_to_core_response(aiohttp_response)