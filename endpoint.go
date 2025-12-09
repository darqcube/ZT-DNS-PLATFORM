package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Config struct {
	Server     string   `json:"server"`
	Proxy      string   `json:"proxy"`
	ServerName string   `json:"server_name"`
	Type       string   `json:"type"`
	Domains    []string `json:"domains"`
	Expires    string   `json:"expires"`
}

type JWTClaims struct {
	Data string `json:"data"`
	jwt.RegisteredClaims
}

func loadConfig() (*Config, error) {
	// Read JWT token
	ztToken, err := os.ReadFile("config.zt")
	if err != nil {
		return nil, fmt.Errorf("failed to read config.zt: %v", err)
	}

	// Read CA certificate for verification
	caPEM, err := os.ReadFile("ca.crt")
	if err != nil {
		return nil, fmt.Errorf("failed to read ca.crt: %v", err)
	}

	// Parse CA certificate
	block, _ := x509.ParseCertificate(caPEM)
	if block == nil {
		// Try PEM format
		certPool := x509.NewCertPool()
		if !certPool.AppendCertsFromPEM(caPEM) {
			return nil, fmt.Errorf("failed to parse CA certificate")
		}
		// Get first cert from pool for public key
		caCert, err := x509.ParseCertificate(caPEM)
		if err != nil {
			// Parse PEM block
			block, _ := parsePEMCertificate(caPEM)
			caCert = block
		}
		block = caCert
	}

	// Parse and verify JWT
	token, err := jwt.ParseWithClaims(string(ztToken), &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return block.PublicKey, nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse JWT: %v", err)
	}

	claims, ok := token.Claims.(*JWTClaims)
	if !ok || !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	// Parse config from JWT data
	var config Config
	if err := json.Unmarshal([]byte(claims.Data), &config); err != nil {
		return nil, fmt.Errorf("failed to parse config: %v", err)
	}

	return &config, nil
}

func parsePEMCertificate(pemData []byte) (*x509.Certificate, error) {
	// Simple PEM parser
	start := []byte("-----BEGIN CERTIFICATE-----")
	end := []byte("-----END CERTIFICATE-----")
	
	startIdx := findIndex(pemData, start)
	endIdx := findIndex(pemData, end)
	
	if startIdx == -1 || endIdx == -1 {
		return nil, fmt.Errorf("invalid PEM format")
	}
	
	// Extract base64 data between markers
	b64Data := pemData[startIdx+len(start):endIdx]
	
	// Decode base64 (simplified - you'd use encoding/base64 in production)
	derData := decodeBase64(b64Data)
	
	return x509.ParseCertificate(derData)
}

func findIndex(data []byte, pattern []byte) int {
	for i := 0; i <= len(data)-len(pattern); i++ {
		match := true
		for j := 0; j < len(pattern); j++ {
			if data[i+j] != pattern[j] {
				match = false
				break
			}
		}
		if match {
			return i
		}
	}
	return -1
}

func decodeBase64(data []byte) []byte {
	// Simplified base64 decoder - in production use encoding/base64
	// This is just a placeholder
	return data
}

func setupTLS(config *Config) (*tls.Config, error) {
	// Load client certificate
	cert, err := tls.LoadX509KeyPair("endpoint.crt", "endpoint.key")
	if err != nil {
		return nil, fmt.Errorf("failed to load client certificate: %v", err)
	}

	// Load CA certificate
	caCert, err := os.ReadFile("ca.crt")
	if err != nil {
		return nil, fmt.Errorf("failed to read CA certificate: %v", err)
	}

	caCertPool := x509.NewCertPool()
	if !caCertPool.AppendCertsFromPEM(caCert) {
		return nil, fmt.Errorf("failed to parse CA certificate")
	}

	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      caCertPool,
		ServerName:   config.ServerName,
		MinVersion:   tls.VersionTLS13,
	}

	return tlsConfig, nil
}

func startLocalDNS(config *Config, tlsConfig *tls.Config) {
	// Try port 53 first (requires root/admin)
	ports := []int{53, 5353}
	var conn *net.UDPConn
	var listenPort int

	for _, port := range ports {
		addr := &net.UDPAddr{
			IP:   net.ParseIP("127.0.0.1"),
			Port: port,
		}
		var err error
		conn, err = net.ListenUDP("udp", addr)
		if err == nil {
			listenPort = port
			if port == 5353 {
				log.Printf("Warning: Could not bind to port 53, using port %d (run as root/admin for port 53)", port)
			}
			break
		}
		if port == ports[len(ports)-1] {
			log.Fatalf("Failed to bind to any DNS port: %v", err)
		}
	}
	defer conn.Close()

	log.Printf("Local DNS listening on 127.0.0.1:%d", listenPort)

	buffer := make([]byte, 512)
	for {
		n, clientAddr, err := conn.ReadFromUDP(buffer)
		if err != nil {
			log.Printf("Error reading from UDP: %v", err)
			continue
		}

		go handleDNSQuery(conn, clientAddr, buffer[:n], config, tlsConfig)
	}
}

func handleDNSQuery(conn *net.UDPConn, clientAddr *net.UDPAddr, query []byte, config *Config, tlsConfig *tls.Config) {
	// For service endpoints, try public DNS first
	if config.Type == "service" {
		response := tryPublicDNS(query)
		if response != nil {
			conn.WriteToUDP(response, clientAddr)
			return
		}
	}

	// Forward to ZeroTrust DNS server via mTLS
	response := forwardToServer(query, config, tlsConfig)
	if response != nil {
		conn.WriteToUDP(response, clientAddr)
	}
}

func tryPublicDNS(query []byte) []byte {
	conn, err := net.DialTimeout("udp", "1.1.1.1:53", 2*time.Second)
	if err != nil {
		return nil
	}
	defer conn.Close()

	conn.SetDeadline(time.Now().Add(2 * time.Second))
	
	if _, err := conn.Write(query); err != nil {
		return nil
	}

	buffer := make([]byte, 512)
	n, err := conn.Read(buffer)
	if err != nil {
		return nil
	}

	if n > 12 { // Valid DNS response
		return buffer[:n]
	}

	return nil
}

func forwardToServer(query []byte, config *Config, tlsConfig *tls.Config) []byte {
	// Connect to DNS server with mTLS
	dialer := &net.Dialer{
		Timeout: 5 * time.Second,
	}

	conn, err := tls.DialWithDialer(dialer, "tcp", config.Server, tlsConfig)
	if err != nil {
		log.Printf("Failed to connect to DNS server: %v", err)
		return nil
	}
	defer conn.Close()

	// Send DNS query with 2-byte length prefix (RFC 7858 - DNS over TLS)
	length := uint16(len(query))
	lengthBytes := []byte{byte(length >> 8), byte(length & 0xff)}
	
	if _, err := conn.Write(append(lengthBytes, query...)); err != nil {
		log.Printf("Failed to send DNS query: %v", err)
		return nil
	}

	// Read length-prefixed DNS response
	respLenBuf := make([]byte, 2)
	if _, err := conn.Read(respLenBuf); err != nil {
		log.Printf("Failed to read DNS response length: %v", err)
		return nil
	}

	respLen := int(respLenBuf[0])<<8 | int(respLenBuf[1])
	if respLen <= 0 || respLen > 4096 {
		log.Printf("Invalid DNS response length: %d", respLen)
		return nil
	}

	resp := make([]byte, respLen)
	if _, err := conn.Read(resp); err != nil {
		log.Printf("Failed to read DNS response: %v", err)
		return nil
	}

	return resp
}

func main() {
	config, err := loadConfig()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	tlsConfig, err := setupTLS(config)
	if err != nil {
		log.Fatalf("Failed to set up TLS: %v", err)
	}

	startLocalDNS(config, tlsConfig)
}