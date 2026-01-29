"""
SDK Usage Example
Demonstrates how to use the AI Agent SDK in a production-like scenario.
"""
import logging
import sys
import os
import time

# Add parent directory to path so we can import sdk package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk import AgentConfig, AgentClient, ActionRunner, SDKError, ConnectionError
# We won't import DB models here to keep SDK usage clean and decoupled from backend code in this demo
# usage script should run as a "client".

# Setup Logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("sdk_demo")

def real_business_logic():
    """Simulate actual work"""
    return "Data from critical database"

def main():
    # 1. Initialize SDK
    # In production, load API key from env var
    logger.info("Initializing SDK Client...")
    config = AgentConfig(
        base_url="http://localhost:8000/api",
        api_key="dev-key-12345",
        timeout=5.0,
        retries=1 # Fail fast for demo
    )
    client = AgentClient(config)
    runner = ActionRunner(client)
    
    logger.info("------------------------------------------------")
    logger.info("Scenario 1: Approved Action")
    logger.info("------------------------------------------------")
    
    try:
        # Execute an action that is ALLOWED
        # Note: Ideally this relies on a running server.
        result = runner.execute(
            agent_id="sdk-demo-agent",
            action="read",
            resource="test_db",
            executor_func=real_business_logic
        )
        logger.info(f"SUCCESS: Operation result: {result}")
        
    except ConnectionError:
        logger.error("Could not connect to API. Is the server running? (uvicorn main:app)")
    except SDKError as e:
        logger.error(f"FAILURE: {e}")

    logger.info("\n------------------------------------------------")
    logger.info("Scenario 2: Denied Action")
    logger.info("------------------------------------------------")
    
    try:
        # Execute an action that is DENIED (no permission for 'write')
        runner.execute(
            agent_id="sdk-demo-agent",
            action="write",
            resource="test_db",
            executor_func=lambda: "This should not happen"
        )
    except ConnectionError:
        logger.error("Could not connect to API.")
    except SDKError as e:
        logger.info(f"EXPECTED FAILURE: Caught SDKError as expected: {e}")

if __name__ == "__main__":
    main()
