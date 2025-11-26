"""
Debug document classification
"""

# Test URL from crawler output
test_url = "https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf?v=111911"
test_link_text = ""  # Empty link text from crawler

combined_text = (test_link_text + ' ' + test_url).lower()

print("Combined text:", combined_text)
print()

# Test each pattern
patterns = {
    'ni43101': ['ni 43-101', 'ni43-101', 'ni43101', '43-101', 'technical-report'],
    'presentation': ['presentation', 'corporate-presentation', '/presentations/'],
    'financial': ['financial', 'annual-report', 'quarterly', '/financial'],
    'news': ['/news/', 'nr-', 'press-release']
}

for doc_type, keywords in patterns.items():
    matches = [kw for kw in keywords if kw in combined_text]
    if matches:
        print(f"{doc_type}: MATCHED - {matches}")
    else:
        print(f"{doc_type}: no match")
