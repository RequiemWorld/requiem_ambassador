from __future__ import annotations
import abc


# a normal class is used over a dataclass for hover support in pycharm
class HTTPRequest:
	"""
	A very simple representation of an HTTP as relevant to the ambassador. This request model
	is the request from the perspective of a client, not a server, hence why the url is used and not the path.
	"""
	def __init__(self, method: str, url: str, headers: dict[str, str], content: bytes):
		self.method = method
		self.url = url  # the method, as a string, to be used very literally
		self.headers = headers.copy() # case-sensitive dictionary for the headers
		self.content: bytes = content # the content to send in the request.


# a normal class is used over a dataclass for hover support in pycharm
class HTTPResponse:
	"""
	A very simple representation of an HTTP response as relevant to the ambassador.
	"""
	def __init__(self, status_code: int, headers: dict[str, str], content: bytes):
		self.status_code: int = status_code
		self.headers: dict[str, str] = headers.copy()
		self.content: bytes = content


class HTTPRequestExecutor(abc.ABC):
	"""
	A driven adaptor for making a request independently of third party libraries,
	all important request code can go through a driven adapter with this interface.
	"""
	@abc.abstractmethod
	async def execute_request(self, request: HTTPRequest) -> HTTPResponse:
		raise NotImplementedError
