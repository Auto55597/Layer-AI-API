from sdk import AgentGuard

API_KEY = "sk-xxxxxxxxxxxxx"
AGENT_ID = "xxxxxxxxxxxxxx"
BASE_URL = "http://127.0.0.1:8000/api"

guard = AgentGuard(
    api_key=API_KEY,
    agent_id=AGENT_ID,
    base_url=BASE_URL
)

guard.check(
    action="xxxxxxx",
    resource="xxxxxxxx"
)

print("Permission approved!")