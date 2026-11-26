"""The client address the login throttle keys on."""

import ipaddress
import re

from django.conf import settings

# Azure writes "a.b.c.d:port" and "[v6]:port".
_V4_WITH_PORT = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3}):\d{1,5}$")
_V6_IN_BRACKETS = re.compile(r"^\[([^\[\]]+)\](?::\d{1,5})?$")

# One client holds a /64: keying on it stops walking round the lockout.
IPV6_PREFIX = 64


def forwarded_address(entry):
    """The canonical throttle key for one X-Forwarded-For entry (port
    dropped, IPv6 as its /64), or None. Never the raw text: axes stores an
    inet, and anything else fails the login with a 500."""
    entry = entry.strip()
    match = _V4_WITH_PORT.match(entry) or _V6_IN_BRACKETS.match(entry)
    if match:
        entry = match.group(1)
    if "%" in entry:  # a zone id is a local link, never a client
        return None
    try:
        address = ipaddress.ip_address(entry)
    except ValueError:
        return None
    if address.version == 6:
        if address.ipv4_mapped:
            return str(address.ipv4_mapped)
        return str(ipaddress.ip_network(f"{address}/{IPV6_PREFIX}", strict=False).network_address)
    return str(address)


def client_ip(request):
    """The client's address. Behind a trusted proxy, the rightmost
    X-Forwarded-For entry only: anything left of it can be forged."""
    if settings.TRUST_X_FORWARDED_FOR:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        entries = [e for e in forwarded.split(",") if e.strip()]
        if entries:
            address = forwarded_address(entries[-1])
            if address:
                return address
    return request.META.get("REMOTE_ADDR")
