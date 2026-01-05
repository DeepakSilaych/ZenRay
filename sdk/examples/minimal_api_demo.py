#!/usr/bin/env python3
"""
Minimal API Demo - ZenRay SDK

This example shows the decorator-based API that requires
minimal code changes to instrument an existing pipeline.
"""
import zenray

# Initialize - reads ZENRAY_API_KEY and ZENRAY_ENDPOINT from env
zenray.init()

# Sample data
PRODUCTS = [
    {"id": "p1", "name": "Laptop Stand Pro", "category": "accessories", "price": 45, "rating": 4.5, "active": True},
    {"id": "p2", "name": "USB-C Hub", "category": "accessories", "price": 35, "rating": 4.2, "active": True},
    {"id": "p3", "name": "Mechanical Keyboard", "category": "keyboards", "price": 120, "rating": 4.8, "active": True},
    {"id": "p4", "name": "Mouse Pad XL", "category": "accessories", "price": 25, "rating": 3.9, "active": False},
    {"id": "p5", "name": "Monitor Light Bar", "category": "lighting", "price": 55, "rating": 4.6, "active": True},
    {"id": "p6", "name": "Webcam HD", "category": "cameras", "price": 80, "rating": 4.1, "active": True},
    {"id": "p7", "name": "Desk Organizer", "category": "accessories", "price": 20, "rating": 3.5, "active": True},
    {"id": "p8", "name": "Cable Management Kit", "category": "accessories", "price": 15, "rating": 4.0, "active": True},
]


# --- Pipeline Definition (Just decorators!) ---

@zenray.pipeline("product-search", version="v2.0")
def search_products(query: str, max_results: int = 5) -> list[dict]:
    """
    Search for products matching a query.
    
    Pipeline:
    1. Retrieve candidates by category
    2. Filter inactive and low-rated products
    3. Rank by relevance score
    4. Return top results
    """
    # Tag the run with query info
    zenray.tag("query", query)
    zenray.tag("max_results", str(max_results))
    
    # Pipeline steps
    candidates = retrieve_candidates(query)
    filtered = filter_candidates(candidates)
    ranked = rank_by_relevance(filtered, query)
    
    return ranked[:max_results]


@zenray.step("RETRIEVE")
def retrieve_candidates(query: str) -> list[dict]:
    """Retrieve all potentially matching products."""
    # In real app, this would be a database query
    zenray.metric("source", "mock_db")
    
    # Simple keyword matching
    query_lower = query.lower()
    matches = [
        p for p in PRODUCTS
        if query_lower in p["name"].lower() or query_lower in p["category"].lower()
    ]
    
    # If no matches, return all products
    if not matches:
        return PRODUCTS.copy()
    
    return matches


@zenray.step("FILTER")
def filter_candidates(candidates: list[dict]) -> list[dict]:
    """Filter out inactive and low-rated products."""
    kept = []
    
    for product in candidates:
        if not product["active"]:
            zenray.drop(product, "inactive")
        elif product["rating"] < 4.0:
            zenray.drop(product, "low_rating")
        else:
            kept.append(product)
    
    return kept


@zenray.step("RANK")
def rank_by_relevance(candidates: list[dict], query: str) -> list[dict]:
    """Rank products by relevance score."""
    query_lower = query.lower()
    
    for product in candidates:
        # Simple relevance score based on name match and rating
        name_match = 1.0 if query_lower in product["name"].lower() else 0.5
        rating_score = product["rating"] / 5.0
        relevance = (name_match * 0.6) + (rating_score * 0.4)
        
        zenray.score(product, relevance)
        product["relevance"] = relevance
    
    return sorted(candidates, key=lambda x: x["relevance"], reverse=True)


# --- LLM Example ---

@zenray.pipeline("product-description", version="v1.0")
def generate_description(product: dict) -> str:
    """Generate a marketing description for a product."""
    description = call_llm(product)
    return description


@zenray.step("LLM_CALL")
def call_llm(product: dict) -> str:
    """Call LLM to generate description (mocked)."""
    prompt = f"Write a short marketing description for: {product['name']}"
    
    # Record prompt as artifact
    zenray.artifact("prompt", prompt)
    zenray.metric("model", "gpt-4")
    zenray.metric("temperature", 0.7)
    
    # Mock LLM response
    response = f"Introducing the {product['name']} - your essential workspace companion. " \
               f"With a stellar {product['rating']} star rating, this premium {product['category']} " \
               f"product delivers exceptional quality at just ${product['price']}."
    
    # Record response as artifact
    zenray.artifact("response", response)
    zenray.metric("tokens_used", len(response.split()))
    
    return response


# --- Main ---

if __name__ == "__main__":
    print("=" * 60)
    print("X-Ray Minimal API Demo")
    print("=" * 60)
    
    # Run search pipeline
    print("\n1. Product Search Pipeline")
    print("-" * 40)
    
    results = search_products("accessories")
    print(f"Query: 'accessories'")
    print(f"Found {len(results)} products:")
    for p in results:
        print(f"  - {p['name']} (score: {p.get('relevance', 'N/A'):.2f})")
    
    # Run another search
    print()
    results2 = search_products("keyboard", max_results=3)
    print(f"Query: 'keyboard'")
    print(f"Found {len(results2)} products:")
    for p in results2:
        print(f"  - {p['name']} (score: {p.get('relevance', 'N/A'):.2f})")
    
    # Run LLM pipeline
    print("\n2. Product Description Pipeline")
    print("-" * 40)
    
    product = {"id": "p3", "name": "Mechanical Keyboard", "category": "keyboards", "price": 120, "rating": 4.8}
    description = generate_description(product)
    print(f"Product: {product['name']}")
    print(f"Description: {description}")
    
    print("\n" + "=" * 60)
    print("Done! Check http://localhost:3000 to view the traces.")
    print("=" * 60)

