# ADR-0004: VPN-isolated SearXNG profile

- Status: Accepted
- Date: 2026-08-06

The optional VPN search instance shares Gluetun's network namespace. ProtonVPN WireGuard credentials are injected at runtime. A failed tunnel removes external connectivity instead of falling back to the host connection.
