import chromadb
client = chromadb.PersistentClient(path = "chroma_store")
collection = client.get_or_create_collection("resume")


def chunk_text(text):
    paragraphs = [c.strip() for c in text.split("\n\n") if c.strip()]
    # If the text has few double newlines but many lines (common in PDF extraction)
    if len(paragraphs) <= 1 and len(text) > 300:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        chunks = []
        current = []
        current_len = 0
        for line in lines:
            current.append(line)
            current_len += len(line)
            if current_len >= 250:
                chunks.append(" ".join(current))
                current = []
                current_len = 0
        if current:
            chunks.append(" ".join(current))
        return chunks if chunks else [text.strip()]
    return paragraphs

def index_resume(text):
    chunks = chunk_text(text)
    old_ids = collection.get()["ids"]
    if old_ids:
        collection.delete(ids = old_ids)
    collection.add(
        documents = chunks,
        ids =[f'chunk - {i}' for i in range(len(chunks))]
    )
    return len(chunks)

def search(query,k = 3):
    n = min(k,collection.count())
    if n == 0:
        return []
    res = collection.query(query_texts = [query], n_results = n)
    return [
        {"id":doc_id, "text":doc, "distance":round(dist,4)}
        for doc_id, doc, dist in zip(res["ids"][0], res["documents"][0], res["distances"][0])
    ]
