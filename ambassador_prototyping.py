import asyncio
import configparser
import aiohttp
from aiohttp import web
from asyncio import StreamReader
from asyncio import StreamWriter
from requiem_ambassador.configuration import AmbassadorForwardOptions
from requiem_ambassador.configuration import  AmbassadorHTTPForwardOptions
from requiem_ambassador.configuration import  AmbassadorListenOptions
from requiem_ambassador.configuration import  AmbassadorConfig
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