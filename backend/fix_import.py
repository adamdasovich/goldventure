# Quick fix for missing import
with open('mcp_servers/mining_data.py', 'r') as f:
    content = f.read()

# Add the missing import
content = content.replace(
    'from .base import BaseMCPServer',
    'from typing import Dict, List, Any\nfrom .base import BaseMCPServer'
)

with open('mcp_servers/mining_data.py', 'w') as f:
    f.write(content)

print("✓ Fixed: Added typing imports to mining_data.py")
