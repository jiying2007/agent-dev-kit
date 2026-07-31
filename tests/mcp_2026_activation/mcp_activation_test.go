package mcp2026activation

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/auth"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

const (
	modernProtocol = "2026-07-28"
	legacyProtocol = "2025-11-25"
	syntheticToken = "valid"
)

var (
	inputSchema202012 = json.RawMessage(`{
		"$schema": "https://json-schema.org/draft/2020-12/schema",
		"type": "object",
		"additionalProperties": false,
		"properties": {
			"query": {"type": "string", "minLength": 1},
			"limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3}
		},
		"required": ["query"]
	}`)
	outputSchema202012 = json.RawMessage(`{
		"$schema": "https://json-schema.org/draft/2020-12/schema",
		"type": "object",
		"additionalProperties": false,
		"properties": {
			"count": {"type": "integer", "minimum": 1},
			"echo": {"type": "string"}
		},
		"required": ["count", "echo"]
	}`)
)

type schemaInput struct {
	Query string `json:"query"`
	Limit int    `json:"limit"`
}

type schemaOutput struct {
	Count int    `json:"count"`
	Echo  string `json:"echo"`
}

type httpExchange struct {
	RequestHeaders  http.Header
	ResponseHeaders http.Header
}

type recordingTransport struct {
	base  http.RoundTripper
	token string

	mu        sync.Mutex
	exchanges []httpExchange
}

func (r *recordingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	clone := req.Clone(req.Context())
	if r.token != "" {
		clone.Header.Set("Authorization", "Bearer "+r.token)
	}
	exchange := httpExchange{RequestHeaders: clone.Header.Clone()}
	resp, err := r.base.RoundTrip(clone)
	if resp != nil {
		exchange.ResponseHeaders = resp.Header.Clone()
	}
	r.mu.Lock()
	r.exchanges = append(r.exchanges, exchange)
	r.mu.Unlock()
	return resp, err
}

func (r *recordingTransport) snapshot() []httpExchange {
	r.mu.Lock()
	defer r.mu.Unlock()
	return append([]httpExchange(nil), r.exchanges...)
}

func newContext(t *testing.T) context.Context {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	t.Cleanup(cancel)
	return ctx
}

func newServer() *mcp.Server {
	return mcp.NewServer(
		&mcp.Implementation{Name: "adk-mcp-activation-fixture", Version: "1.0.0"},
		nil,
	)
}

func addSchemaTools(server *mcp.Server) {
	mcp.AddTool(server, &mcp.Tool{
		Name:         "schema_echo",
		Description:  "Validate JSON Schema 2020-12 input and output",
		InputSchema:  inputSchema202012,
		OutputSchema: outputSchema202012,
	}, func(_ context.Context, _ *mcp.CallToolRequest, input schemaInput) (*mcp.CallToolResult, schemaOutput, error) {
		return nil, schemaOutput{Count: input.Limit, Echo: input.Query}, nil
	})

	mcp.AddTool[schemaInput, any](server, &mcp.Tool{
		Name:         "invalid_output",
		Description:  "Return an output that must be rejected by the output schema",
		InputSchema:  inputSchema202012,
		OutputSchema: outputSchema202012,
	}, func(_ context.Context, _ *mcp.CallToolRequest, input schemaInput) (*mcp.CallToolResult, any, error) {
		return nil, map[string]any{"count": "not-an-integer", "echo": input.Query}, nil
	})
}

func newHTTPServer(t *testing.T, server *mcp.Server, stateless bool, outer func(http.Handler) http.Handler) *httptest.Server {
	t.Helper()
	handler := http.Handler(mcp.NewStreamableHTTPHandler(
		func(_ *http.Request) *mcp.Server { return server },
		&mcp.StreamableHTTPOptions{Stateless: stateless, JSONResponse: true},
	))
	if outer != nil {
		handler = outer(handler)
	}
	httpServer := httptest.NewServer(handler)
	t.Cleanup(httpServer.Close)
	return httpServer
}

func connectClient(
	t *testing.T,
	ctx context.Context,
	endpoint string,
	token string,
) (*mcp.ClientSession, *recordingTransport) {
	t.Helper()
	recorder := &recordingTransport{base: http.DefaultTransport, token: token}
	transport := &mcp.StreamableClientTransport{
		Endpoint:             endpoint,
		HTTPClient:           &http.Client{Transport: recorder},
		MaxRetries:           -1,
		DisableStandaloneSSE: true,
	}
	client := mcp.NewClient(
		&mcp.Implementation{Name: "adk-mcp-activation-client", Version: "1.0.0"},
		nil,
	)
	session, err := client.Connect(ctx, transport, nil)
	if err != nil {
		t.Fatalf("client.Connect: %v", err)
	}
	t.Cleanup(func() {
		if err := session.Close(); err != nil {
			t.Errorf("session.Close: %v", err)
		}
	})
	return session, recorder
}

func assertProtocol(t *testing.T, session *mcp.ClientSession, want string) {
	t.Helper()
	result := session.InitializeResult()
	if result == nil {
		t.Fatal("InitializeResult is nil")
	}
	if result.ProtocolVersion != want {
		t.Fatalf("negotiated protocol = %q, want %q", result.ProtocolVersion, want)
	}
}

func TestSchemaCompatibilityFixture(t *testing.T) {
	ctx := newContext(t)
	server := newServer()
	addSchemaTools(server)
	httpServer := newHTTPServer(t, server, true, nil)
	session, _ := connectClient(t, ctx, httpServer.URL, "")
	assertProtocol(t, session, modernProtocol)

	listed, err := session.ListTools(ctx, nil)
	if err != nil {
		t.Fatalf("ListTools: %v", err)
	}
	var schemaTool *mcp.Tool
	for _, tool := range listed.Tools {
		if tool.Name == "schema_echo" {
			schemaTool = tool
			break
		}
	}
	if schemaTool == nil {
		t.Fatal("schema_echo missing from tools/list")
	}
	wireSchema, err := json.Marshal(schemaTool.InputSchema)
	if err != nil {
		t.Fatalf("marshal listed input schema: %v", err)
	}
	if !bytes.Contains(wireSchema, []byte(`https://json-schema.org/draft/2020-12/schema`)) {
		t.Fatalf("listed schema does not retain JSON Schema 2020-12 identity: %s", wireSchema)
	}

	valid, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name:      "schema_echo",
		Arguments: map[string]any{"query": "fixture"},
	})
	if err != nil {
		t.Fatalf("valid CallTool: %v", err)
	}
	if valid.IsError {
		t.Fatalf("valid schema call returned tool error: %v", valid.Content)
	}
	structured, ok := valid.StructuredContent.(map[string]any)
	if !ok {
		t.Fatalf("structured content type = %T, want map[string]any", valid.StructuredContent)
	}
	if structured["count"] != float64(3) || structured["echo"] != "fixture" {
		t.Fatalf("structured content = %#v, want default count=3 and echo=fixture", structured)
	}

	for name, arguments := range map[string]map[string]any{
		"missing-required": {"limit": 2},
		"wrong-type":       {"query": "fixture", "limit": "two"},
	} {
		t.Run(name, func(t *testing.T) {
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name:      "schema_echo",
				Arguments: arguments,
			})
			if err != nil {
				t.Fatalf("CallTool returned protocol error: %v", err)
			}
			if !result.IsError {
				t.Fatalf("invalid schema input unexpectedly succeeded: %#v", result.StructuredContent)
			}
		})
	}

	invalidOutput, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name:      "invalid_output",
		Arguments: map[string]any{"query": "fixture"},
	})
	if err != nil {
		if !strings.Contains(err.Error(), "validating tool output") ||
			!strings.Contains(err.Error(), `want "integer"`) {
			t.Fatalf("invalid output failed through an unexpected error path: %v", err)
		}
	} else if invalidOutput == nil || !invalidOutput.IsError {
		t.Fatalf("invalid output unexpectedly passed schema validation: %#v", invalidOutput)
	}
}

func TestVersionPinnedClientServerSmoke(t *testing.T) {
	ctx := newContext(t)
	server := newServer()
	addSchemaTools(server)
	httpServer := newHTTPServer(t, server, true, nil)
	session, recorder := connectClient(t, ctx, httpServer.URL, "")
	assertProtocol(t, session, modernProtocol)

	if _, err := session.ListTools(ctx, nil); err != nil {
		t.Fatalf("ListTools: %v", err)
	}
	if _, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name:      "schema_echo",
		Arguments: map[string]any{"query": "smoke", "limit": 1},
	}); err != nil {
		t.Fatalf("CallTool: %v", err)
	}

	methods := map[string]bool{}
	for _, exchange := range recorder.snapshot() {
		request := exchange.RequestHeaders
		if got := request.Get("Mcp-Protocol-Version"); got != modernProtocol {
			t.Fatalf("Mcp-Protocol-Version = %q, want %q", got, modernProtocol)
		}
		if method := request.Get("Mcp-Method"); method != "" {
			methods[method] = true
		}
		if got := request.Get("Mcp-Session-Id"); got != "" {
			t.Fatalf("modern stateless request unexpectedly has Mcp-Session-Id=%q", got)
		}
		if got := exchange.ResponseHeaders.Get("Mcp-Session-Id"); got != "" {
			t.Fatalf("modern stateless response unexpectedly has Mcp-Session-Id=%q", got)
		}
	}
	for _, method := range []string{"server/discover", "tools/list", "tools/call"} {
		if !methods[method] {
			t.Fatalf("Mcp-Method %q not observed; got %v", method, methods)
		}
	}
}

type syntheticClaims struct {
	issuer   string
	audience string
	scopes   []string
	expires  time.Time
}

func syntheticVerifier(expectedIssuer, expectedAudience string) auth.TokenVerifier {
	claimsByToken := map[string]syntheticClaims{
		syntheticToken: {
			issuer: expectedIssuer, audience: expectedAudience,
			scopes: []string{"mcp.read"}, expires: time.Now().Add(time.Hour),
		},
		"bad-iss": {
			issuer: "https://attacker.invalid", audience: expectedAudience,
			scopes: []string{"mcp.read"}, expires: time.Now().Add(time.Hour),
		},
		"bad-aud": {
			issuer: expectedIssuer, audience: "https://other.example.test/mcp",
			scopes: []string{"mcp.read"}, expires: time.Now().Add(time.Hour),
		},
		"low-scope": {
			issuer: expectedIssuer, audience: expectedAudience,
			scopes: []string{"profile"}, expires: time.Now().Add(time.Hour),
		},
		"expired": {
			issuer: expectedIssuer, audience: expectedAudience,
			scopes: []string{"mcp.read"}, expires: time.Now().Add(-time.Minute),
		},
	}
	return func(_ context.Context, token string, _ *http.Request) (*auth.TokenInfo, error) {
		claims, ok := claimsByToken[token]
		if !ok {
			return nil, fmt.Errorf("%w: unknown token", auth.ErrInvalidToken)
		}
		if claims.issuer != expectedIssuer {
			return nil, fmt.Errorf("%w: issuer mismatch", auth.ErrInvalidToken)
		}
		if claims.audience != expectedAudience {
			return nil, fmt.Errorf("%w: audience mismatch", auth.ErrInvalidToken)
		}
		return &auth.TokenInfo{
			Scopes:     claims.scopes,
			Expiration: claims.expires,
			UserID:     "fixture-user",
			Extra: map[string]any{
				"issuer":   claims.issuer,
				"audience": claims.audience,
			},
		}, nil
	}
}

func authProbe(t *testing.T, endpoint, token string) *http.Response {
	t.Helper()
	req, err := http.NewRequest(http.MethodPost, endpoint, strings.NewReader(`{}`))
	if err != nil {
		t.Fatalf("NewRequest: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("auth probe: %v", err)
	}
	t.Cleanup(func() {
		if err := resp.Body.Close(); err != nil {
			t.Errorf("probe response close: %v", err)
		}
	})
	return resp
}

func TestAuthBoundaryVerification(t *testing.T) {
	ctx := newContext(t)
	const (
		expectedIssuer   = "https://issuer.example.test"
		expectedAudience = "https://mcp.example.test/mcp"
		metadataURL      = "https://mcp.example.test/.well-known/oauth-protected-resource"
	)

	downstreamAuthorization := make(chan string, 1)
	downstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		downstreamAuthorization <- r.Header.Get("Authorization")
		w.Header().Set("Content-Type", "application/json")
		_, _ = io.WriteString(w, `{"status":"ok"}`)
	}))
	t.Cleanup(downstream.Close)

	server := newServer()
	mcp.AddTool(server, &mcp.Tool{
		Name:        "downstream_probe",
		Description: "Prove incoming bearer credentials are not forwarded",
	}, func(ctx context.Context, req *mcp.CallToolRequest, _ struct{}) (*mcp.CallToolResult, map[string]any, error) {
		if req.Extra.TokenInfo == nil {
			return nil, nil, errors.New("missing verified TokenInfo")
		}
		downstreamReq, err := http.NewRequestWithContext(ctx, http.MethodGet, downstream.URL, nil)
		if err != nil {
			return nil, nil, err
		}
		resp, err := http.DefaultClient.Do(downstreamReq)
		if err != nil {
			return nil, nil, err
		}
		defer resp.Body.Close()
		return nil, map[string]any{"status": "ok"}, nil
	})

	authLayer := auth.RequireBearerToken(
		syntheticVerifier(expectedIssuer, expectedAudience),
		&auth.RequireBearerTokenOptions{
			ResourceMetadataURL: metadataURL,
			Scopes:              []string{"mcp.read"},
		},
	)
	httpServer := newHTTPServer(t, server, true, authLayer)

	for _, test := range []struct {
		name       string
		token      string
		wantStatus int
	}{
		{name: "missing-token", wantStatus: http.StatusUnauthorized},
		{name: "wrong-issuer", token: "bad-iss", wantStatus: http.StatusUnauthorized},
		{name: "wrong-audience", token: "bad-aud", wantStatus: http.StatusUnauthorized},
		{name: "insufficient-scope", token: "low-scope", wantStatus: http.StatusForbidden},
		{name: "expired", token: "expired", wantStatus: http.StatusUnauthorized},
	} {
		t.Run(test.name, func(t *testing.T) {
			resp := authProbe(t, httpServer.URL, test.token)
			if resp.StatusCode != test.wantStatus {
				body, _ := io.ReadAll(resp.Body)
				t.Fatalf("status = %d, want %d; body=%s", resp.StatusCode, test.wantStatus, body)
			}
			challenge := resp.Header.Get("WWW-Authenticate")
			if !strings.Contains(challenge, `resource_metadata="`+metadataURL+`"`) {
				t.Fatalf("WWW-Authenticate missing resource metadata: %q", challenge)
			}
			if !strings.Contains(challenge, `scope="mcp.read"`) {
				t.Fatalf("WWW-Authenticate missing required scope: %q", challenge)
			}
		})
	}

	session, _ := connectClient(t, ctx, httpServer.URL, syntheticToken)
	assertProtocol(t, session, modernProtocol)
	result, err := session.CallTool(ctx, &mcp.CallToolParams{Name: "downstream_probe"})
	if err != nil {
		t.Fatalf("authorized CallTool: %v", err)
	}
	if result.IsError {
		t.Fatalf("authorized CallTool returned tool error: %v", result.Content)
	}
	select {
	case got := <-downstreamAuthorization:
		if got != "" {
			t.Fatalf("incoming bearer token was passed downstream: %q", got)
		}
	case <-ctx.Done():
		t.Fatal("downstream probe was not observed")
	}
	resultJSON, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("marshal result: %v", err)
	}
	if bytes.Contains(resultJSON, []byte(syntheticToken)) {
		t.Fatal("bearer token leaked into MCP response")
	}
}

func modernDiscoverRequest(t *testing.T, endpoint string) *http.Response {
	t.Helper()
	body := `{
		"jsonrpc": "2.0",
		"id": 1,
		"method": "server/discover",
		"params": {
			"_meta": {
				"io.modelcontextprotocol/protocolVersion": "2026-07-28",
				"io.modelcontextprotocol/clientCapabilities": {},
				"io.modelcontextprotocol/clientInfo": {"name": "rollback-probe", "version": "1.0.0"}
			}
		}
	}`
	req, err := http.NewRequest(http.MethodPost, endpoint, strings.NewReader(body))
	if err != nil {
		t.Fatalf("NewRequest: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	req.Header.Set("Mcp-Protocol-Version", modernProtocol)
	req.Header.Set("Mcp-Method", "server/discover")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("modern rollback probe: %v", err)
	}
	t.Cleanup(func() {
		if err := resp.Body.Close(); err != nil {
			t.Errorf("rollback response close: %v", err)
		}
	})
	return resp
}

func modernToolsListRequest(t *testing.T, endpoint string) *http.Response {
	t.Helper()
	body := `{
		"jsonrpc": "2.0",
		"id": 2,
		"method": "tools/list",
		"params": {
			"_meta": {
				"io.modelcontextprotocol/protocolVersion": "2026-07-28",
				"io.modelcontextprotocol/clientCapabilities": {},
				"io.modelcontextprotocol/clientInfo": {"name": "rollback-probe", "version": "1.0.0"}
			}
		}
	}`
	req, err := http.NewRequest(http.MethodPost, endpoint, strings.NewReader(body))
	if err != nil {
		t.Fatalf("NewRequest: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	req.Header.Set("Mcp-Protocol-Version", modernProtocol)
	req.Header.Set("Mcp-Method", "tools/list")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("modern tools/list rollback probe: %v", err)
	}
	t.Cleanup(func() {
		if err := resp.Body.Close(); err != nil {
			t.Errorf("rollback tools/list response close: %v", err)
		}
	})
	return resp
}

func TestRollbackSmoke(t *testing.T) {
	ctx := newContext(t)
	server := newServer()
	addSchemaTools(server)
	legacyHTTPServer := newHTTPServer(t, server, false, nil)

	session, _ := connectClient(t, ctx, legacyHTTPServer.URL, "")
	assertProtocol(t, session, legacyProtocol)
	if _, err := session.ListTools(ctx, nil); err != nil {
		t.Fatalf("legacy ListTools after rollback: %v", err)
	}
	result, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name:      "schema_echo",
		Arguments: map[string]any{"query": "rollback", "limit": 1},
	})
	if err != nil {
		t.Fatalf("legacy CallTool after rollback: %v", err)
	}
	if result.IsError {
		t.Fatalf("legacy CallTool returned tool error: %v", result.Content)
	}

	modernResponse := modernDiscoverRequest(t, legacyHTTPServer.URL)
	discoverBody, err := io.ReadAll(modernResponse.Body)
	if err != nil {
		t.Fatalf("read discover response: %v", err)
	}
	var discoverEnvelope struct {
		Result struct {
			SupportedVersions []string `json:"supportedVersions"`
		} `json:"result"`
	}
	if err := json.Unmarshal(discoverBody, &discoverEnvelope); err != nil {
		t.Fatalf("decode discover response: %v; body=%s", err, discoverBody)
	}
	if len(discoverEnvelope.Result.SupportedVersions) == 0 {
		t.Fatalf("legacy discover returned no supportedVersions: %s", discoverBody)
	}
	for _, version := range discoverEnvelope.Result.SupportedVersions {
		if version == modernProtocol {
			t.Fatalf("legacy rollback endpoint still advertises modern protocol: %v",
				discoverEnvelope.Result.SupportedVersions)
		}
	}
	if !contains(discoverEnvelope.Result.SupportedVersions, legacyProtocol) {
		t.Fatalf("legacy rollback endpoint does not advertise %s: %v",
			legacyProtocol, discoverEnvelope.Result.SupportedVersions)
	}

	modernApplicationResponse := modernToolsListRequest(t, legacyHTTPServer.URL)
	applicationBody, err := io.ReadAll(modernApplicationResponse.Body)
	if err != nil {
		t.Fatalf("read modern tools/list response: %v", err)
	}
	if modernApplicationResponse.StatusCode < 200 || modernApplicationResponse.StatusCode >= 300 {
		if !bytes.Contains(applicationBody, []byte(`only supported on stateless HTTP servers`)) {
			t.Fatalf("modern tools/list failed for an unexpected reason: status=%d body=%s",
				modernApplicationResponse.StatusCode, applicationBody)
		}
		return
	}
	var applicationEnvelope map[string]any
	if err := json.Unmarshal(applicationBody, &applicationEnvelope); err != nil {
		t.Fatalf("decode modern tools/list response: %v; body=%s", err, applicationBody)
	}
	if applicationEnvelope["error"] == nil {
		t.Fatalf("legacy rollback endpoint accepted modern tools/list: status=%d body=%s",
			modernApplicationResponse.StatusCode, applicationBody)
	}
}

func contains(values []string, want string) bool {
	for _, value := range values {
		if value == want {
			return true
		}
	}
	return false
}
