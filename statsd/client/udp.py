from __future__ import absolute_import, division, unicode_literals

import socket

from .base import StatsClientBase, PipelineBase
from .dnsresolver import DnsResolver


class Pipeline(PipelineBase):

    def __init__(self, client):
        super(Pipeline, self).__init__(client)
        self._maxudpsize = client._maxudpsize

    def _send(self):
        data = self._stats.popleft()
        while self._stats:
            # Use popleft to preserve the order of the stats.
            stat = self._stats.popleft()
            if len(stat) + len(data) + 1 >= self._maxudpsize:
                self._client._after(data)
                data = stat
            else:
                data += '\n' + stat
        self._client._after(data)


class StatsClient(StatsClientBase):
    """A client for statsd."""

    def __init__(self, host='localhost', port=8125, prefix=None,
                 maxudpsize=512, ipv6=False, respect_ttl=False):
        """Create a new client."""
        fam = socket.AF_INET6 if ipv6 else socket.AF_INET
        self._respect_ttl = respect_ttl
        if respect_ttl:
            self._resolver = DnsResolver(host, port, fam)
            family = self._resolver.get_family()
            addr = self._resolver.get_addr()
        else:
            family, _, _, _, addr = socket.getaddrinfo(
                host, port, fam, socket.SOCK_DGRAM)[0]
        self._addr = addr
        self._sock = socket.socket(family, socket.SOCK_DGRAM)
        self._prefix = prefix
        self._maxudpsize = maxudpsize

    def _send(self, data):
        """Send data to statsd."""
        try:
            if self._respect_ttl:
                self._addr = self._resolver.get_addr()
            self._sock.sendto(data.encode('ascii'), self._addr)
        except (socket.error, RuntimeError):
            # No time for love, Dr. Jones!
            pass

    def pipeline(self):
        return Pipeline(self)
