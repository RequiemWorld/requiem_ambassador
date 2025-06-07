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

	async def test_should_raise_assertion_errors_again_after_packets_cleared(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		self._packet_sender.clear_recorded_packets()
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_exact_amount_of_packets_sent(2)

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

	async def test_should_raise_assertion_error_again_after_packet_cleared(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		self._packet_sender.clear_recorded_packets()
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


class TestMockPacketSenderNoPacketsSentAssertion(MockGamePacketSenderTestFixture):
	async def test_should_raise_no_errors_when_no_packets_have_been_sent(self):
		self._packet_sender.assert_no_packets_sent()

	async def test_should_raise_no_errors_again_after_packets_have_been_cleared(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		self._packet_sender.clear_recorded_packets()
		self._packet_sender.assert_no_packets_sent()

	async def test_should_raise_assertion_error_when_single_packet_has_been_sent(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		with self.assertRaises(AssertionError):
				self._packet_sender.assert_no_packets_sent()

	async def test_should_raise_assertion_error_when_multiple_packets_have_been_sent(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		with self.assertRaises(AssertionError):
				self._packet_sender.assert_no_packets_sent()


class TestMockPacketSenderPacketWithTypeNumberSentAssertion(MockGamePacketSenderTestFixture):
	async def test_should_raise_no_errors_when_packet_with_type_number_was_sent(self):
		type_4_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00")
		await self._packet_sender.send_game_packet(type_4_packet)
		self._packet_sender.assert_packet_with_type_number_sent(4)

	async def test_should_raise_assertion_error_when_no_packets_have_been_sent(self):
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_packet_with_type_number_sent(90)

	async def test_should_raise_assertion_error_again_after_packets_have_been_cleared(self):
		type_8_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00")
		type_9_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x09\x00\x00\x00\x00")
		await self._packet_sender.send_game_packet(type_8_packet)
		await self._packet_sender.send_game_packet(type_9_packet)
		self._packet_sender.clear_recorded_packets()
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_packet_with_type_number_sent(8)

	async def test_should_raise_assertion_error_when_only_packets_with_different_type_numbers_sent(self):
		type_1_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00")
		type_2_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00")
		await self._packet_sender.send_game_packet(type_1_packet)
		await self._packet_sender.send_game_packet(type_2_packet)
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_packet_with_type_number_sent(3)

class TestMockPacketSenderTypeNumberExactlyOnceSentAssertion(MockGamePacketSenderTestFixture):

	async def test_should_raise_assertion_error_when_no_packets_sent(self):
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_packet_with_type_number_sent_exactly_once(100)

	async def test_should_raise_assertion_error_after_packets_cleared(self):
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		await self._packet_sender.send_game_packet(self._minimal_valid_packet)
		self._packet_sender.clear_recorded_packets()
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_packet_with_type_number_sent_exactly_once(2)

	async def test_should_raise_assertion_error_when_multiple_packets_of_same_type_sent(self):
		type_8_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00")
		await self._packet_sender.send_game_packet(type_8_packet)
		await self._packet_sender.send_game_packet(type_8_packet)
		with self.assertRaises(AssertionError):
			self._packet_sender.assert_packet_with_type_number_sent_exactly_once(8)

	async def test_should_not_raise_any_error_when_exactly_one_packet_of_type_sent(self):
		type_9_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x09\x00\x00\x00\x00")
		await self._packet_sender.send_game_packet(type_9_packet)
		self._packet_sender.assert_packet_with_type_number_sent_exactly_once(9)

	async def test_should_not_raise_any_error_when_multiple_packets_sent_but_only_one_matches_type(self):
		type_1_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00")
		type_2_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00")
		await self._packet_sender.send_game_packet(type_1_packet)
		await self._packet_sender.send_game_packet(type_2_packet)
		self._packet_sender.assert_packet_with_type_number_sent_exactly_once(1)
