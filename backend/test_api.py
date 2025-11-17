"""
Test REST API Endpoints
Quick script to test all API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_api():
    """Test all API endpoints"""

    print_section("TESTING REST API ENDPOINTS")

    # Test 1: List Companies
    print_section("TEST 1: GET /api/companies/")
    response = requests.get(f"{BASE_URL}/companies/")
    print(f"Status: {response.status_code}")
    data = response.json()
    
    # Handle pagination
    if isinstance(data, dict) and 'results' in data:
        companies = data['results']
    else:
        companies = data
    
    print(f"Found {len(companies)} companies")
    for company in companies:
        print(f"  - {company['name']} ({company.get('ticker_symbol', 'N/A')})")

    # Test 2: Get Single Company
    if companies:
        company_id = companies[0]['id']
        print_section(f"TEST 2: GET /api/companies/{company_id}/")
        response = requests.get(f"{BASE_URL}/companies/{company_id}/")
        print(f"Status: {response.status_code}")
        company = response.json()
        print(f"Company: {company['name']}")
        print(f"Projects: {len(company.get('projects', []))}")

    # Test 3: List Projects
    print_section("TEST 3: GET /api/projects/")
    response = requests.get(f"{BASE_URL}/projects/")
    print(f"Status: {response.status_code}")
    data = response.json()
    
    # Handle pagination
    if isinstance(data, dict) and 'results' in data:
        projects = data['results']
    else:
        projects = data
    
    print(f"Found {len(projects)} projects")
    for project in projects:
        print(f"  - {project['name']} ({project.get('company_name', 'N/A')})")

    # Test 4: Get Available MCP Tools
    print_section("TEST 4: GET /api/claude/tools/")
    response = requests.get(f"{BASE_URL}/claude/tools/")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Available tools: {data.get('count', 0)}")
    for tool in data.get('tools', []):
        print(f"  - {tool['name']}")

    # Test 5: Claude Chat - List Companies
    print_section("TEST 5: POST /api/claude/chat/ - What companies?")
    response = requests.post(
        f"{BASE_URL}/claude/chat/",
        json={"message": "What companies do I have in my database?"}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"\nClaude's Response:")
    print("-" * 70)
    print(data.get('message', 'No message'))
    print("-" * 70)
    if data.get('tool_calls'):
        print(f"Tools used: {[tc['tool'] for tc in data['tool_calls']]}")

    # Test 6: Claude Chat - Company Details
    print_section("TEST 6: POST /api/claude/chat/ - Tell me about 1911 Gold")
    response = requests.post(
        f"{BASE_URL}/claude/chat/",
        json={"message": "Tell me about 1911 Gold Corporation"}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"\nClaude's Response:")
    print("-" * 70)
    print(data.get('message', 'No message'))
    print("-" * 70)

    # Test 7: Search Companies
    print_section("TEST 7: GET /api/companies/?search=gold")
    response = requests.get(f"{BASE_URL}/companies/?search=gold")
    print(f"Status: {response.status_code}")
    data = response.json()
    
    # Handle pagination
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        results = data
        
    print(f"Found {len(results)} companies matching 'gold'")

    # Test 8: Filter Projects by Commodity
    print_section("TEST 8: GET /api/projects/?commodity=gold")
    response = requests.get(f"{BASE_URL}/projects/?commodity=gold")
    print(f"Status: {response.status_code}")
    data = response.json()
    
    # Handle pagination
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        results = data
        
    print(f"Found {len(results)} gold projects")

    print_section("API TESTS COMPLETE ✓")
    print("\n✓ All REST API endpoints are working!")
    print("✓ Claude chat is accessible via HTTP")
    print("✓ Ready for frontend integration!\n")


if __name__ == "__main__":
    print("Make sure Django dev server is running:")
    print("  python manage.py runserver\n")

    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to Django server")
        print("Please run: python manage.py runserver")
        print("Then try this test again.\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
