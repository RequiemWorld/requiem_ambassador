from __future__ import annotations
import time
import psutil
import random
import socket


def wait_for_port_connectivity(host: str, port: int, keep_trying_for: int | float) -> None:
	"""
	:param host: The hostname or IPv4 address to connect to at the given port.
	:param keep_trying_for: The number of seconds to give up after when a connection doesn't go through.
	:raises TimeoutError: When the port can't be reached in the given time period.
	"""
	time_started_trying = None
	seconds_since_started_trying = 0
	if keep_trying_for < 0.1:
		socket_timeout_value = keep_trying_for
	else:
		socket_timeout_value = 0.1  # this should be an eternity for local connections.
	while seconds_since_started_trying < keep_trying_for:
		if time_started_trying is None:
			time_started_trying = time.time()
		else:
			seconds_since_started_trying = time.time() - time_started_trying
		sock = socket.socket()
		sock.settimeout(socket_timeout_value)
		try:
			sock.connect((host, port))
			return
		except ConnectionRefusedError:
			continue
		except TimeoutError:
			continue
		finally:
			sock.close()
	raise TimeoutError(f"no {host}:{port} could be reached while trying in the given retry for period.")


def _search_for_ports_unavailable(address: str) -> list[int]:
	# Intended for an IPv4 address, although this code is not too specific yet.
	# When a socket has bound to a port but hasn't called listen, it won't
	# show up in the processes, but no other application can use the port.
	# ^^ This means race conditions are a possibility for this search.
	#
	# This will also likely only show the ports available for the current user.
	# https://gist.github.com/fmerlin/d4a60dc4fcdf1687b9742088eb2e4c1c
	unavailable_ports_list = []
	for connection in psutil.net_connections():
		ip_address_matches = address == connection.laddr[0]
		if ip_address_matches and connection.status == psutil.CONN_LISTEN:
			unavailable_ports_list.append(connection.laddr[1])
	return unavailable_ports_list

def pick_random_available_port(for_address: str, pick_starting_at: int = 20000) -> int:
	# Intended for an IPv4 address, although this code is not too specific yet.
	available_ports = []
	unavailable_ports = _search_for_ports_unavailable(for_address)
	for port_number in range(pick_starting_at, 0xFFFF):
		if port_number not in unavailable_ports:
			available_ports.append(port_number)
	return random.choice(available_ports)


def pick_random_loopback_address() -> str:
	# If we choose a random loopback address to bind to, we can lower chances
	# if the port we choose being in conflict. While this isn't an option for
	# testing in production like environments for our servers, this is fine here.
	number_one = "127"
	number_two = str(random.randint(0, 255))
	number_three = str(random.randint(0, 255))
	number_four = str(random.randint(0, 255))
	return f"{number_one}.{number_two}.{number_three}.{number_four}"