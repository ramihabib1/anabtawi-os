import time
from datetime import datetime, timedelta, timezone

from anthropic import Anthropic
from core.supabase_client import get_supabase
from core.mem0_client import get_memory


class BaseAgent:
    """Shared infrastructure for all agents."""

    def __init__(self, agent_name: str, domain: str):
        self.agent_name = agent_name
        self.domain = domain
        self.run_id = (
            f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}_{agent_name}"
        )
        self.supabase = get_supabase()
        self.memory = get_memory()
        self.anthropic = Anthropic()

    def run(self):
        """Main execution flow for every agent."""
        start_time = time.time()
        success = True
        error_message = None
        output_summary = ""

        try:
            print(f"[{self.run_id}] Fetching data...")
            data = self.fetch_data()

            print(f"[{self.run_id}] Fetching memories...")
            memories = self.fetch_memories()

            print(f"[{self.run_id}] Calling Claude...")
            response = self.analyze(data, memories)

            print(f"[{self.run_id}] Processing response...")
            output_summary = self.process_response(response)

            print(f"[{self.run_id}] Writing observations to Mem0...")
            self.write_observations(response)

        except Exception as e:
            success = False
            error_message = str(e)
            print(f"[{self.run_id}] FAILED: {e}")
            self.send_failure_alert(e)

        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_run(success, error_message, output_summary, duration_ms)
            print(
                f"[{self.run_id}] Done in {duration_ms}ms. "
                f"Success={success}. {output_summary}"
            )

        return output_summary

    def fetch_data(self) -> dict:
        raise NotImplementedError

    def fetch_memories(self) -> list:
        """Retrieve relevant memories from Mem0. Returns [] if Mem0 unavailable."""
        if self.memory is None:
            return []

        results = []
        try:
            high_value = self.memory.search(
                query=f"{self.domain} patterns strategies insights",
                user_id="habib_distribution",
                limit=15,
                filters={"memory_type": {"in": ["pattern", "playbook"]}},
            )
            results.extend(high_value.get("results", []))
        except Exception as e:
            print(f"[{self.run_id}] Mem0 pattern search skipped: {e}")

        try:
            recent = self.memory.search(
                query=f"recent {self.domain} observations",
                user_id="habib_distribution",
                limit=10,
                filters={"memory_type": "observation"},
            )
            results.extend(recent.get("results", []))
        except Exception as e:
            print(f"[{self.run_id}] Mem0 observation search skipped: {e}")

        return results

    def analyze(self, data: dict, memories: list) -> dict:
        raise NotImplementedError

    def process_response(self, response: dict) -> str:
        raise NotImplementedError

    def write_observations(self, response: dict):
        """Write agent observations to Mem0. Skips if Mem0 unavailable."""
        if self.memory is None:
            obs_count = len(response.get("observations", []))
            if obs_count:
                print(f"[{self.run_id}] Mem0 unavailable — skipping {obs_count} observations.")
            return

        observations = response.get("observations", [])
        if not observations:
            return

        now = datetime.now(timezone.utc).isoformat()
        for obs in observations:
            try:
                self.memory.add(
                    messages=[{"role": "user", "content": obs["text"]}],
                    user_id="habib_distribution",
                    metadata={
                        "agent": self.agent_name,
                        "memory_type": "observation",
                        "product_ids": obs.get("product_ids", []),
                        "campaign_ids": obs.get("campaign_ids", []),
                        "competitor_asins": obs.get("competitor_asins", []),
                        "confidence": obs.get("confidence", 0.6),
                        "domain": self.domain,
                        "source_run_id": self.run_id,
                        "created_date": now,
                        "last_reinforced": now,
                        "reinforcement_count": 1,
                        "outcome_validated": False,
                    },
                )
            except Exception as e:
                print(f"[{self.run_id}] Failed to write observation to Mem0: {e}")

    def create_approval_request(
        self,
        action_type: str,
        description: str,
        payload: dict,
        estimated_cost: float = None,
    ):
        """Create an approval request for a financial action."""
        expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=24)
        ).isoformat()
        self.supabase.table("approval_requests").insert(
            {
                "action_type": action_type,
                "agent": self.agent_name,
                "description": description,
                "payload": payload,
                "estimated_cost": estimated_cost,
                "status": "pending",
                "expires_at": expires_at,
            }
        ).execute()

    def create_notification(
        self,
        severity: str,
        title: str,
        body: str,
        product_id: str = None,
        metadata: dict = None,
    ):
        """Create a notification for the dashboard/Telegram."""
        self.supabase.table("notifications").insert(
            {
                "agent": self.agent_name,
                "severity": severity,
                "title": title,
                "body": body,
                "status": "unread",
                "product_id": product_id,
                "metadata": metadata or {},
            }
        ).execute()

    def log_run(
        self,
        success: bool,
        error_message: str,
        output_summary: str,
        duration_ms: int,
    ):
        """Log agent run to agent_runs table."""
        try:
            self.supabase.table("agent_runs").insert(
                {
                    "agent": self.agent_name,
                    "task": f"{self.agent_name}_daily_{self.domain}",
                    "trigger_type": "scheduled",
                    "input_summary": f"Analyzed {self.domain} data",
                    "output_summary": output_summary[:1000] if output_summary else None,
                    "duration_ms": duration_ms,
                    "success": success,
                    "error_message": error_message[:500] if error_message else None,
                }
            ).execute()
        except Exception as e:
            print(f"[{self.run_id}] Failed to log run: {e}")

    def send_failure_alert(self, error: Exception):
        """Send critical notification on agent failure."""
        try:
            self.supabase.table("notifications").insert({
                "agent": self.agent_name,
                "severity": "critical",
                "title": f"{self.agent_name} failed",
                "body": f"Error: {str(error)[:500]}. Will retry in 30 minutes.",
                "status": "unread",
            }).execute()
        except Exception as e:
            print(f"[{self.run_id}] Could not send failure alert: {e}")
