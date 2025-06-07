from __future__ import annotations
import abc
from base64 import b64decode, b64encode

# There is a strange issue with pycharm thinking this is a string, added bytes type annotation
MINIMUM_VALID_PACKET_DATA: bytes = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

class GamePacket:
	"""
	A value object/wrapper for the data that is supposed to be sent to/from the original game server,
	this class only offers very basic integrity checks on the packet data.
	"""

	def __init__(self, packet_data: bytes):
		"""
		:param packet_data: The raw-data that is sent from the game client to the game server and vice versa, without the length.
		"""
		if not len(packet_data) >= 13:
			raise ValueError("the minimum length of valid packet data is 13 (we aren't working with a length prefix here)")
		if not packet_data.startswith(b"\x01"):
			raise ValueError("valid packet data for the game server/client should always start with one")
		self._packet_data = packet_data

	@property
	def packet_data(self) -> bytes:
		return self._packet_data

	@property
	def type_number(self):
		"""
		The number that indicates what is to be further expected inside the packet, more or less.
		"""
		return int.from_bytes(self._packet_data[7:9], "big")

	def to_original_xml_and_base64(self) -> bytes:
		"""
		Takes the packet data, adds a big endian ordered 4-byte length prefix,
		encodes it in base64, wraps it in <m> </m> and adds a null terminator.
		"""
		packet_data_length_prefix = len(self._packet_data).to_bytes(4, "big")
		packet_data_with_length_prefix = packet_data_length_prefix + self._packet_data
		return b"<m>" + b64encode(packet_data_with_length_prefix) + b"</m>\x00"

	@classmethod
	def from_original_xml_and_base64(cls, xml_base64_data: bytes) -> GamePacket:
		"""
		Takes packet data that has had its length prefixed as a 32-bit big endian
		ordered integer, encoded with base64, wrapped in <m> </m> and optionally terminated with a null byte.

		:raises ValueError: When the length of the encoded data is less the size of the length prefix (4 bytes)
		"""
		base64_data = xml_base64_data.split(b"<m>")[1].split(b"</m>")[0]
		packet_data_with_length_prefix = b64decode(base64_data)
		if len(packet_data_with_length_prefix) < 4:
			raise ValueError(f"{packet_data_with_length_prefix} is not packet data with its length prefixed.")
		return GamePacket(packet_data_with_length_prefix[4:])


class GamePacketSender(abc.ABC):

	@abc.abstractmethod
	async def send_game_packet(self, packet: GamePacket) -> None:
		raise NotImplementedError


class GamePacketReader(abc.ABC):

	@abc.abstractmethod
	async def read_game_packet(self) -> GamePacket:
		raise NotImplementedError


class MockGamePacketSender(GamePacketSender):
	def __init__(self):
		self._sent_packets: list[GamePacket] = list()

	def clear_recorded_packets(self) -> None:
		self._sent_packets.clear()

	def assert_no_packets_sent(self):
		assert len(self._sent_packets) == 0

	def assert_exact_amount_of_packets_sent(self, number: int) -> None:
		assert len(self._sent_packets) == number

	def assert_exactly_one_packet_sent(self) -> None:
		self.assert_exact_amount_of_packets_sent(1)

	def assert_packet_with_type_number_sent(self, type_number: int) -> None:
		found_packet_with_type = False
		for game_packet in self._sent_packets:
			if game_packet.type_number == type_number:
				return
		assert found_packet_with_type, f"no packet with type number {type_number} was sent."

	def assert_packet_with_type_number_sent_exactly_once(self, type_number: int) -> None:
		packets_with_number = 0
		for game_packet in self._sent_packets:
			if game_packet.type_number == type_number:
				packets_with_number += 1
		assert packets_with_number == 1, f"only one packet of that type should have been sent but {packets_with_number} were instead"

	async def send_game_packet(self, packet: GamePacket) -> None:
		self._sent_packets.append(packet)
