import asyncio


# I don't feel like putting this together, so this implementation is
# AI generated since it is only for development anyway.
async def do_reverse_proxy(listen_host: str, listen_port: int, forward_host: str, forward_port: int) -> None:

	async def _handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
		client_address = writer.get_extra_info('peername')
		print(f"[*] Incoming connection from {client_address}")

		try:
			# Open a connection to the destination server
			print(f"[>] Connecting to forward target {forward_host}:{forward_port}...")
			remote_reader, remote_writer = await asyncio.open_connection(forward_host, forward_port)
			print(f"[+] Connected to forward target for {client_address}")
		except Exception as e:
			print(f"[!] Failed to connect to forward target for {client_address}: {e}")
			writer.close()
			await writer.wait_closed()
			return

		# Helper function to pipe data from a reader to a writer
		async def pipe(src: asyncio.StreamReader, dst: asyncio.StreamWriter, direction: str):
			try:
				while True:
					data = await src.read(0xFFFF)
					if not data:
						print(f"[-] End of stream reached for direction: {direction} ({client_address})")
						break
					print(f"[{direction}] Piping {len(data)} bytes ({client_address})")
					dst.write(data)
					await dst.drain()
			except Exception as e:
				print(f"[!] Error in direction {direction} ({client_address}): {e}")
			finally:
				dst.close()
				try:
					await dst.wait_closed()
				except Exception:
					pass

		# Run both directions simultaneously (client->remote and remote->client)
		await asyncio.gather(
			pipe(reader, remote_writer, f"{client_address} -> Target"),
			pipe(remote_reader, writer, f"Target -> {client_address}"),
			return_exceptions=True
		)
		print(f"[*] Connection fully closed for {client_address}")

	# Start the local server to listen for incoming connections
	print(f"[*] Starting reverse proxy on {listen_host}:{listen_port}...")
	print(f"[*] Forwarding traffic to {forward_host}:{forward_port}")
	server = await asyncio.start_server(_handle_client, listen_host, listen_port)

	async with server:
		print("[*] Proxy server is now active and listening.")
		await server.serve_forever()


# I'm personally developing both the ambassador and the game server from
# a linux workstation. The game server requires <redacted> to run
# and sqlite is not substitutable on account of requiring incrementable sequences.
#
# I'll be running the game server on my host machine where I can use docker for <redacted>,
# and be testing the game from the windows guest machine. This proxy will allow the usage of
# a development config that can expect the game server and file servers running locally without requiring either to be. ~ polllaris
# Example Usage: ./generic_tcp_reverse_proxy.py 127.0.0.1:6000 192.168.98.101:6000
async def main() -> None:
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("listen_address")
	parser.add_argument("forward_address")
	arguments = parser.parse_args()

	listen_host, listen_port = arguments.listen_address.split(":")
	listen_port = int(listen_port)
	forward_host, forward_port = arguments.forward_address.split(":")
	forward_port = int(forward_port)

	await do_reverse_proxy(listen_host, listen_port, forward_host, forward_port)


if __name__ == '__main__':
	asyncio.run(main())