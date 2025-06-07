import abc
from unittest import IsolatedAsyncioTestCase
from requiem_ambassador.game_proxy.packets import GamePacket
from requiem_ambassador.game_proxy.packets import MockGamePacketSender
from requiem_ambassador.game_proxy.packets import MINIMUM_VALID_PACKET_DATA


class MockGamePacketSenderTestFixture(IsolatedAsyncioTestCase):
	def setUp(self):
		self._packet_sender = MockGamePacketSender()
		self._minimal_valid_packet = GamePacket(MINIMUM_VALID_PACKET_DATA)


class TestMockGamePacketSenderExactAmountSentAssertion(MockGamePacketSenderTestFixture):

	async def test_should_raise_assertion_error_when_no_packets_sent(self):
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_exact_amount_of_packets_sent(4)

	async def test_should_raise_assertion_error_when_more_packets_than_given_amount_were_sent(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_exact_amount_of_packets_sent(2)

	async def test_should_raise_assertion_error_when_less_packets_than_given_amount_were_sent(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_exact_amount_of_packets_sent(3)

	async def test_should_not_raise_any_error_when_no_packets_were_sent_and_given_amount_is_zero(self):
		self._packet_sender.assert_exact_amount_of_packets_sent(0)

class TestMockGamePacketSenderExactlyOneSentAssertion(MockGamePacketSenderTestFixture):

	async def test_should_raise_assertion_error_when_no_packet_sent(self):
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_exactly_one_packet_sent()

	async def test_should_raise_assertion_error_when_more_than_one_packet_sent(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_exactly_one_packet_sent()

	async def test_should_raise_no_errors_when_exactly_one_packet_sent(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		self._packet_sender.assert_exactly_one_packet_sent()
