import sys
import time
import requests

def run_tests(alb_dns):
    base_url = f"http://{alb_dns}"
    print(f"Starting integration tests against: {base_url}")
    
    # 1. Warm-up poll loop (wait for EC2 user data to finish and ALB targets to become healthy)
    max_retries = 30
    retry_interval = 10
    healthy = False
    
    print("Waiting for application to become healthy (polling /health)...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print(f"Application is healthy on try {i+1}!")
                    healthy = True
                    break
            print(f"[/] Poll {i+1}/{max_retries}: Status code {response.status_code}. Waiting...")
        except requests.exceptions.RequestException as e:
            print(f"[/] Poll {i+1}/{max_retries}: Connection pending... ({e})")
        time.sleep(retry_interval)
        
    if not healthy:
        print("[!] Error: Application did not become healthy within the timeout period.")
        sys.exit(1)

    print("\n--- Test 1: Verify DB Status and SSL Encryption ---")
    status_resp = requests.get(f"{base_url}/api/db-status")
    assert status_resp.status_code == 200, "DB Status API failed"
    status_data = status_resp.json()
    print("Database Status Response:")
    for k, v in status_data.items():
        if "password" not in k.lower():
            print(f"  {k}: {v}")
            
    assert status_data.get("primary_configured") is True, "Primary DB not configured"
    assert status_data.get("replica_configured") is True, "Replica DB not configured"
    assert status_data.get("primary_ssl_active") is True, "SSL not active on Primary DB!"
    assert status_data.get("replica_ssl_active") is True, "SSL not active on Replica DB!"
    print("[x] Test 1 Passed: Both nodes are configured and enforcing SSL encryption in-transit!")

    print("\n--- Test 2: Verify Inventory Reading (Primary DB) ---")
    get_resp = requests.get(f"{base_url}/api/items")
    assert get_resp.status_code == 200, "Get Items API failed"
    get_data = get_resp.json()
    assert get_data.get("source") == "Primary Database", "Incorrect data source for transactional read"
    items = get_data.get("items", [])
    print(f"Found {len(items)} items in the database.")
    print("[x] Test 2 Passed: Successfully read inventory records from the Primary DB.")

    print("\n--- Test 3: Verify Inventory Writing (Primary DB) ---")
    new_item = {
        "name": "Integration Test Router",
        "description": "Enterprise router added during automated integration testing run.",
        "price": 1850.75,
        "quantity": 4
    }
    post_resp = requests.post(f"{base_url}/api/items", json=new_item)
    assert post_resp.status_code == 201, "Post Item API failed"
    post_data = post_resp.json()
    assert post_data.get("source") == "Primary Database", "Incorrect data source for transactional write"
    created_item = post_data.get("item", {})
    assert created_item.get("name") == new_item["name"], "Item name mismatch"
    print(f"Successfully created item. ID: {created_item.get('id')}")
    print("[x] Test 3 Passed: Successfully wrote new asset record and audit log to the Primary DB.")

    print("\n--- Test 4: Verify Complex Analytics Query (Read Replica) ---")
    report_resp = requests.get(f"{base_url}/api/report")
    assert report_resp.status_code == 200, "Get Report API failed"
    report_data = report_resp.json()
    assert report_data.get("source") == "Read Replica Database", "Incorrect data source for reporting query"
    reports = report_data.get("report", [])
    print(f"Generated {len(reports)} aggregate report rows from the Read Replica.")
    
    # Check if our new item exists in the replica report (asynchronous replication check)
    found_in_report = False
    for r in reports:
        if r.get("name") == new_item["name"]:
            found_in_report = True
            print(f"Found replica record for '{new_item['name']}':")
            print(f"  Actions Logged: {r.get('action_count')}")
            print(f"  Avg Asset Price: ${r.get('avg_price')}")
            print(f"  Total Inventory Value: ${r.get('inventory_value')}")
            break
            
    if not found_in_report:
        print("[!] Note: Newly added item not immediately in replica report. Retrying in 5 seconds (asynchronous replication sync lag)...")
        time.sleep(5)
        report_resp = requests.get(f"{base_url}/api/report")
        reports = report_resp.json().get("report", [])
        for r in reports:
            if r.get("name") == new_item["name"]:
                found_in_report = True
                print(f"Found replica record after sync retry: {r}")
                break
                
    assert found_in_report, "New item was not found in read replica report!"
    print("[x] Test 4 Passed: Complex join and aggregation queries successfully routed to the Read Replica node!")

    print("\n=============================================")
    print("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=============================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 integration_test.py <ALB_DNS_NAME>")
        sys.exit(1)
    run_tests(sys.argv[1])
