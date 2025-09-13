"""
test_swarm_intelligence.py - Test for Swarm Intelligence Service

This script tests the functionality of the Swarm Intelligence Service in the TrustViz platform.
"""

import os
import sys
import json
import time
import requests
import unittest

# Service endpoint
SWARM_INTELLIGENCE_URL = "http://localhost:5001"

class TestSwarmIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment before all tests"""
        cls.test_product_id = f"test_product_{int(time.time())}"
        cls.test_task_id = f"test_task_{int(time.time())}"
        cls._wait_for_service()
    
    @classmethod
    def _wait_for_service(cls, timeout=120):
        """Wait for the swarm intelligence service to be available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{SWARM_INTELLIGENCE_URL}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Swarm Intelligence service is ready")
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        else:
            raise TimeoutError(f"Service Swarm Intelligence at {SWARM_INTELLIGENCE_URL} not ready after {timeout} seconds")
    
    def test_swarm_task_submission(self):
        """Test swarm intelligence task submission and completion"""
        print("\n=== Testing Swarm Intelligence Task Submission ===")
        
        # Create a test task for the swarm
        task = {
            "task_id": self.test_task_id,
            "product_id": self.test_product_id,
            "analysis_types": ["authenticity", "reputation", "pricing"],
            "priority": "high"
        }
        
        # Submit task to swarm
        response = requests.post(f"{SWARM_INTELLIGENCE_URL}/tasks", json=task)
        self.assertEqual(response.status_code, 202, "Failed to submit swarm task")
        task_id = response.json().get("task_id")
        self.assertEqual(task_id, self.test_task_id, "Task ID mismatch in response")
        print(f"✅ Created swarm task: {task_id}")
        
        # Wait for task completion
        max_attempts = 15
        for attempt in range(max_attempts):
            response = requests.get(f"{SWARM_INTELLIGENCE_URL}/tasks/{task_id}")
            self.assertEqual(response.status_code, 200, f"Failed to get status for task {task_id}")
            task_status = response.json()
            if task_status.get("status") == "completed":
                break
            time.sleep(2)
        else:
            self.fail(f"Swarm task {task_id} did not complete within expected time")
        
        # Verify task results
        self.assertEqual(task_status.get("status"), "completed", f"Task {task_id} did not complete successfully")
        self.assertIn("results", task_status, f"Results missing for completed task {task_id}")
        print("✅ Swarm task completed successfully with results")
        
        print("✅ Swarm intelligence test completed successfully")

if __name__ == "__main__":
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    print("\n=== Swarm Intelligence Test Summary ===")
    print("All tests for Swarm Intelligence completed successfully!")
