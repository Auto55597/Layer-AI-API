import requests


class AgentGuard:
    def __init__(self, api_key: str, agent_id: str, base_url: str):
        self.api_key = api_key
        self.agent_id = agent_id
        self.base_url = base_url.rstrip("/")

    def check(self, action: str, resource: str):
        url = f"{self.base_url}/agent/request"

        payload = {
            "agent_id": self.agent_id,
            "action": action,
            "resource": resource
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=5
            )
        except Exception as e:
            raise RuntimeError(f"Permission service unreachable: {e}")

        if response.status_code != 200:
            raise RuntimeError(f"Permission check failed: {response.text}")

        data = response.json()

        if data.get("result") != "approved":
            raise PermissionError({
                "message": data.get("message"),
                "reason": data.get("reason"),
                "decision_trace": data.get("decision_trace")
            })

        return True