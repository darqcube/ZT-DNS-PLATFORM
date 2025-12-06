#!/usr/bin/env python3
"""
ZeroTrust DNS Endpoint (Python version)
Provides local DNS proxy with mTLS authentication to centralized DNS server
"""

import json
import logging
import socket
import ssl
import struct
import sys
import threading
from pathlib import Path

from jwcrypto import jwk, jwt
from cryptography import x509
from cryptography.hazmat.backends import default_backend

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


class ZeroTrustEndpoint:
    def __init__(self):
        self.config = None
        self.tls_context = None
        self.local_port = 53

    def load_config(self):
        """Load and validate JWT-signed configuration"""
        try:
            # Read JWT token
            zt_token = Path("config.zt").read_text()

            # Read CA certificate for JWT verification
            ca_pem = Path("ca.crt").read_bytes()
            ca_cert = x509.load_pem_x509_certificate(ca_pem, default_backend())

            # Extract RSA public key from CA cert
            ca_key = jwk.JWK.from_pyca(ca_cert.public_key())

            # Verify and decode JWT
            token = jwt.JWT(key=ca_key, jwt=zt_token)
            claims = json.loads(token.claims)

            # Parse config payload
            self.config = json.loads(claims["data"])
            log.info(
                f"Loaded config: Type={self.config['type']}, Server={self.config['server']}"
            )

        except FileNotFoundError as e:
            log.fatal(f"Missing required file: {e.filename}")
            sys.exit(1)
        except Exception as e:
            log.fatal(f"Failed to load config: {e}")
            sys.exit(1)

    def setup_tls(self):
        """Configure mTLS context with client certificate"""
        try:
            # Create SSL context for client authentication
            self.tls_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            # Load client certificate and key
            self.tls_context.load_cert_chain(
                certfile="endpoint.crt", keyfile="endpoint.key"
            )

            # Load CA certificate for server verification
            self.tls_context.load_verify_locations("ca.crt")

            # Set server hostname for SNI
            self.tls_context.check_hostname = True

            # Require TLS 1.3
            self.tls_context.minimum_version = ssl.TLSVersion.TLSv1_3

            log.info("mTLS context initialized")

        except ssl.SSLError as e:
            # Check if endpoint.crt is actually a CSR
            try:
                crt_data = Path("endpoint.crt").read_text()
                if "CERTIFICATE REQUEST" in crt_data:
                    log.fatal(
                        "endpoint.crt is a CSR, not a signed certificate. Regenerate client after server update."
                    )
                    sys.exit(1)
            except:
                pass
            log.fatal(f"Failed to setup TLS: {e}")
            sys.exit(1)
        except Exception as e:
            log.fatal(f"Failed to load certificates: {e}")
            sys.exit(1)

    def start_local_dns(self):
        """Start local UDP DNS server on 127.0.0.1"""
        # Try port 53 first (requires root/CAP_NET_BIND_SERVICE)
        for port in [53, 5353]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", port))
                self.local_port = port

                if port == 5353:
                    log.warning(
                        f"Permission denied on port 53, using port {port} (run as root or grant CAP_NET_BIND_SERVICE for port 53)"
                    )

                log.info(f"Local DNS listening on 127.0.0.1:{port}")

                # Handle incoming DNS queries
                while True:
                    try:
                        data, client_addr = sock.recvfrom(65536)
                        # Handle each query in separate thread
                        threading.Thread(
                            target=self.handle_query,
                            args=(data, client_addr, sock),
                            daemon=True,
                        ).start()
                    except Exception as e:
                        log.error(f"Error receiving query: {e}")

            except PermissionError:
                if port == 53:
                    continue  # Try 5353
                else:
                    log.fatal(f"Failed to bind to port {port}: Permission denied")
                    sys.exit(1)
            except Exception as e:
                log.fatal(f"Failed to start DNS server: {e}")
                sys.exit(1)

    def handle_query(self, query: bytes, client_addr: tuple, sock: socket.socket):
        """Process DNS query and return response"""
        try:
            # Service endpoints first try public DNS for non-private queries
            if self.config.get("type") == "service":
                public_response = self.try_public_dns(query)
                if public_response:
                    sock.sendto(public_response, client_addr)
                    return

            # Forward to ZeroTrust DNS server via mTLS
            response = self.forward_to_server(query)
            if response:
                sock.sendto(response, client_addr)

        except Exception as e:
            log.error(f"Error handling query: {e}")

    def try_public_dns(self, query: bytes) -> bytes:
        """Try resolving via public DNS (Cloudflare) for service endpoints"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            sock.sendto(query, ("1.1.1.1", 53))
            response, _ = sock.recvfrom(512)
            sock.close()

            # Verify we got a valid response (more than just header)
            if len(response) > 12:
                return response

        except socket.timeout:
            pass
        except Exception as e:
            log.debug(f"Public DNS query failed: {e}")

        return None

    def forward_to_server(self, query: bytes) -> bytes:
        """Forward DNS query to ZeroTrust server via mTLS DoT (DNS over TLS)"""
        try:
            # Parse server address
            server_host, server_port = self.config["server"].rsplit(":", 1)
            server_port = int(server_port)

            # Create TLS connection with mTLS authentication
            with socket.create_connection(
                (server_host, server_port), timeout=5.0
            ) as raw_sock:
                with self.tls_context.wrap_socket(
                    raw_sock, server_hostname=self.config["server_name"]
                ) as tls_sock:
                    # Send DNS query with 2-byte length prefix (RFC 7858 - DNS over TLS)
                    length_prefix = struct.pack("!H", len(query))
                    tls_sock.sendall(length_prefix + query)

                    # Read response length
                    resp_len_bytes = self._recv_exact(tls_sock, 2)
                    if not resp_len_bytes:
                        return None
                    resp_len = struct.unpack("!H", resp_len_bytes)[0]

                    # Read response data
                    response = self._recv_exact(tls_sock, resp_len)
                    return response

        except ssl.SSLError as e:
            log.error(f"TLS error connecting to server: {e}")
        except socket.timeout:
            log.error("Connection to server timed out")
        except Exception as e:
            log.error(f"Failed to forward query: {e}")

        return None

    def _recv_exact(self, sock: socket.socket, n: int) -> bytes:
        """Read exactly n bytes from socket"""
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def run(self):
        """Main entry point"""
        log.info("ZeroTrust DNS Endpoint starting...")

        # Load configuration
        self.load_config()

        # Setup mTLS
        self.setup_tls()

        # Log endpoint type and target server
        endpoint_type = self.config.get("type", "unknown").upper()
        log.info(f"ZeroTrust {endpoint_type} Endpoint Active → {self.config['server']}")

        if self.config.get("proxy"):
            log.info(f"Service proxy available at: {self.config['proxy']}")

        if self.config.get("domains"):
            log.info(f"Authorized domains: {', '.join(self.config['domains'])}")

        # Start local DNS server (blocking)
        self.start_local_dns()


def main():
    """Entry point"""
    # Check required files exist
    required_files = ["config.zt", "ca.crt", "endpoint.crt", "endpoint.key"]
    missing = [f for f in required_files if not Path(f).exists()]

    if missing:
        log.fatal(f"Missing required files: {', '.join(missing)}")
        log.fatal("Ensure you've extracted all files from the downloaded ZIP package")
        sys.exit(1)

    # Start endpoint
    endpoint = ZeroTrustEndpoint()

    try:
        endpoint.run()
    except KeyboardInterrupt:
        log.info("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        log.fatal(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
