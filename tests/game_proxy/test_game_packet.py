import unittest
from base64 import b64decode
from base64 import b64encode
from requiem_ambassador.game_proxy import GamePacket
from requiem_ambassador.game_proxy.packets import MINIMUM_VALID_PACKET_DATA

minimum_length_valid_packet_data = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
class TestGamePacketConstructor(unittest.TestCase):

	def test_should_raise_value_error_when_given_otherwise_valid_data_that_does_not_start_with_one(self):
		# valid packet data from the original game client/server will always start with one.
		minimum_length_data_not_starting_with_one = b"\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
		assert len(minimum_length_data_not_starting_with_one) == 13
		with self.assertRaises(ValueError):
			GamePacket(minimum_length_data_not_starting_with_one)

	def test_should_raise_value_error_when_given_data_starts_with_one_but_is_smaller_than_13_bytes(self):
		invalid_data_1 = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
		assert len(invalid_data_1) < 13
		with self.assertRaises(ValueError):
			GamePacket(invalid_data_1)

	def test_should_construct_without_error_when_given_minimal_length_valid_packet_data(self):
		GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")


class TestOriginalFormatConversionMethod(unittest.TestCase):
	def setUp(self):
		self._minimal_valid_game_packet = GamePacket(minimum_length_valid_packet_data)

	@staticmethod
	def _parse_and_decode_base64_from_written_data(data: bytes) -> bytes:
		assert data.startswith(b"<m>")
		assert data.endswith(b"</m>\x00") or data.endswith(b"</m>")
		base64_data = data.split(b"<m>")[1].split(b"</m>")[0]
		return b64decode(base64_data)

	def test_should_return_bytes_starting_with_opening_m_tag(self):
		written_data = self._minimal_valid_game_packet.to_original_xml_and_base64()
		self.assertTrue(written_data.startswith(b"<m>"))

	def test_should_return_bytes_ending_with_null_character(self):
		written_data = self._minimal_valid_game_packet.to_original_xml_and_base64()
		self.assertTrue(written_data.endswith(b"\x00"))

	def test_should_return_bytes_ending_with_closing_m_tag_and_null_terminator(self):
		written_data = self._minimal_valid_game_packet.to_original_xml_and_base64()
		self.assertTrue(written_data.endswith(b"</m>\x00"))

	def test_should_return_bytes_with_base64_between_tags_with_encoded_data_starting_with_length_prefix(self):
		# the data should have the length added as a 32-bit integer at the beginning,
		# be base64 encoded, wrapped in <m> </m> and end with a null byte as it did originally.
		game_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
		game_packet_data = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
		game_packet_data_with_length_prefix = b"\x00\x00\x00\x0d" + game_packet_data

		written_data = game_packet.to_original_xml_and_base64()
		decoded_base64_content = self._parse_and_decode_base64_from_written_data(written_data)
		self.assertEqual(game_packet_data_with_length_prefix, decoded_base64_content)
		self.assertTrue(decoded_base64_content.startswith(b"\x00\x00\x00\r"), game_packet_data_with_length_prefix)


class TestFromOriginalXMLBase64DataMethod(unittest.TestCase):
	def setUp(self):
		self._valid_packet_data = MINIMUM_VALID_PACKET_DATA
		self._valid_packet_data_with_prefix = self._add_length_prefix(self._valid_packet_data)

	@staticmethod
	def _add_length_prefix(packet_data: bytes) -> bytes:
		return len(packet_data).to_bytes(4, "big") + packet_data

	def test_should_raise_value_error_if_length_of_encoded_data_is_less_than_length_prefix(self):
		data = b"<m>" + b64decode(b"\x00\x00\x00") + b"</m>"
		with self.assertRaises(ValueError):
			GamePacket.from_original_xml_and_base64(data)
	def test_should_read_length_prefixed_base64_encoded_xml_wrapped_packet_data_correctly_with_null_ending(self):
		data = b"<m>" + b64encode(self._valid_packet_data_with_prefix) + b"</m>\x00"
		game_packet = GamePacket.from_original_xml_and_base64(data)
		self.assertEqual(self._valid_packet_data, game_packet.packet_data)

	def test_should_read_length_prefixed_base64_encoded_xml_wrapped_packet_data_correctly_without_null_ending(self):
		data = b"<m>" + b64encode(self._valid_packet_data_with_prefix) + b"</m>"
		game_packet = GamePacket.from_original_xml_and_base64(data)
		self.assertEqual(self._valid_packet_data, game_packet.packet_data)


class TestTypeNumberReading(unittest.TestCase):

	def test_should_read_type_number_correctly_when_less_than_255(self):
		packet_one = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00")
		packet_two = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x09\x00\x00\x00\x00")
		self.assertEqual(4, packet_one.type_number)
		self.assertEqual(9, packet_two.type_number)

	def test_should_read_type_number_correctly_when_greater_than_255(self):
		packet_one = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00")
		packet_two = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00")
		self.assertEqual(256, packet_one.type_number)
		self.assertEqual(257, packet_two.type_number)


class TestPacketDataProperty(unittest.TestCase):
	def test_should_have_value_that_was_passed_in_constructor(self):
		game_packet = GamePacket(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
		self.assertEqual(b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", game_packet.packet_data)