"""
Example: Using X-Ray SDK to instrument a product search pipeline.
Run with: python example.py
"""

import sys
sys.path.insert(0, '.')

from xray import configure, Run

# Configure SDK to point to local server
configure(endpoint="http://localhost:8000", flush_interval=0.5)

# Simulate product data
PRODUCTS = [
    {"id": "p1", "name": "Sony WH-1000XM5", "category": "headphones", "price": 350, "score": 0.95},
    {"id": "p2", "name": "Bose QC45", "category": "headphones", "price": 280, "score": 0.91},
    {"id": "p3", "name": "Apple AirPods Pro", "category": "earbuds", "price": 250, "score": 0.88},
    {"id": "p4", "name": "Samsung Galaxy Buds", "category": "earbuds", "price": 150, "score": 0.75},
    {"id": "p5", "name": "JBL Tune 500", "category": "headphones", "price": 50, "score": 0.60},
    {"id": "p6", "name": "Skullcandy Crusher", "category": "headphones", "price": 120, "score": 0.55},
    {"id": "p7", "name": "Beats Solo3", "category": "headphones", "price": 200, "score": 0.70},
    {"id": "p8", "name": "Anker Soundcore", "category": "earbuds", "price": 30, "score": 0.45},
    {"id": "p9", "name": "Audio-Technica M50x", "category": "headphones", "price": 150, "score": 0.85},
    {"id": "p10", "name": "Sennheiser HD 560S", "category": "headphones", "price": 180, "score": 0.82},
]


def run_search_pipeline(query: str, category_filter: str, max_price: int):
    """Simulated product search pipeline with X-Ray instrumentation."""
    
    with Run(
        pipeline_name="sdk-demo-search",
        version="v1.0.0",
        tags={"source": "sdk-example"},
        input_summary={"query": query, "category": category_filter, "max_price": max_price},
    ) as run:
        
        # Step 1: Retrieve all products (simulated vector search)
        with run.step("vector-search", "RETRIEVE") as step:
            candidates = PRODUCTS.copy()
            step.set_counts(1, len(candidates))
            step.add_metric("index", "products-v2")
        
        # Step 2: Filter by category
        with run.step("category-filter", "FILTER") as step:
            cs = step.record_candidates()
            cs.record_input(candidates)
            
            filtered = []
            drop_reasons = {}
            for p in candidates:
                if p["category"] == category_filter:
                    filtered.append(p)
                else:
                    drop_reasons[p["id"]] = "wrong_category"
            
            cs.record_output(filtered)
            cs.record_drop_reasons(drop_reasons)
            candidates = filtered
        
        # Step 3: Filter by price
        with run.step("price-filter", "FILTER") as step:
            cs = step.record_candidates()
            cs.record_input(candidates)
            
            filtered = []
            drop_reasons = {}
            for p in candidates:
                if p["price"] <= max_price:
                    filtered.append(p)
                else:
                    drop_reasons[p["id"]] = "above_budget"
            
            cs.record_output(filtered)
            cs.record_drop_reasons(drop_reasons)
            candidates = filtered
        
        # Step 4: Rank by score
        with run.step("relevance-ranker", "RANK") as step:
            cs = step.record_candidates()
            cs.record_input(candidates)
            
            # Record scores
            scores = {p["id"]: p["score"] for p in candidates}
            cs.record_scores(scores)
            
            # Sort by score and take top 3
            ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)[:3]
            cs.record_output(ranked)
            candidates = ranked
        
        # Step 5: Final selection
        with run.step("final-select", "SELECT") as step:
            step.set_counts(len(candidates), 1)
            result = candidates[0] if candidates else None
        
        # Set final output
        if result:
            run.set_output({"selected": result["name"], "price": result["price"]})
        
        print(f"[{run.run_id}] Query: '{query}' -> Result: {result['name'] if result else 'None'}")
        return result


if __name__ == "__main__":
    import time
    
    print("Running X-Ray SDK example...\n")
    
    # Run a few searches
    run_search_pipeline("wireless audio", "headphones", 200)
    run_search_pipeline("budget earbuds", "earbuds", 100)
    run_search_pipeline("premium headphones", "headphones", 400)
    
    # Wait for async flush
    print("\nFlushing events to server...")
    time.sleep(2)
    
    print("\nDone! Check http://localhost:3000 to see the new runs.")
    print("Look for pipeline: 'sdk-demo-search'")

