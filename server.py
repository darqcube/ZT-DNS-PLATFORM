#!/usr/bin/env python3
from flask import Flask, render_template, request, send_file, abort, jsonify
import json, os, secrets, subprocess, zipfile, datetime, socket, httpx
from pathlib import Path
from jwcrypto import jwk, jwt
import asyncio, ssl, dnslib, struct

BASE = Path("/opt/zerotrust-dns")
CERTS = BASE / "certs"
CERTS.mkdir(parents=True, exist_ok=True)
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
BINARIES = BASE / "binaries"
BINARIES.mkdir(exist_ok=True)

DB = DATA / "endpoints.json"
ZONES = DATA / "zones.json"
ROUTES = DATA / "routes.json"  # New: Service routing table


def load(f, default={}):
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default


endpoints = load(DB, {})
zones = load(ZONES, {})
routes = load(ROUTES, {})  # CN -> {host, port} mapping

app = Flask(__name__, template_folder="templates", static_folder="static")

# CA key will be loaded when needed
ca_key = None


def get_ca_key():
    global ca_key
    if ca_key is None:
        ca_key = jwk.JWK.from_pem((CERTS / "ca.key").read_bytes())
    return ca_key


CLIENT_MAP = {
    "win-x64": "ZeroTrust-Client-x64.exe",
    "win-arm64": "ZeroTrust-Client-ARM64.exe",
    "linux-x64": "ZeroTrust-Client-x86_64",
    "linux-arm64": "ZeroTrust-Client-arm64",
}
SERVICE_MAP = {
    "win-x64": "ZeroTrust-Service-x64.exe",
    "win-arm64": "ZeroTrust-Service-ARM64.exe",
    "linux-x64": "ZeroTrust-Service-x86_64",
    "linux-arm64": "ZeroTrust-Service-arm64",
}


def check_binaries_exist():
    """Check if all required binaries exist"""
    missing = []
    for platform, binary in CLIENT_MAP.items():
        if not (BINARIES / binary).exists():
            missing.append(binary)
    for platform, binary in SERVICE_MAP.items():
        if not (BINARIES / binary).exists() and binary not in missing:
            missing.append(binary)
    return missing


def get_binary_status():
    """Get status of all binaries for UI display"""
    status = {}
    for platform, binary in CLIENT_MAP.items():
        path = BINARIES / binary
        status[f"client-{platform}"] = {
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
            "name": binary,
        }
    for platform, binary in SERVICE_MAP.items():
        path = BINARIES / binary
        status[f"service-{platform}"] = {
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
            "name": binary,
        }
    return status


# === AUTO DETECT PUBLIC IP (works in containers, VMs, cloud) ===
def get_public_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 1))
            return s.getsockname()[0]
    except:
        pass
    try:
        resp = httpx.get("https://ifconfig.me", timeout=5)
        return resp.text.strip()
    except:
        return "127.0.0.1"


SERVER_IP = get_public_ip()
print(f"ZeroTrust DNS Server detected IP: {SERVER_IP}")
print(f"  - DNS over TLS: {SERVER_IP}:853")
print(f"  - Service Proxy: {SERVER_IP}:8443")


def make_zt(payload):
    token = jwt.JWT(header={"alg": "RS256"}, claims={"data": json.dumps(payload)})
    token.make_signed_token(get_ca_key())
    return token.serialize()


@app.route("/")
def index():
    binary_status = get_binary_status()
    missing_binaries = check_binaries_exist()
    return render_template(
        "index.html",
        endpoints=endpoints,
        binary_status=binary_status,
        missing_binaries=missing_binaries,
        routes=routes,
    )


@app.route("/client", methods=["POST"])
def create_client():
    name = request.form["name"].strip()
    platform = request.form["platform"]
    cn = f"c{secrets.token_hex(8)}"

    bin_path = BINARIES / CLIENT_MAP[platform]
    if not bin_path.exists():
        return jsonify(
            {
                "success": False,
                "error": f"Binary not found: {CLIENT_MAP[platform]}. Please run ./build_binaries.sh first.",
            }
        ), 400

    # Generate key + CSR
    subprocess.run(
        [
            "openssl",
            "req",
            "-new",
            "-nodes",
            "-newkey",
            "rsa:4096",
            "-keyout",
            f"{CERTS}/{cn}.key",
            "-out",
            f"{CERTS}/{cn}.csr",
            "-subj",
            f"/CN={cn}/O=Client-{name}",
            "-days",
            "3650",
        ],
        check=True,
    )
    # Sign CSR with CA into certificate
    subprocess.run(
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            f"{CERTS}/{cn}.csr",
            "-CA",
            f"{CERTS}/ca.crt",
            "-CAkey",
            f"{CERTS}/ca.key",
            "-CAcreateserial",
            "-days",
            "3650",
            "-out",
            f"{CERTS}/{cn}.crt",
        ],
        check=True,
    )

    payload = {
        "server": f"{SERVER_IP}:853",
        "proxy": f"{SERVER_IP}:8443",  # New: Service proxy endpoint
        "server_name": "dns-server",
        "type": "client",
        "expires": "2028-12-31T23:59:59Z",
    }

    zip_path = CERTS / f"{cn}-client.zip"

    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(bin_path, bin_path.name)
        z.write(CERTS / f"{cn}.crt", "endpoint.crt")
        z.write(CERTS / f"{cn}.key", "endpoint.key")
        z.write(CERTS / "ca.crt", "ca.crt")
        z.writestr("config.zt", make_zt(payload))
        z.writestr(
            "README.txt",
            f"ZeroTrust Client: {name}\n"
            f"Run binary → DNS = 127.0.0.1\n"
            f"All service traffic routed through {SERVER_IP}:8443",
        )

    endpoints[cn] = {
        "type": "client",
        "name": name,
        "platform": platform,
        "created": str(datetime.datetime.now())[:19],
    }
    DB.write_text(json.dumps(endpoints, indent=2))
    return render_template("download.html", cn=cn, name=name, kind="Client")


@app.route("/service", methods=["POST"])
def create_service():
    name = request.form["name"].strip()
    domains_raw = request.form["domains"]
    records_raw = request.form["records"].strip()
    service_host = request.form["service_host"].strip()  # New: Actual service location
    service_port = request.form.get("service_port", "443").strip()
    platform = request.form["platform"]
    cn = f"s{secrets.token_hex(8)}"

    bin_path = BINARIES / SERVICE_MAP[platform]
    if not bin_path.exists():
        return jsonify(
            {
                "success": False,
                "error": f"Binary not found: {SERVICE_MAP[platform]}. Please run ./build_binaries.sh first.",
            }
        ), 400

    domains = [d.strip().rstrip(".") for d in domains_raw.split(",") if d.strip()]
    records = {}
    for line in records_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            continue
        # DNS records now point to the proxy server, not the actual service
        # Clients will connect to SERVER_IP and we'll route them
        records[parts[0]] = f"{parts[1].upper()} {SERVER_IP}"

    if not records:
        records["@"] = f"A {SERVER_IP}"

    # Generate key + CSR
    subprocess.run(
        [
            "openssl",
            "req",
            "-new",
            "-nodes",
            "-newkey",
            "rsa:4096",
            "-keyout",
            f"{CERTS}/{cn}.key",
            "-out",
            f"{CERTS}/{cn}.csr",
            "-subj",
            f"/CN={cn}/O=Service-{name}",
            "-days",
            "3650",
        ],
        check=True,
    )
    subprocess.run(
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            f"{CERTS}/{cn}.csr",
            "-CA",
            f"{CERTS}/ca.crt",
            "-CAkey",
            f"{CERTS}/ca.key",
            "-CAcreateserial",
            "-days",
            "3650",
            "-out",
            f"{CERTS}/{cn}.crt",
        ],
        check=True,
    )

    payload = {
        "server": f"{SERVER_IP}:853",
        "proxy": f"{SERVER_IP}:8443",
        "server_name": "dns-server",
        "type": "service",
        "domains": domains,
        "expires": "2028-12-31T23:59:59Z",
    }

    zip_path = CERTS / f"{cn}-service.zip"

    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(bin_path, bin_path.name)
        z.write(CERTS / f"{cn}.crt", "endpoint.crt")
        z.write(CERTS / f"{cn}.key", "endpoint.key")
        z.write(CERTS / "ca.crt", "ca.crt")
        z.writestr("config.zt", make_zt(payload))
        z.writestr(
            "README.txt",
            f"ZeroTrust Service: {name}\n"
            f"Run on service host: {service_host}:{service_port}\n"
            f"Connects to proxy at: {SERVER_IP}:8443\n"
            f"Clients will be routed through DNS server",
        )

    # Store routing information: CN -> actual service location
    routes[cn] = {
        "host": service_host,
        "port": int(service_port),
        "domains": domains,
        "name": name,
    }
    ROUTES.write_text(json.dumps(routes, indent=2))

    for domain in domains:
        zones[domain] = {
            "records": records,
            "service_cn": cn,  # Track which service owns this domain
            "allowed_endpoints": zones.get(domain, {}).get("allowed_endpoints", [])
            + [cn],
        }

    summary = "<br>".join(
        f"{k} → {SERVER_IP} (routed to {service_host}:{service_port})"
        for k in records.keys()
    )
    ZONES.write_text(json.dumps(zones, indent=2))

    endpoints[cn] = {
        "type": "service",
        "name": name,
        "domains": domains,
        "records_summary": summary,
        "platform": platform,
        "service_host": service_host,
        "service_port": service_port,
    }
    DB.write_text(json.dumps(endpoints, indent=2))
    return render_template("download.html", cn=cn, name=name, kind="Service + DNS Zone")


@app.route("/download/<cn>")
def download(cn):
    if cn not in endpoints:
        abort(404)
    kind = "client" if endpoints[cn]["type"] == "client" else "service"
    return send_file(CERTS / f"{cn}-{kind}.zip", as_attachment=True)


@app.route("/delete/<cn>", methods=["POST"])
def delete_endpoint(cn):
    """Delete an endpoint and clean up all associated resources"""
    if cn not in endpoints:
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    endpoint_data = endpoints[cn]
    endpoint_type = endpoint_data["type"]

    try:
        del endpoints[cn]
        DB.write_text(json.dumps(endpoints, indent=2))

        if endpoint_type == "service" and "domains" in endpoint_data:
            # Remove from routes
            if cn in routes:
                del routes[cn]
                ROUTES.write_text(json.dumps(routes, indent=2))

            # Remove from zones
            for domain in endpoint_data["domains"]:
                if domain in zones:
                    if "allowed_endpoints" in zones[domain]:
                        zones[domain]["allowed_endpoints"] = [
                            ep for ep in zones[domain]["allowed_endpoints"] if ep != cn
                        ]
                    if not zones[domain].get("allowed_endpoints"):
                        del zones[domain]

            ZONES.write_text(json.dumps(zones, indent=2))

        cert_files = [
            CERTS / f"{cn}.crt",
            CERTS / f"{cn}.key",
            CERTS / f"{cn}.csr",
            CERTS / f"{cn}-{endpoint_type}.zip",
        ]

        for cert_file in cert_files:
            if cert_file.exists():
                cert_file.unlink()

        return jsonify(
            {
                "success": True,
                "message": f"{endpoint_type.capitalize()} '{endpoint_data['name']}' deleted successfully",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# DNS over TLS Server (Port 853)
# ============================================


async def dns_handler(reader, writer):
    """Handle DNS queries with mTLS authentication"""
    cert = writer.get_extra_info("peercert")
    if not cert:
        return writer.close()

    cn = dict(cert["subject"])["commonName"]
    if cn not in endpoints:
        return writer.close()

    while True:
        try:
            l = await reader.readexactly(2)
            qlen = int.from_bytes(l, "big")
            qdata = await reader.readexactly(qlen)
            q = dnslib.DNSRecord.parse(qdata)
            qname = str(q.q.qname).rstrip(".").lower()

            resp = None
            for zone, zdata in zones.items():
                if qname == zone or qname.endswith("." + zone):
                    if cn in zdata.get("allowed_endpoints", []):
                        part = qname.removesuffix("." + zone) if qname != zone else "@"
                        part = part.rstrip(".")
                        rec = zdata["records"].get(part) or zdata["records"].get("@")
                        if rec:
                            resp = q.reply()
                            rtype, rdata = rec.split(" ", 1)
                            if rtype == "A":
                                # Return proxy server IP instead of actual service IP
                                resp.add_answer(
                                    dnslib.RR(
                                        qname,
                                        dnslib.QTYPE.A,
                                        rdata=dnslib.A(rdata),
                                        ttl=60,
                                    )
                                )
                            elif rtype == "CNAME":
                                resp.add_answer(
                                    dnslib.RR(
                                        qname,
                                        dnslib.QTYPE.CNAME,
                                        rdata=dnslib.CNAME(rdata + "."),
                                        ttl=60,
                                    )
                                )
                        break

            if not resp:
                # Forward to public DNS if not a private zone
                async with httpx.AsyncClient() as c:
                    r = await c.post(
                        "https://1.1.1.1/dns-query",
                        headers={"accept": "application/dns-message"},
                        content=qdata,
                    )
                    out = r.content
            else:
                out = resp.pack()

            writer.write(len(out).to_bytes(2, "big") + out)
            await writer.drain()
        except:
            break
    writer.close()


async def start_dns():
    """Start DNS over TLS server on port 853"""
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(CERTS / "server.crt", CERTS / "server.key")
    ctx.load_verify_locations(CERTS / "ca.crt")
    ctx.verify_mode = ssl.CERT_REQUIRED
    server = await asyncio.start_server(dns_handler, "0.0.0.0", 853, ssl=ctx)
    print("✓ DNS over TLS server started on port 853")
    async with server:
        await server.serve_forever()


# ============================================
# TLS Proxy/Router (Port 8443)
# Routes client connections to actual services
# ============================================


async def proxy_handler(reader, writer):
    """Handle TLS proxy connections - route clients to services"""
    try:
        # Get client certificate
        cert = writer.get_extra_info("peercert")
        if not cert:
            print("Proxy: No client certificate provided")
            writer.close()
            return

        client_cn = dict(cert["subject"])["commonName"]
        client_addr = writer.get_extra_info("peername")

        if client_cn not in endpoints:
            print(f"Proxy: Unknown client CN: {client_cn}")
            writer.close()
            return

        print(f"Proxy: Client {client_cn} connected from {client_addr}")

        # Read SNI or first data to determine which service is being requested
        # For simplicity, we'll use the client's first request to determine the target
        # In production, you'd use SNI (Server Name Indication) from TLS handshake

        # Read initial data from client (could be HTTP request, database protocol, etc.)
        try:
            initial_data = await asyncio.wait_for(reader.read(8192), timeout=5.0)
            if not initial_data:
                writer.close()
                return
        except asyncio.TimeoutError:
            print(f"Proxy: Timeout reading from client {client_cn}")
            writer.close()
            return

        # Try to extract hostname from HTTP Host header or SNI
        target_service_cn = None
        target_host = None
        target_port = None

        # Parse HTTP request to find Host header
        if b"Host:" in initial_data or b"host:" in initial_data:
            lines = initial_data.split(b"\r\n")
            for line in lines:
                if line.lower().startswith(b"host:"):
                    hostname = line.split(b":", 1)[1].strip().decode()
                    # Find which service owns this domain
                    for zone, zdata in zones.items():
                        if hostname == zone or hostname.endswith("." + zone):
                            if client_cn in zdata.get("allowed_endpoints", []):
                                target_service_cn = zdata.get("service_cn")
                                if target_service_cn and target_service_cn in routes:
                                    route = routes[target_service_cn]
                                    target_host = route["host"]
                                    target_port = route["port"]
                                    print(
                                        f"Proxy: Routing {client_cn} → {target_service_cn} ({target_host}:{target_port})"
                                    )
                                    break
                    break

        if not target_host:
            print(f"Proxy: Could not determine target service for client {client_cn}")
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\nNo route to service\r\n")
            await writer.drain()
            writer.close()
            return

        # Connect to actual service
        try:
            service_reader, service_writer = await asyncio.open_connection(
                target_host, target_port
            )
            print(f"Proxy: Connected to service {target_host}:{target_port}")
        except Exception as e:
            print(
                f"Proxy: Failed to connect to service {target_host}:{target_port}: {e}"
            )
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\nService unavailable\r\n")
            await writer.drain()
            writer.close()
            return

        # Forward initial data to service
        service_writer.write(initial_data)
        await service_writer.drain()

        # Bidirectional proxy
        async def forward(src, dst, direction):
            try:
                while True:
                    data = await src.read(8192)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
            except Exception as e:
                print(f"Proxy: Error in {direction}: {e}")
            finally:
                try:
                    dst.close()
                    await dst.wait_closed()
                except:
                    pass

        # Create bidirectional forwarding tasks
        await asyncio.gather(
            forward(reader, service_writer, f"{client_cn}→service"),
            forward(service_reader, writer, f"service→{client_cn}"),
            return_exceptions=True,
        )

        print(f"Proxy: Connection closed for {client_cn}")

    except Exception as e:
        print(f"Proxy: Error handling connection: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass


async def start_proxy():
    """Start TLS proxy/router on port 8443"""
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(CERTS / "server.crt", CERTS / "server.key")
    ctx.load_verify_locations(CERTS / "ca.crt")
    ctx.verify_mode = ssl.CERT_REQUIRED

    server = await asyncio.start_server(proxy_handler, "0.0.0.0", 8443, ssl=ctx)
    print("✓ TLS Proxy/Router started on port 8443")
    async with server:
        await server.serve_forever()


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    if not (CERTS / "ca.crt").exists():
        print("Generating CA and server certificates...")
        os.system(
            f"cd {CERTS} && "
            "openssl req -new -x509 -days 3650 -keyout ca.key -out ca.crt -subj '/CN=ZeroTrust CA' -nodes && "
            "openssl req -new -nodes -newkey rsa:4096 -keyout server.key -out server.csr -subj '/CN=dns-server' && "
            "openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -days 3650 -out server.crt"
        )
        print("✓ Certificates generated")

    # Check binaries
    missing = check_binaries_exist()
    if missing:
        print("\n⚠️  WARNING: Missing endpoint binaries!")
        print("=" * 50)
        print("The following binaries are required but not found:")
        for binary in missing:
            print(f"  - {binary}")
        print("\nTo build: ./build-all-binaries.sh")
        print("=" * 50)
        print()

    import threading

    # Start DNS server in background
    threading.Thread(target=lambda: asyncio.run(start_dns()), daemon=True).start()

    # Start TLS Proxy/Router in background
    threading.Thread(target=lambda: asyncio.run(start_proxy()), daemon=True).start()

    print(f"\n{'=' * 60}")
    print("✓ ZeroTrust DNS Platform Running")
    print(f"{'=' * 60}")
    print(f"  Web UI:         http://127.0.0.1:5001")
    print(f"  DNS over TLS:   {SERVER_IP}:853")
    print(f"  Service Proxy:  {SERVER_IP}:8443")
    print(f"{'=' * 60}\n")

    app.run(host="0.0.0.0", port=5001)
