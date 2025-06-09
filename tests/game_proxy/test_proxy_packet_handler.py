import typing
import unittest
from requiem_ambassador.game_proxy import GamePacket
from requiem_ambassador.game_proxy.packets import MockGamePacketSender
from requiem_ambassador.game_proxy.proxying import GameProxyGamePacketHandler

CHAT = 20


class ProxyPacketHandlerTestFixture(unittest.IsolatedAsyncioTestCase):
	def setUp(self):
		self._client_packet_sender = MockGamePacketSender()
		self._server_packet_sender = MockGamePacketSender()
		self._packet_handler = GameProxyGamePacketHandler(
			self._client_packet_sender,
			self._server_packet_sender)
		# any packet type number that isn't whitelisted should be blocked
		# to test that we're going to test handling explicitly and exclude testing these.
		self._whitelisted_packet_numbers = [
			CHAT
		]  # these will be hardcoded in implementation for better testability

	@staticmethod
	def _make_packet_with_type_number(number: int) -> GamePacket:
		packet_data = b"\x01\x00\x00\x00\x00\x00\x00" + number.to_bytes(2, "big") + b"\x00\x00\x00\x00"
		return GamePacket(packet_data)



class TestPacketHandlerServerToClientPacketTypeWhitelisting(ProxyPacketHandlerTestFixture):
	def _generate_all_non_whitelisted_packet_numbers(self) -> typing.Iterable[int]:
		for number in range(0, 0xFFFF):
			if number not in self._whitelisted_packet_numbers:
				yield number

	async def test_should_not_forward_packets_to_client_with_type_numbers_that_are_not_whitelisted(self):
		for non_whitelisted_packet_numbers in self._generate_all_non_whitelisted_packet_numbers():
			game_packet = self._make_packet_with_type_number(non_whitelisted_packet_numbers)
			await self._packet_handler.handle_packet_from_server(game_packet)
			self._client_packet_sender.assert_no_packets_sent()

	async def test_should_be_able_to_forward_packets_with_whitelisted_type_numbers(self):
		for whitelisted_type_number in self._whitelisted_packet_numbers:
			packet_with_whitelisted_type_number = self._make_packet_with_type_number(whitelisted_type_number)
			await self._packet_handler.handle_packet_from_server(packet_with_whitelisted_type_number)
			self._client_packet_sender.assert_packet_with_type_number_sent(whitelisted_type_number)



class TestPacketHandlerClientToServerLogic(ProxyPacketHandlerTestFixture):

	async def test_should_forward_packets_from_the_client_to_the_server(self):
		valid_packet = self._make_packet_with_type_number(2)  # any number will do, outgoing stuff isn't filtered.
		await self._packet_handler.handle_packet_from_client(valid_packet)
		self._server_packet_sender.assert_exactly_one_packet_sent()
		self._server_packet_sender.assert_packet_with_type_number_sent(2)

	async def test_should_not_forward_packets_from_client_back_to_the_client(self):
		valid_packet = self._make_packet_with_type_number(5)  # any number will do, outgoing stuff isn't filtered.
		await self._packet_handler.handle_packet_from_client(valid_packet)
		self._client_packet_sender.assert_no_packets_sent()