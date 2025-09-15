## Ory Kratos + Flask GraphQL Demo

Demo repository accompanying the blog post “Building a Secure GraphQL API with Ory Kratos.” See the article for background and concepts: [Blog post](https://wassim.bougarfa.com/blogs/cloud-native-dev).

### What this repo contains

- Flask + Ariadne GraphQL server exposing:
  - `hello` public query
  - `registerUser(email, password)` mutation (creates identity via Kratos Admin API)
  - `login(identifier, password)` mutation (returns `sessionToken`)
  - `me` query protected by `X-Session-Token` header (validates with Kratos `whoami`)
- Local Ory Kratos via Docker Compose with minimal dev config
- GraphQL SDL in `schema/schema.graphql`

### Prerequisites

- Docker and Docker Compose
- Python 3.13 (repo includes a ready-to-use virtualenv under `env/`)

### Quick start

1. Start Ory Kratos

```bash
docker compose up -d

# verify health
curl -s http://localhost:4433/health/ready | jq .
```

2. Install Python dependencies

```bash
# Option A: use the provided venv directly
./env/bin/pip install -U pip
./env/bin/pip install -r <(cat <<'REQ'
Flask==3.1.2
ariadne==0.26.2
requests==2.32.5
python-dotenv==1.1.1
REQ
)

# Option B: create your own venv
# python3 -m venv .venv && source .venv/bin/activate
# pip install Flask==3.1.2 ariadne==0.26.2 requests==2.32.5 python-dotenv==1.1.1
```

3. Run the GraphQL server

```bash
./env/bin/python server.py
# server listens on http://localhost:8000/graphql
```

### Trying it out

Open the GraphQL Explorer at `http://localhost:8000/graphql` or use `curl`.

1. Public hello

```graphql
query {
  hello
}
```

2. Register a user (via Kratos Admin API)

```graphql
mutation {
  registerUser(email: "alice@example.com", password: "secret")
}
```

3. Login to obtain a session token

```graphql
mutation {
  login(identifier: "alice@example.com", password: "secret") {
    sessionToken
    identityEmail
  }
}
```

Copy the returned `sessionToken`.

4. Call protected `me` with `X-Session-Token`

Using the Explorer, add a header:

```json
{ "X-Session-Token": "<paste-session-token>" }
```

Then run:

```graphql
query {
  me
}
```

Or with curl:

```bash
curl -s \
  -H 'Content-Type: application/json' \
  -H 'X-Session-Token: <paste-session-token>' \
  -d '{"query":"query{ me }"}' \
  http://localhost:8000/graphql | jq .
```

### Configuration

Defaults (as used in `server.py`):

- `KRATOS_PUBLIC_URL`: `http://localhost:4433`
- `KRATOS_ADMIN_URL`: `http://localhost:4434/admin`

These match the compose file. If you change ports or hostnames, update the constants in `server.py` accordingly.

### Security notes

- Dev-only settings. Do not expose Kratos Admin API publicly in production.
- Treat `sessionToken` as sensitive. Prefer secure, HTTP-only cookies and HTTPS.
- Rotate secrets and configure proper session TTLs for real deployments.

### Troubleshooting

- If `login` fails, confirm Kratos is healthy: `curl -s http://localhost:4433/health/ready`.
- If `me` returns `Unauthorized`, ensure you pass a fresh `X-Session-Token` header.

### Credit

This demo accompanies the blog post by Wassim Bougarfa: [Building a Secure GraphQL API with Ory Kratos](https://wassim.bougarfa.com/blogs/cloud-native-dev).
