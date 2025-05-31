import subprocess
import sys
import time
import requests

# Test configuration
API_CONFIG = {
    "ingestion_base_url": "http://localhost:8000/api/v1",
    "alerting_base_url": "http://localhost:8001/api/v1", 
    "timeout": 30
}

def wait_for_service(url: str, timeout: int = 60) -> bool:
    """Wait for service to be available"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url.replace('/api/v1', '')}/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    
    return False

def main():
    """Run E2E tests"""
    print("Starting IoT System E2E Tests")
    
    # Wait for services
    print("Waiting for services to be ready...")
    if not wait_for_service(API_CONFIG["ingestion_base_url"]):
        print("ERROR: Ingestion service not available")
        sys.exit(1)
        
    if not wait_for_service(API_CONFIG["alerting_base_url"]):
        print("ERROR: Alerting service not available") 
        sys.exit(1)
    
    print("Services are ready!")
    
    # Run tests
    print("Running tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_iot_system.py", 
        "-v", 
        "--tb=short"
    ])
    
    if result.returncode == 0:
        print("All tests passed!")
    else:
        print("Some tests failed!")
        
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
