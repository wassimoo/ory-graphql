from flask import Flask, request, jsonify
from ariadne import (
    QueryType,
    MutationType,
    make_executable_schema,
    graphql_sync,
    load_schema_from_path,
)
from ariadne.explorer import ExplorerPlayground
import requests

app = Flask(__name__)
query = QueryType()
mutation = MutationType()
explorer = ExplorerPlayground()

KRATOS_PUBLIC_URL = "http://localhost:4433"
KRATOS_ADMIN_URL = "http://localhost:4434/admin"


def get_kratos_session(token):
    headers = {"X-Session-Token": token}
    resp = requests.get(f"{KRATOS_PUBLIC_URL}/sessions/whoami", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return None


# --- Query Resolvers ---
@query.field("hello")
def resolve_hello(*_):
    return "Hello, world!"


@query.field("me")
def resolve_me(*_):
    token = request.headers.get("X-Session-Token")
    session = get_kratos_session(token)
    if not session:
        return "Unauthorized"
    return session["identity"]["traits"]["email"]


# --- Mutation Resolvers ---
@mutation.field("registerUser")
def resolve_register_user(_, info, email, password):
    """Register a new user using Kratos admin API"""
    try:
        payload = {
            "schema_id": "default",
            "traits": {"email": email},
            "credentials": {"password": {"config": {"password": password}}},
        }
        resp = requests.post(f"{KRATOS_ADMIN_URL}/identities", json=payload)
        if resp.status_code in (200, 201):
            return f"User {email} registered successfully"
        return f"Registration failed: {resp.text}"
    except Exception as exc:
        return f"Registration failed: {exc}"


@mutation.field("login")
def resolve_login(_, info, identifier, password):
    """Login via Kratos self-service flow and return session token + email"""
    # 1) Create login flow
    flow_resp = requests.get(f"{KRATOS_PUBLIC_URL}/self-service/login/api")
    if flow_resp.status_code != 200:
        raise Exception(f"Failed to init login flow: {flow_resp.text}")
    flow_id = flow_resp.json().get("id")
    if not flow_id:
        raise Exception("Login flow id missing")

    # 2) Submit credentials
    submit_resp = requests.post(
        f"{KRATOS_PUBLIC_URL}/self-service/login?flow={flow_id}",
        json={
            "method": "password",
            "identifier": identifier,
            "password": password,
        },
    )

    if submit_resp.status_code != 200:
        try:
            details = submit_resp.json()
        except Exception:
            details = {"raw": submit_resp.text}
        raise Exception(f"Invalid credentials: {details}")

    payload = submit_resp.json()
    token = payload.get("session_token")
    session = payload.get("session") or {}
    identity_email = ((session.get("identity") or {}).get("traits") or {}).get(
        "email"
    ) or ""

    if not token:
        raise Exception("No session token returned")

    return {"sessionToken": token, "identityEmail": identity_email}


# --- Schema ---
schema = make_executable_schema(load_schema_from_path("schema"), query, mutation)


# --- GraphQL Endpoint ---
@app.route("/graphql", methods=["GET", "POST"])
def graphql_endpoint():
    if request.method == "GET":
        return explorer.html(request)
    success, result = graphql_sync(schema, request.get_json(), context_value=request)
    return jsonify(result)


if __name__ == "__main__":
    app.run(port=8000)
