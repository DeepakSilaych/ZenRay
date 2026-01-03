"""
Competitor Selection Pipeline - X-Ray SDK Example

This example matches the problem statement scenario:
Given a seller's product, find the best competitor product to benchmark against.

Steps:
1. LLM generates search keywords from product title/category
2. Retrieve candidate products from catalog
3. Filter by price range, category match
4. LLM judges relevance and eliminates false positives
5. Rank and select the best competitor

Run with: python examples/competitor_selection.py
"""

import sys
sys.path.insert(0, '.')

from xray import configure, Run

configure(endpoint="http://localhost:8000", flush_interval=0.5)

# Simulated product catalog
CATALOG = [
    {"id": "prod-001", "name": "Adjustable Laptop Stand - Aluminum", "category": "laptop-accessories", "price": 45, "rating": 4.5},
    {"id": "prod-002", "name": "Portable Laptop Desk with Cooling Fan", "category": "laptop-accessories", "price": 65, "rating": 4.2},
    {"id": "prod-003", "name": "Phone Case for iPhone 15 - Clear", "category": "phone-cases", "price": 15, "rating": 4.8},
    {"id": "prod-004", "name": "Wooden Laptop Riser Stand", "category": "laptop-accessories", "price": 35, "rating": 4.6},
    {"id": "prod-005", "name": "Monitor Stand with USB Hub", "category": "monitor-accessories", "price": 55, "rating": 4.3},
    {"id": "prod-006", "name": "Foldable Laptop Stand for Desk", "category": "laptop-accessories", "price": 28, "rating": 4.4},
    {"id": "prod-007", "name": "Phone Stand Holder - Adjustable", "category": "phone-accessories", "price": 12, "rating": 4.1},
    {"id": "prod-008", "name": "Ergonomic Laptop Stand with Keyboard", "category": "laptop-accessories", "price": 89, "rating": 4.7},
    {"id": "prod-009", "name": "Silicone Phone Case - Black", "category": "phone-cases", "price": 10, "rating": 4.0},
    {"id": "prod-010", "name": "Laptop Cooling Pad with Fans", "category": "laptop-accessories", "price": 40, "rating": 4.3},
]


def run_competitor_selection(seller_product: dict, price_range: tuple = (0.5, 1.5)):
    """
    Find the best competitor for a seller's product.
    
    This demonstrates the full X-Ray instrumentation including:
    - LLM steps with prompt/response artifacts
    - Filter steps with drop reasons
    - Rank steps with scores
    - Candidate tracing
    """
    
    with Run(
        pipeline_name="competitor-selection",
        version="v2.0.0",
        tags={"use_case": "benchmarking", "region": "us"},
        input_summary={
            "seller_product": seller_product["name"],
            "category": seller_product["category"],
            "price": seller_product["price"],
        },
    ) as run:
        
        # Step 1: LLM Keyword Generation
        with run.step("keyword-generator", "LLM_CALL") as step:
            prompt = f"""Generate search keywords to find competitor products for:
Product: {seller_product['name']}
Category: {seller_product['category']}

Return 3-5 keywords that would help find similar competing products."""

            # Simulated LLM response
            response = f"""Based on the product "{seller_product['name']}", here are relevant keywords:
1. laptop stand
2. adjustable stand
3. ergonomic desk accessory
4. aluminum laptop holder
5. portable laptop riser"""
            
            keywords = ["laptop stand", "adjustable stand", "desk accessory", "laptop holder"]
            
            # Record LLM artifacts
            step.add_artifact("prompt", prompt)
            step.add_artifact("response", response)
            step.add_artifact("config", {"model": "gpt-4", "temperature": 0.3})
            step.set_counts(1, len(keywords))
            step.add_metric("tokens_in", 45)
            step.add_metric("tokens_out", 62)
        
        # Step 2: Retrieve Candidates
        with run.step("catalog-search", "RETRIEVE") as step:
            # Simulate searching catalog (would be vector search in reality)
            candidates = CATALOG.copy()
            step.set_counts(1, len(candidates))
            step.add_metric("index", "products-v3")
            step.add_metric("search_type", "keyword+vector")
        
        # Step 3: Category Filter
        with run.step("category-filter", "FILTER") as step:
            cs = step.record_candidates()
            cs.record_input(candidates, id_field="id")
            
            target_category = seller_product["category"]
            filtered = []
            drop_reasons = {}
            
            for p in candidates:
                if p["category"] == target_category:
                    filtered.append(p)
                else:
                    drop_reasons[p["id"]] = f"category_mismatch:{p['category']}"
            
            cs.record_output(filtered, id_field="id")
            cs.record_drop_reasons(drop_reasons)
            candidates = filtered
        
        # Step 4: Price Range Filter
        with run.step("price-filter", "FILTER") as step:
            cs = step.record_candidates()
            cs.record_input(candidates, id_field="id")
            
            min_price = seller_product["price"] * price_range[0]
            max_price = seller_product["price"] * price_range[1]
            
            filtered = []
            drop_reasons = {}
            
            for p in candidates:
                if min_price <= p["price"] <= max_price:
                    filtered.append(p)
                elif p["price"] < min_price:
                    drop_reasons[p["id"]] = "price_too_low"
                else:
                    drop_reasons[p["id"]] = "price_too_high"
            
            cs.record_output(filtered, id_field="id")
            cs.record_drop_reasons(drop_reasons)
            step.add_metric("price_range", f"${min_price:.0f}-${max_price:.0f}")
            candidates = filtered
        
        # Step 5: LLM Relevance Judge
        with run.step("relevance-judge", "JUDGE") as step:
            cs = step.record_candidates()
            cs.record_input(candidates, id_field="id")
            
            # Simulate LLM judging each candidate
            prompt = f"""For each candidate, judge if it's a relevant competitor to:
"{seller_product['name']}" (${seller_product['price']})

Candidates:
{chr(10).join(f"- {p['name']} (${p['price']})" for p in candidates)}

For each, respond: RELEVANT or NOT_RELEVANT with brief reason."""

            # Simulated LLM judgments
            judgments = {}
            scores = {}
            drop_reasons = {}
            kept = []
            
            for p in candidates:
                # Simulate LLM scoring based on name similarity
                if "laptop" in p["name"].lower() and "stand" in p["name"].lower():
                    judgments[p["id"]] = {"relevant": True, "confidence": 0.9, "reason": "Direct competitor - same product type"}
                    scores[p["id"]] = 0.9
                    kept.append(p)
                elif "laptop" in p["name"].lower():
                    judgments[p["id"]] = {"relevant": True, "confidence": 0.7, "reason": "Related product - laptop accessory"}
                    scores[p["id"]] = 0.7
                    kept.append(p)
                else:
                    judgments[p["id"]] = {"relevant": False, "confidence": 0.85, "reason": "Not a direct competitor"}
                    scores[p["id"]] = 0.3
                    drop_reasons[p["id"]] = "low_relevance"
            
            response = "Judgments:\n" + "\n".join(
                f"- {p['name']}: {'RELEVANT' if judgments[p['id']]['relevant'] else 'NOT_RELEVANT'} ({judgments[p['id']]['reason']})"
                for p in candidates
            )
            
            cs.record_output(kept, id_field="id")
            cs.record_scores(scores)
            cs.record_drop_reasons(drop_reasons)
            
            step.add_artifact("prompt", prompt)
            step.add_artifact("response", response)
            step.add_artifact("judgments", judgments)
            step.add_metric("model", "gpt-4")
            step.add_metric("candidates_judged", len(candidates))
            candidates = kept
        
        # Step 6: Final Ranking & Selection
        with run.step("final-ranker", "RANK") as step:
            cs = step.record_candidates()
            cs.record_input(candidates, id_field="id")
            
            # Rank by combined score: rating * price_similarity
            def compute_score(p):
                price_diff = abs(p["price"] - seller_product["price"]) / seller_product["price"]
                price_score = max(0, 1 - price_diff)
                return p["rating"] * 0.6 + price_score * 0.4
            
            scores = {p["id"]: round(compute_score(p), 3) for p in candidates}
            ranked = sorted(candidates, key=lambda p: scores[p["id"]], reverse=True)
            
            # Take top 3
            top_k = ranked[:3]
            
            cs.record_output(top_k, id_field="id")
            cs.record_scores(scores)
            candidates = top_k
        
        # Step 7: Select Best
        with run.step("select-best", "SELECT") as step:
            step.set_counts(len(candidates), 1)
            best = candidates[0] if candidates else None
            
            if best:
                step.add_metric("selected_id", best["id"])
                step.add_metric("selected_name", best["name"])
        
        # Set final output
        if best:
            run.set_output({
                "competitor": best["name"],
                "competitor_id": best["id"],
                "competitor_price": best["price"],
                "match_confidence": scores.get(best["id"], 0),
            })
        
        result = best["name"] if best else "No match found"
        print(f"[{run.run_id}] Seller: {seller_product['name']} → Competitor: {result}")
        return best


if __name__ == "__main__":
    import time
    
    print("Running Competitor Selection Pipeline with X-Ray...\n")
    
    # Test case 1: Good match scenario
    seller_product_1 = {
        "id": "seller-001",
        "name": "Premium Aluminum Laptop Stand",
        "category": "laptop-accessories",
        "price": 42,
    }
    run_competitor_selection(seller_product_1)
    
    # Test case 2: Edge case - might match wrong category
    seller_product_2 = {
        "id": "seller-002",
        "name": "Universal Phone & Tablet Stand",
        "category": "phone-accessories",
        "price": 25,
    }
    run_competitor_selection(seller_product_2)
    
    # Wait for flush
    print("\nFlushing events to server...")
    time.sleep(2)
    
    print("\nDone! Check http://localhost:3000 for:")
    print("- Pipeline: 'competitor-selection'")
    print("- LLM steps with prompt/response artifacts")
    print("- Filter steps with drop reasons")
    print("- Candidate trace to debug mismatches")

