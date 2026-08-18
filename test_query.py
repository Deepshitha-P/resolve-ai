import duckdb
import textwrap

con = duckdb.connect()
import spacy
nlp = spacy.load('en_core_web_sm')
print('Loaded spacy')
rel = con.sql("SELECT text FROM 'data/knowledge/conversations/conversations.parquet' LIMIT 200")
print("=== REGION TAGGING SPOT-CHECK ===")
for r in rel.fetchall():
    doc = nlp(r[0])
    for ent in doc.ents:
        if ent.label_ == 'GPE':
            print(f"[{ent.text}] -> {textwrap.shorten(r[0].replace(chr(10), ' '), width=80)}")
