from dns.resolver import Resolver
from datetime import datetime
import socket


class DnsResolver(object):
    """DNS Resolver object that can keep track of TTLs"""
    expiration_dt = None
    expires = True

    def __init__(self, name, port, family):
        self.name = name
        self.port = port
        self._set_address_family(family)
        if self.name_is_ip:
            self.expires = False

    def _get_answer(self):
        """Queries for name against the default resolver.  Returns an Answer."""
        try:
            return Resolver().query(self.name, rdtype=self._rdtype)
        except Exception as e:
            raise RuntimeError(e)

    @property
    def _rdtype(self):
        """Translate AddressFamily enum to rdtype"""
        if self.address_family == socket.AddressFamily.AF_INET6:
            return 'AAAA'
        return 'A'  # Default ipv4

    def _set_expiration(self, ts):
        """Takes float timestamp from Answer.expiration and converts it to datetime"""
        self.expires = datetime.fromtimestamp(ts)

    def _set_address_family(self, family):
        """Translate socket variables to AddressFamily enum"""
        if family == socket.AF_INET6:
            self.address_family = socket.AddressFamily.AF_INET6
        else:
            self.address_family = socket.AddressFamily.AF_INET

    @property
    def name_is_ip(self):
        """Attempts to parse name into a packed string based on AddressFamily to determine if name is an IP address."""
        try:
            socket.inet_pton(self.address_family, self.name)
            return True
        except socket.error:
            return False

    @property
    def expired(self):
        """Determine if the Answer is past its TTL"""
        if not self.expires:  # If the name is an IP, it never expires.
            return False
        if not self.expiration_dt:  # If called before get_addr(), assume expired.
            return True
        return datetime.now() > self.expiration_dt

    def get_addr(self):
        """Returns the tuple expected by socket.sendto()"""
        if self.expired:
            response = self._get_answer()
            self._set_expiration(response.expiration)
            if response:
                self.address = str(response[0])
        return (self.address, self.port)

    def get_family(self):
        return self.address_family
