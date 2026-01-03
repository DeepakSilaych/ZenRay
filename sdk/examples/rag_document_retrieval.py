#!/usr/bin/env python3
"""
RAG Document Retrieval Pipeline

A comprehensive Retrieval-Augmented Generation pipeline with:
- 200+ documents across multiple domains
- Vector similarity search
- Reranking with cross-encoder simulation
- Context window optimization
- LLM response generation with citations

Run: python examples/rag_document_retrieval.py
"""
import xray
import random
import math
import hashlib
from datetime import datetime, timedelta

xray.init()

# =============================================================================
# DATASET: 200+ Documents
# =============================================================================

DOMAINS = {
    "technology": {
        "topics": ["AI", "Machine Learning", "Cloud Computing", "Cybersecurity", "Blockchain", "IoT", "5G", "Quantum Computing"],
        "sources": ["TechCrunch", "Wired", "MIT Tech Review", "IEEE", "ArXiv"],
    },
    "healthcare": {
        "topics": ["Drug Discovery", "Clinical Trials", "Medical Imaging", "Telemedicine", "Genomics", "Mental Health", "Vaccination"],
        "sources": ["Nature Medicine", "NEJM", "Lancet", "JAMA", "BMJ"],
    },
    "finance": {
        "topics": ["Cryptocurrency", "Stock Market", "Banking", "Insurance", "Fintech", "Regulations", "ESG Investing"],
        "sources": ["Bloomberg", "Reuters", "Financial Times", "WSJ", "Forbes"],
    },
    "science": {
        "topics": ["Climate Change", "Space Exploration", "Renewable Energy", "Biodiversity", "Particle Physics", "Neuroscience"],
        "sources": ["Nature", "Science", "Scientific American", "NASA", "CERN"],
    },
    "legal": {
        "topics": ["Data Privacy", "Intellectual Property", "Antitrust", "Employment Law", "GDPR", "Contract Law"],
        "sources": ["Harvard Law Review", "Yale Law Journal", "Supreme Court", "EU Commission"],
    },
}

CONTENT_TEMPLATES = [
    "Recent advances in {topic} have shown promising results. Researchers at {source} published findings indicating that {finding}. This has implications for {implication}.",
    "The {topic} landscape is evolving rapidly. According to {source}, {finding}. Industry experts predict {prediction}.",
    "A comprehensive study on {topic} reveals {finding}. Published by {source}, the research highlights {highlight}. Future directions include {future}.",
    "Breaking developments in {topic}: {source} reports that {finding}. This could lead to {outcome}.",
    "{topic} continues to transform industries. Analysis from {source} shows {finding}. Key stakeholders are {action}.",
]

FINDINGS = [
    "significant improvements in efficiency",
    "unexpected correlations in the data",
    "new methodologies outperforming existing approaches",
    "regulatory challenges that need addressing",
    "cost reductions of up to 40%",
    "scalability issues in current implementations",
    "promising results in early trials",
    "integration challenges with legacy systems",
]


def generate_documents(count: int = 200) -> list[dict]:
    """Generate a corpus of documents."""
    documents = []
    
    for i in range(count):
        domain = random.choice(list(DOMAINS.keys()))
        domain_info = DOMAINS[domain]
        topic = random.choice(domain_info["topics"])
        source = random.choice(domain_info["sources"])
        
        # Generate content
        template = random.choice(CONTENT_TEMPLATES)
        content = template.format(
            topic=topic,
            source=source,
            finding=random.choice(FINDINGS),
            implication=f"the broader {domain} sector",
            prediction=f"continued growth in {topic.lower()} adoption",
            highlight=f"key challenges in {topic.lower()} implementation",
            future=f"expanding {topic.lower()} applications",
            outcome=f"major shifts in {domain} practices",
            action=f"evaluating {topic.lower()} strategies",
        )
        
        # Add more paragraphs for longer documents
        for _ in range(random.randint(1, 3)):
            extra_template = random.choice(CONTENT_TEMPLATES)
            content += " " + extra_template.format(
                topic=topic,
                source=source,
                finding=random.choice(FINDINGS),
                implication=f"industry standards",
                prediction=f"widespread adoption by 2026",
                highlight=f"emerging trends",
                future=f"next-generation solutions",
                outcome=f"competitive advantages",
                action=f"investing in innovation",
            )
        
        # Generate embedding (simplified)
        embedding = [random.gauss(0, 1) for _ in range(384)]
        
        # Metadata
        days_old = random.randint(1, 365)
        created_at = datetime.now() - timedelta(days=days_old)
        
        doc_id = hashlib.md5(f"{domain}-{topic}-{i}".encode()).hexdigest()[:12]
        
        documents.append({
            "id": f"DOC-{doc_id}",
            "title": f"{topic}: {random.choice(['Analysis', 'Overview', 'Deep Dive', 'Report', 'Study'])} by {source}",
            "content": content,
            "domain": domain,
            "topic": topic,
            "source": source,
            "created_at": created_at.isoformat(),
            "word_count": len(content.split()),
            "embedding": embedding,
            "citation_count": random.randint(0, 500),
            "quality_score": round(random.uniform(0.5, 1.0), 2),
        })
    
    return documents


# Generate corpus
DOCUMENTS = generate_documents(200)
print(f"Generated {len(DOCUMENTS)} documents")


# =============================================================================
# QUERY TYPES
# =============================================================================

SAMPLE_QUERIES = [
    # Technology
    {"query": "What are the latest developments in quantum computing?", "domain_hint": "technology"},
    {"query": "How is AI being used in cybersecurity?", "domain_hint": "technology"},
    {"query": "Explain the impact of 5G on IoT devices", "domain_hint": "technology"},
    
    # Healthcare
    {"query": "What are the recent advances in drug discovery using AI?", "domain_hint": "healthcare"},
    {"query": "How effective are telemedicine platforms?", "domain_hint": "healthcare"},
    {"query": "Latest research on mental health treatments", "domain_hint": "healthcare"},
    
    # Finance
    {"query": "How is blockchain changing the banking industry?", "domain_hint": "finance"},
    {"query": "What are ESG investing trends?", "domain_hint": "finance"},
    {"query": "Cryptocurrency regulation updates", "domain_hint": "finance"},
    
    # Science
    {"query": "Recent findings on climate change mitigation", "domain_hint": "science"},
    {"query": "Progress in space exploration missions", "domain_hint": "science"},
    {"query": "Advances in renewable energy technology", "domain_hint": "science"},
    
    # Legal
    {"query": "GDPR compliance requirements for AI systems", "domain_hint": "legal"},
    {"query": "Recent antitrust cases in tech industry", "domain_hint": "legal"},
    {"query": "Data privacy laws comparison", "domain_hint": "legal"},
]


# =============================================================================
# RAG PIPELINE
# =============================================================================

@xray.pipeline("rag-document-qa", version="v3.0.0")
def answer_question(query: str, max_context_tokens: int = 2000) -> dict:
    """
    Full RAG pipeline for document Q&A.
    
    Stages:
    1. Embed query
    2. Vector search (retrieve top-100)
    3. Rerank with cross-encoder
    4. Filter low-quality docs
    5. Optimize context window
    6. Generate response with LLM
    """
    xray.tag("query_type", classify_query(query))
    xray.tag("max_tokens", str(max_context_tokens))
    
    # Embed the query
    query_embedding = embed_query(query)
    
    # Retrieve candidates
    candidates = vector_search(query_embedding, top_k=100)
    
    # Rerank
    reranked = rerank_documents(candidates, query)
    
    # Filter
    filtered = filter_low_quality(reranked)
    
    # Optimize context
    context_docs = optimize_context(filtered, max_context_tokens)
    
    # Generate response
    response = generate_response(query, context_docs)
    
    return response


def classify_query(query: str) -> str:
    """Simple query classification."""
    query_lower = query.lower()
    for domain in DOMAINS:
        if domain in query_lower:
            return domain
        for topic in DOMAINS[domain]["topics"]:
            if topic.lower() in query_lower:
                return domain
    return "general"


@xray.step("LLM_CALL")
def embed_query(query: str) -> list[float]:
    """Embed the query using an embedding model."""
    xray.artifact("input", {"query": query})
    xray.metric("model", "text-embedding-3-large")
    xray.metric("dimensions", 384)
    
    # Simulate embedding (in reality, call OpenAI/Cohere/etc.)
    embedding = [random.gauss(0, 1) for _ in range(384)]
    
    xray.artifact("output", {"embedding_norm": sum(e*e for e in embedding)**0.5})
    
    return embedding


@xray.step("RETRIEVE")
def vector_search(query_embedding: list[float], top_k: int = 100) -> list[dict]:
    """Search documents using vector similarity."""
    xray.metric("index_size", len(DOCUMENTS))
    xray.metric("top_k", top_k)
    
    # Calculate similarity scores
    scored_docs = []
    for doc in DOCUMENTS:
        # Cosine similarity (simplified)
        similarity = sum(q * d for q, d in zip(query_embedding, doc["embedding"]))
        norm_q = sum(e*e for e in query_embedding) ** 0.5
        norm_d = sum(e*e for e in doc["embedding"]) ** 0.5
        
        if norm_q > 0 and norm_d > 0:
            similarity /= (norm_q * norm_d)
        
        doc_copy = {k: v for k, v in doc.items() if k != "embedding"}
        doc_copy["similarity_score"] = round(similarity, 4)
        scored_docs.append(doc_copy)
    
    # Sort by similarity
    scored_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    xray.metric("max_similarity", scored_docs[0]["similarity_score"] if scored_docs else 0)
    xray.metric("min_similarity", scored_docs[top_k-1]["similarity_score"] if len(scored_docs) >= top_k else 0)
    
    return scored_docs[:top_k]


@xray.step("RANK")
def rerank_documents(candidates: list[dict], query: str) -> list[dict]:
    """Rerank documents using cross-encoder simulation."""
    xray.metric("model", "cross-encoder-ms-marco")
    xray.metric("candidates_count", len(candidates))
    
    query_terms = set(query.lower().split())
    
    for doc in candidates:
        # Simulate cross-encoder scoring
        content_terms = set(doc["content"].lower().split())
        
        # Term overlap
        overlap = len(query_terms & content_terms) / len(query_terms) if query_terms else 0
        
        # Quality boost
        quality_boost = doc["quality_score"] * 0.2
        
        # Citation boost
        citation_boost = min(0.2, math.log(doc["citation_count"] + 1) / 10)
        
        # Recency boost
        days_old = (datetime.now() - datetime.fromisoformat(doc["created_at"])).days
        recency_boost = max(0, (365 - days_old) / 365) * 0.1
        
        # Combine scores
        rerank_score = (
            doc["similarity_score"] * 0.4 +
            overlap * 0.3 +
            quality_boost +
            citation_boost +
            recency_boost
        )
        
        doc["rerank_score"] = round(rerank_score, 4)
        xray.score(doc, rerank_score)
    
    return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)


@xray.step("FILTER")
def filter_low_quality(candidates: list[dict]) -> list[dict]:
    """Filter out low-quality documents."""
    kept = []
    
    for doc in candidates:
        # Quality threshold
        if doc["quality_score"] < 0.6:
            xray.drop(doc, "low_quality_score")
            continue
        
        # Rerank score threshold
        if doc["rerank_score"] < 0.2:
            xray.drop(doc, "low_rerank_score")
            continue
        
        # Too old (over 1 year)
        days_old = (datetime.now() - datetime.fromisoformat(doc["created_at"])).days
        if days_old > 365:
            xray.drop(doc, "too_old")
            continue
        
        # Too short
        if doc["word_count"] < 50:
            xray.drop(doc, "too_short")
            continue
        
        kept.append(doc)
    
    xray.metric("filter_rate", 1 - len(kept) / len(candidates) if candidates else 0)
    
    return kept


@xray.step("SELECT")
def optimize_context(candidates: list[dict], max_tokens: int) -> list[dict]:
    """Select documents to fit within context window."""
    xray.metric("max_tokens", max_tokens)
    
    selected = []
    total_tokens = 0
    domains_seen = set()
    
    for doc in candidates:
        # Estimate tokens (rough: 1 word ≈ 1.3 tokens)
        doc_tokens = int(doc["word_count"] * 1.3)
        
        # Check if it fits
        if total_tokens + doc_tokens > max_tokens:
            xray.drop(doc, "context_window_exceeded")
            continue
        
        # Limit per domain for diversity
        if doc["domain"] in domains_seen and len([d for d in selected if d["domain"] == doc["domain"]]) >= 3:
            xray.drop(doc, "domain_limit_reached")
            continue
        
        selected.append(doc)
        total_tokens += doc_tokens
        domains_seen.add(doc["domain"])
        
        # Stop if we have enough
        if len(selected) >= 10:
            break
    
    xray.metric("selected_count", len(selected))
    xray.metric("total_tokens_used", total_tokens)
    xray.metric("domains_covered", list(domains_seen))
    
    return selected


@xray.step("LLM_CALL")
def generate_response(query: str, context_docs: list[dict]) -> dict:
    """Generate response using LLM."""
    # Build context
    context = "\n\n".join([
        f"[{i+1}] {doc['title']}\n{doc['content'][:500]}..."
        for i, doc in enumerate(context_docs)
    ])
    
    prompt = f"""Based on the following documents, answer the question.

Question: {query}

Documents:
{context}

Provide a comprehensive answer with citations [1], [2], etc."""

    xray.artifact("prompt", prompt)
    xray.metric("model", "gpt-4-turbo")
    xray.metric("context_docs", len(context_docs))
    xray.metric("prompt_tokens", len(prompt.split()))
    
    # Simulate LLM response
    citations = [f"[{i+1}]" for i in range(min(3, len(context_docs)))]
    response = f"""Based on the retrieved documents, here is a comprehensive answer to your question:

The query relates to {context_docs[0]['domain'] if context_docs else 'various domains'}. 
According to the sources {', '.join(citations)}, there have been significant developments 
in this area. Key findings include {random.choice(FINDINGS)} and {random.choice(FINDINGS)}.

The research from {context_docs[0]['source'] if context_docs else 'various sources'} 
indicates that this trend is expected to continue. For more details, refer to the 
cited documents.

Sources: {', '.join([doc['title'] for doc in context_docs[:3]])}"""
    
    xray.artifact("response", response)
    xray.metric("response_tokens", len(response.split()))
    
    return {
        "answer": response,
        "citations": [{"id": doc["id"], "title": doc["title"]} for doc in context_docs],
        "confidence": round(random.uniform(0.7, 0.95), 2),
    }


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RAG Document Retrieval Pipeline Demo")
    print("=" * 70)
    
    # Run sample queries
    for sample in SAMPLE_QUERIES[:5]:
        query = sample["query"]
        print(f"\n❓ Query: {query}")
        print("-" * 50)
        
        result = answer_question(query, max_context_tokens=2000)
        
        print(f"📝 Answer preview:")
        print(f"   {result['answer'][:200]}...")
        print(f"\n📚 Citations ({len(result['citations'])}):")
        for cite in result['citations'][:3]:
            print(f"   - {cite['title']}")
        print(f"\n🎯 Confidence: {result['confidence']:.0%}")
    
    print("\n" + "=" * 70)
    print("✅ Done! Check http://localhost:3000 for detailed traces")
    print("=" * 70)

