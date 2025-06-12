import asyncio
import configparser
import aiohttp
from aiohttp import web
from asyncio import StreamReader
from asyncio import StreamWriter
from requiem_ambassador.game_proxy import GamePacket
from requiem_ambassador.game_proxy.packets import GamePacketSender
from requiem_ambassador.game_proxy.proxying import GamePacketReader
from requiem_ambassador.game_proxy.proxying import GameProxyGamePacketHandler
from requiem_ambassador.http_proxy.routing import RoutingConfiguration
from requiem_ambassador.http_proxy.proxying import ReverseProxyHTTPRequestUseCase
from requiem_ambassador.http_proxy.proxying import MakeRequestSecurelyUseCase
from requiem_ambassador.http_proxy.aiohttp import AiohttpHTTPRequestExecutor



class AsyncioGamePacketReader(GamePacketReader):
	def __init__(self, stream_reader: StreamReader):
		self._stream_reader = stream_reader

	async def read_game_packet(self) -> GamePacket:
		xml_base64_data = await self._stream_reader.readuntil(b"\x00")
		return GamePacket.from_original_xml_and_base64(xml_base64_data)


class AsyncioGamePacketSender(GamePacketSender):
	def __init__(self, stream_writer: StreamWriter):
		self._stream_writer = stream_writer

	async def send_game_packet(self, packet: GamePacket) -> None:
		prepared_packet_data = packet.to_original_xml_and_base64()
		assert prepared_packet_data.endswith(b"\x00"), f"{prepared_packet_data} should end with null"
		self._stream_writer.write(prepared_packet_data)
		await self._stream_writer.drain()


class WebsocketGamePacketSender(GamePacketSender):

	def __init__(self, websocket: aiohttp.ClientWebSocketResponse):
		self._websocket = websocket

	async def send_game_packet(self, packet: GamePacket) -> None:
		prepared_packet_data = packet.to_original_xml_and_base64()
		assert prepared_packet_data.endswith(b"\x00"), f"{prepared_packet_data} should end with null"
		await self._websocket.send_bytes(prepared_packet_data)


class WebsocketGamePacketReader(GamePacketReader):

	def __init__(self, websocket: aiohttp.ClientWebSocketResponse):
		self._websocket = websocket

	async def read_game_packet(self) -> GamePacket:
		xml_base64_packet_data = await self._websocket.receive_bytes()
		return GamePacket.from_original_xml_and_base64(xml_base64_packet_data)



class AmbassadorForwardOptions:
	# to start with, the server used will be a single instance, and configured in the release
	def __init__(self,
				 upstream_game_websocket_url: str):
		self.upstream_game_websocket_url = upstream_game_websocket_url

	@classmethod
	def from_config_file(cls, path: str) -> "AmbassadorForwardOptions":
		config = configparser.ConfigParser()
		config.read(path)
		upstream_game_websocket = config.get("forwarding", "upstream_game_websocket")
		return AmbassadorForwardOptions(upstream_game_websocket)


class AmbassadorHTTPForwardOptions:
	def __init__(self,
				 main_api_base_url: str,
				 main_cdn_base_url: str,
				 image_cdn_base_url: str,
				 game_image_cdn_base_url: str,
				 cdn_dynamic_base_url: str,
				 cdn_dynamic_common_base_url: str):
		"""
		:param main_api_base_url: example: http://www.example.com/ow/
		:param main_cdn_base_url: example: http://cdn-ssl.example.com/ow/
		:param image_cdn_base_url: example: http://cdn-ssl.example.com/i/
		:param cdn_dynamic_base_url: example: http://s3e-main.example.com/shared/
		:param cdn_dynamic_common_base_url: example: http://s3e-images.example.com/shared/
		"""
		self.main_api_base_url = main_api_base_url
		self.main_cdn_base_url = main_cdn_base_url
		self.image_cdn_base_url = image_cdn_base_url
		self.game_image_cdn_base_url = game_image_cdn_base_url
		self.cdn_dynamic_base_url = cdn_dynamic_base_url
		self.cdn_dynamic_common_url = cdn_dynamic_common_base_url

	@staticmethod
	def from_config_file(file_path: str):
		parser = configparser.ConfigParser()
		parser.read(file_path)
		main_api_base_url = parser.get("forwarding-http", "main_api_base_url")
		main_cdn_base_url = parser.get("forwarding-http", "main_cdn_base_url")
		image_cdn_base_url = parser.get("forwarding-http", "image_cdn_base_url")
		cdn_dynamic_base_url = parser.get("forwarding-http", "cdn_dynamic_base_url")
		cdn_dynamic_common_url = parser.get("forwarding-http", "cdn_dynamic_common_base_url")
		return AmbassadorHTTPForwardOptions(
			main_api_base_url=main_api_base_url,
			main_cdn_base_url=main_cdn_base_url,
			image_cdn_base_url=image_cdn_base_url,
			game_image_cdn_base_url=image_cdn_base_url,
			cdn_dynamic_base_url=cdn_dynamic_base_url,
			cdn_dynamic_common_base_url=cdn_dynamic_common_url)


	def to_routing_configuration(self) -> RoutingConfiguration:
		return RoutingConfiguration(
			main_api_base_url=self.main_api_base_url,
			main_cdn_base_url=self.main_cdn_base_url,
			image_cdn_base_url=self.image_cdn_base_url,
			game_image_cdn_base_url=self.game_image_cdn_base_url,
			cdn_dynamic_base_url=self.cdn_dynamic_base_url,
			cdn_dynamic_common_base_url=self.cdn_dynamic_common_url)


class AmbassadorListenOptions:

	def __init__(self, http_host: str, http_port: int, game_host: str, game_port: int):
		self._http_port = http_port
		self._http_host = http_host
		self._game_host = game_host
		self._game_port = game_port

	@property
	def http_host(self) -> str:
		return self._http_host

	@property
	def http_port(self) -> int:
		return self._http_port

	@property
	def game_host(self) -> str:
		return self._game_host

	@property
	def game_port(self) -> int:
		return self._game_port

	@classmethod
	def from_config_file(cls, path: str) -> "AmbassadorListenOptions":
		parser = configparser.ConfigParser()
		parser.read(path)
		http_proxy_host = parser.get("listening", "http_proxy_host")
		http_proxy_port = int(parser.get("listening", "http_proxy_port"))
		game_proxy_host = parser.get("listening", "game_proxy_host")
		game_proxy_port = int(parser.get("listening", "game_proxy_port"))
		return AmbassadorListenOptions(http_proxy_host, http_proxy_port, game_proxy_host, game_proxy_port)


class AmbassadorConfig:
	def __init__(self,
				 listen_options: AmbassadorListenOptions,
				 forward_options: AmbassadorForwardOptions,
				 http_forward_options: AmbassadorHTTPForwardOptions):
		self._listen_options = listen_options
		self._forward_options = forward_options
		self._http_forward_options = http_forward_options

	@property
	def listen_options(self):
		return self._listen_options

	@property
	def forward_options(self):
		return self._forward_options

	@property
	def http_forward_options(self) -> AmbassadorHTTPForwardOptions:
		return self._http_forward_options



async def driving_game_proxy(config: AmbassadorConfig) -> None:
	"""
	The driving adapter for the core game server proxy stuff.
	"""
	game_proxy_host = config.listen_options.game_host
	game_proxy_port = config.listen_options.game_port
	async def _handle_client_to_server(client_reader: GamePacketReader, handler: GameProxyGamePacketHandler) -> None:
		while True:
			game_packet_from_client = await client_reader.read_game_packet()
			print(f"received packet from game client {game_packet_from_client.packet_data}")
			await handler.handle_packet_from_client(game_packet_from_client)


	async def _handle_server_to_client(server_reader: GamePacketReader, handler: GameProxyGamePacketHandler) -> None:
		while True:
			game_packet_from_server = await server_reader.read_game_packet()
			print(f"received packet from game server {game_packet_from_server.packet_data}")
			await handler.handle_packet_from_server(game_packet_from_server)

	async def _handle_connection(reader: StreamReader, writer: StreamWriter) -> None:
		client_packet_reader = AsyncioGamePacketReader(reader)
		client_packet_sender = AsyncioGamePacketSender(writer)
		aiohttp_session = aiohttp.ClientSession()
		print("accepted connection to game proxy")
		async with aiohttp_session.ws_connect(config.forward_options.upstream_game_websocket_url) as ws:
			server_packet_sender = WebsocketGamePacketSender(ws)
			server_packet_reader = WebsocketGamePacketReader(ws)
			proxy_packet_handler = GameProxyGamePacketHandler(client_packet_sender, server_packet_sender)
			await asyncio.gather(
				_handle_client_to_server(client_packet_reader, proxy_packet_handler),
				_handle_server_to_client(server_packet_reader, proxy_packet_handler)
			)
	server = await asyncio.start_server(_handle_connection, host=game_proxy_host, port=game_proxy_port)
	print(f"ambassador game proxy listening on {game_proxy_host}:{game_proxy_port}")

	await server.serve_forever()


async def driving_http_proxy(config: AmbassadorConfig) -> None:
	"""
	The ambassador in part uses hexagonal architecture, the core logic for making
	requests securely is independent of how requests come in to send. This is driver
	code, which, as the name implies, drives the application and translates stuff in and out.
	"""
	http_listen_host = config.listen_options.http_host
	http_listen_port = config.listen_options.http_port
	routing_configuration = config.http_forward_options.to_routing_configuration()

	proxying_use_case = ReverseProxyHTTPRequestUseCase(
		routing_config=routing_configuration,
		request_use_case=MakeRequestSecurelyUseCase(AiohttpHTTPRequestExecutor(client=aiohttp.ClientSession()))
	)
	async def _on_request_to_mobile_server_endpoint(request: web.Request) -> web.Response:
		content = f'<xml url="http://{config.listen_options.http_host}:{config.listen_options.http_port}/ow" action="info"></xml>'
		return web.Response(body=content)

	async def _on_request_for_main_xml_endpoint(request: web.Request) -> web.Response:
		body = routing_configuration.make_main_xml_data(http_listen_host, http_listen_port)
		return web.Response(body=body)

	async def _on_every_route(request: web.Request) -> web.Response:
		print(f"got request for {request.path}")

		if request.path == "/ow/mobileserver":
			return await _on_request_to_mobile_server_endpoint(request)
		if request.path == "/ow/static/main.xml":
			return await _on_request_for_main_xml_endpoint(request)
		else:
			response = await proxying_use_case.proxy_request_for_path(
				method=request.method,
				path=request.path,
				headers=dict(request.headers),
				content=await request.content.read())
			return web.Response(
				status=response.status_code,
				headers=response.headers,
				body=response.content)
		# return web.Response(body="my response")



	app = aiohttp.web.Application()
	# https://stackoverflow.com/questions/70783518/catching-all-routes-in-aiohttp
	app.router.add_route("*", "/{key:.+}", _on_every_route)
	app.router.add_route("get", "/ow/mobileserver", _on_request_to_mobile_server_endpoint)
	runner = web.AppRunner(app)
	await runner.setup()
	site = web.TCPSite(runner, http_listen_host, http_listen_port)
	await site.start()
	print(f"ambassador http proxy listening on {http_listen_host}:{http_listen_port}")
	while True:
		await asyncio.sleep(3600)


async def main() -> None:

	config = AmbassadorConfig(
		AmbassadorListenOptions.from_config_file("ambassador_prototyping.cfg"),
		AmbassadorForwardOptions.from_config_file("ambassador_prototyping.cfg"),
		AmbassadorHTTPForwardOptions.from_config_file("ambassador_prototyping.cfg")
	)
	print("starting the game proxy")
	await asyncio.gather(
		driving_game_proxy(config),
		driving_http_proxy(config)
	)

asyncio.run(main())