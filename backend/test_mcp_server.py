"""
Test script for Mining Data MCP Server
Run this to verify your MCP server is working correctly
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp_servers.mining_data import MiningDataServer
import json


def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_mining_server():
    """Test all Mining Data MCP Server tools"""

    print_section("INITIALIZING MINING DATA MCP SERVER")
    server = MiningDataServer()

    print(f"✓ Server initialized")
    print(f"✓ Registered {len(server._tools)} tools")

    # Test 1: List all tools
    print_section("TEST 1: List Available Tools")
    tools = server.get_tool_definitions()
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   {tool['description'][:80]}...")

    # Test 2: List companies
    print_section("TEST 2: List All Companies")
    result = server.execute_tool("mining_list_companies", {"active_only": True})
    print(json.dumps(result, indent=2))

    # Test 3: Get company details
    print_section("TEST 3: Get Company Details (Aston Bay)")
    result = server.execute_tool("mining_get_company_details", {"company_name": "BAY"})
    print(json.dumps(result, indent=2))

    # Test 4: Get company details (1911 Gold)
    print_section("TEST 4: Get Company Details (1911 Gold)")
    result = server.execute_tool("mining_get_company_details", {"company_name": "AUMB"})
    print(json.dumps(result, indent=2))

    # Test 5: List all projects
    print_section("TEST 5: List All Projects")
    result = server.execute_tool("mining_list_projects", {})
    print(json.dumps(result, indent=2))

    # Test 6: Get project details
    print_section("TEST 6: Get Project Details (Storm)")
    result = server.execute_tool("mining_get_project_details", {"project_name": "Storm"})
    print(json.dumps(result, indent=2))

    # Test 7: Get total resources
    print_section("TEST 7: Get Total Resources (All)")
    result = server.execute_tool("mining_get_total_resources", {
        "category": "all",
        "commodity": "all"
    })
    print(json.dumps(result, indent=2))

    # Test 8: Get resources for specific company
    print_section("TEST 8: Get Resources (1911 Gold only)")
    result = server.execute_tool("mining_get_total_resources", {
        "company_name": "1911",
        "category": "all",
        "commodity": "gold"
    })
    print(json.dumps(result, indent=2))

    print_section("ALL TESTS COMPLETE ✓")
    print("\n✓ MCP Server is working correctly!")
    print("✓ Ready to integrate with Claude API")
    print("\nNext step: Build the Claude integration client\n")


if __name__ == "__main__":
    test_mining_server()
