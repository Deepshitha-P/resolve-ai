"""
Check conversation IDs and parquet data.
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'c:\Users\indhu\Downloads\Resolve-AI (2)\Resolve-AI\Resolve-AI'

# Check JSON conversations
with open(os.path.join(ROOT, 'outputs/03_conversations.json'), 'r', encoding='utf-8') as f:
    convs = json.load(f)

print(f'Total conversations in JSON: {len(convs)}')
all_ids = [c.get('conversation_id') for c in convs[:20]]
print(f'First 20 conv IDs: {all_ids}')

first = convs[0]
print(f'First conv keys: {list(first.keys())}')

# Check parquet data
try:
    import duckdb
    conv_parquet = os.path.join(ROOT, 'data/conversations/conversations.parquet')
    if os.path.exists(conv_parquet):
        con = duckdb.connect()
        cnt = con.execute(f"SELECT count(*) FROM '{conv_parquet}'").fetchone()[0]
        print(f'\nParquet conversations count: {cnt}')
        # Sample IDs
        sample = con.execute(f"SELECT conversation_id FROM '{conv_parquet}' LIMIT 20").fetchall()
        print(f'Sample parquet IDs: {[r[0] for r in sample]}')
        
        # Check if cluster reps exist in parquet
        for cid in ['CONV-284', 'CONV-242', 'CONV-785']:
            exists = con.execute(f"SELECT count(*) FROM '{conv_parquet}' WHERE conversation_id='{cid}'").fetchone()[0]
            print(f'  {cid} in parquet: {exists}')
    else:
        print(f'Parquet not found at: {conv_parquet}')
        # List parquet files
        conv_dir = os.path.join(ROOT, 'data/conversations')
        print(f'Files in data/conversations: {os.listdir(conv_dir) if os.path.exists(conv_dir) else "dir not found"}')
except Exception as e:
    print(f'DuckDB error: {e}')

# Check parquet raw cases
try:
    raw_parquet = os.path.join(ROOT, 'data/parquet/raw_cases.parquet')
    if os.path.exists(raw_parquet):
        import duckdb
        con = duckdb.connect()
        cnt = con.execute(f"SELECT count(*) FROM '{raw_parquet}'").fetchone()[0]
        print(f'\nRaw parquet count: {cnt}')
        # Get product distribution
        prod_dist = con.execute(f"""
            SELECT COALESCE(product, '__NULL__') as prod, count(*) as cnt 
            FROM '{raw_parquet}' 
            GROUP BY prod 
            ORDER BY cnt DESC 
            LIMIT 20
        """).fetchall()
        print('Product distribution in raw_cases.parquet:')
        for row in prod_dist:
            print(f'  {row[0]}: {row[1]}')
except Exception as e:
    print(f'Raw parquet error: {e}')
