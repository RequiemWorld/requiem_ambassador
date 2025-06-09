from .packets import GamePacket
from .packets import GamePacketReader
from .packets import GamePacketSender


class GameProxyGamePacketHandler:
	def __init__(self,
				 downstream_sender: GamePacketSender,
				 upstream_sender: GamePacketSender):
		self._downstream_sender = downstream_sender
		self._upstream_sender = upstream_sender
		self._whitelisted_type_numbers = [20]

	async def handle_packet_from_client(self, packet: GamePacket):
		await self._upstream_sender.send_game_packet(packet)

	async def handle_packet_from_server(self, packet: GamePacket):
		if packet.type_number in self._whitelisted_type_numbers:
			await self._downstream_sender.send_game_packet(packet)