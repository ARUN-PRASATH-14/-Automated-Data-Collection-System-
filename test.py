from supabase_client import supabase

# Fetch limited columns and records
response = supabase.table("articles").select("id, title, source").limit(5).execute()

print(f"Total articles retrieved: {len(response.data)}")
for i, item in enumerate(response.data):
    # Safe console printing by stripping non-ascii characters
    title_safe = item['title'].encode('ascii', 'ignore').decode('ascii')
    print(f"{i + 1}. [{item['source']}] {title_safe}")
