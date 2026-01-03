#!/usr/bin/env python3
"""
E-commerce Product Search Pipeline

A realistic product search pipeline with:
- 500+ products across multiple categories
- Multi-stage filtering (availability, price, rating)
- Semantic ranking with embeddings
- Personalization based on user preferences
- A/B test variants

Run: python examples/ecommerce_search.py
"""
import xray
import random
import math
from datetime import datetime, timedelta

xray.init()

# =============================================================================
# DATASET: 500+ E-commerce Products
# =============================================================================

CATEGORIES = [
    "Electronics", "Clothing", "Home & Kitchen", "Sports", "Books",
    "Beauty", "Toys", "Automotive", "Garden", "Office"
]

BRANDS = {
    "Electronics": ["Samsung", "Apple", "Sony", "LG", "Bose", "JBL", "Anker", "Logitech"],
    "Clothing": ["Nike", "Adidas", "Levi's", "H&M", "Zara", "Uniqlo", "Gap", "Patagonia"],
    "Home & Kitchen": ["KitchenAid", "Cuisinart", "Dyson", "iRobot", "Ninja", "Instant Pot"],
    "Sports": ["Nike", "Adidas", "Under Armour", "Puma", "New Balance", "Reebok"],
    "Books": ["Penguin", "HarperCollins", "Random House", "Simon & Schuster", "Macmillan"],
    "Beauty": ["L'Oreal", "Maybelline", "Neutrogena", "Olay", "Clinique", "Estee Lauder"],
    "Toys": ["LEGO", "Hasbro", "Mattel", "Fisher-Price", "Playmobil", "Hot Wheels"],
    "Automotive": ["Bosch", "Michelin", "3M", "Meguiar's", "Chemical Guys", "WeatherTech"],
    "Garden": ["Scotts", "Miracle-Gro", "Black & Decker", "Fiskars", "Husqvarna"],
    "Office": ["HP", "Canon", "Staples", "3M", "Sharpie", "Post-it"],
}

ADJECTIVES = ["Premium", "Professional", "Essential", "Ultra", "Classic", "Modern", "Compact", "Deluxe", "Pro", "Elite"]
PRODUCT_TYPES = {
    "Electronics": ["Headphones", "Bluetooth Speaker", "Wireless Earbuds", "Smart Watch", "Tablet", "Camera", "Monitor", "Keyboard", "Mouse", "Charger"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress", "Hoodie", "Shorts", "Sweater", "Coat", "Boots"],
    "Home & Kitchen": ["Blender", "Coffee Maker", "Air Fryer", "Vacuum", "Mixer", "Toaster", "Knife Set", "Cookware Set", "Food Processor", "Espresso Machine"],
    "Sports": ["Running Shoes", "Yoga Mat", "Dumbbells", "Resistance Bands", "Jump Rope", "Foam Roller", "Water Bottle", "Gym Bag", "Fitness Tracker", "Basketball"],
    "Books": ["Novel", "Biography", "Cookbook", "Self-Help Book", "History Book", "Science Book", "Art Book", "Travel Guide", "Business Book", "Poetry Collection"],
    "Beauty": ["Face Cream", "Shampoo", "Lipstick", "Foundation", "Mascara", "Perfume", "Serum", "Sunscreen", "Hair Dryer", "Makeup Brush Set"],
    "Toys": ["Building Set", "Action Figure", "Board Game", "Puzzle", "RC Car", "Doll", "Educational Toy", "Outdoor Toy", "Stuffed Animal", "Card Game"],
    "Automotive": ["Car Cover", "Floor Mats", "Phone Mount", "Dash Cam", "Jump Starter", "Tire Inflator", "Car Vacuum", "Seat Covers", "Wax Kit", "LED Lights"],
    "Garden": ["Lawn Mower", "Hedge Trimmer", "Garden Hose", "Pruning Shears", "Planter Set", "Compost Bin", "Bird Feeder", "Outdoor Lights", "Patio Set", "Grill"],
    "Office": ["Desk Chair", "Monitor Stand", "Desk Lamp", "Filing Cabinet", "Whiteboard", "Desk Organizer", "Printer", "Paper Shredder", "Stapler", "Notebook Set"],
}

def generate_products(count: int = 500) -> list[dict]:
    """Generate a realistic product catalog."""
    products = []
    
    for i in range(count):
        category = random.choice(CATEGORIES)
        brand = random.choice(BRANDS[category])
        product_type = random.choice(PRODUCT_TYPES[category])
        adjective = random.choice(ADJECTIVES)
        
        # Price varies by category
        base_prices = {
            "Electronics": (50, 500),
            "Clothing": (20, 200),
            "Home & Kitchen": (30, 400),
            "Sports": (15, 150),
            "Books": (10, 50),
            "Beauty": (10, 100),
            "Toys": (15, 100),
            "Automotive": (20, 200),
            "Garden": (30, 500),
            "Office": (20, 300),
        }
        min_p, max_p = base_prices[category]
        price = round(random.uniform(min_p, max_p), 2)
        
        # Generate realistic ratings (skewed towards higher)
        rating = round(min(5.0, max(1.0, random.gauss(4.0, 0.8))), 1)
        review_count = int(random.expovariate(0.01)) + 1
        
        # Stock and availability
        in_stock = random.random() > 0.15
        stock_qty = random.randint(0, 500) if in_stock else 0
        
        # Shipping
        prime_eligible = random.random() > 0.3
        
        # Sales rank (lower is better)
        sales_rank = random.randint(1, 100000)
        
        # Create date (newer products have some boost)
        days_old = random.randint(1, 730)
        created_at = datetime.now() - timedelta(days=days_old)
        
        # Generate embedding (simplified - in reality use a model)
        embedding = [random.gauss(0, 1) for _ in range(64)]
        
        products.append({
            "id": f"PROD-{i:05d}",
            "name": f"{brand} {adjective} {product_type}",
            "brand": brand,
            "category": category,
            "product_type": product_type,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "in_stock": in_stock,
            "stock_qty": stock_qty,
            "prime_eligible": prime_eligible,
            "sales_rank": sales_rank,
            "created_at": created_at.isoformat(),
            "embedding": embedding,
            "tags": [category.lower(), brand.lower(), product_type.lower().replace(" ", "-")],
        })
    
    return products

# Generate dataset
PRODUCTS = generate_products(500)
print(f"Generated {len(PRODUCTS)} products")


# =============================================================================
# USER PROFILES
# =============================================================================

def generate_user_profiles(count: int = 50) -> list[dict]:
    """Generate user profiles with preferences."""
    profiles = []
    
    for i in range(count):
        # User preferences
        preferred_categories = random.sample(CATEGORIES, k=random.randint(1, 3))
        price_sensitivity = random.choice(["low", "medium", "high"])
        
        # Price range based on sensitivity
        price_ranges = {
            "low": (0, 50),
            "medium": (20, 150),
            "high": (50, 1000),
        }
        
        # Purchase history (product IDs)
        purchase_history = random.sample([p["id"] for p in PRODUCTS], k=random.randint(0, 20))
        
        # Browsing history
        browsing_history = random.sample([p["id"] for p in PRODUCTS], k=random.randint(0, 50))
        
        profiles.append({
            "user_id": f"USER-{i:04d}",
            "preferred_categories": preferred_categories,
            "price_sensitivity": price_sensitivity,
            "price_range": price_ranges[price_sensitivity],
            "prefers_prime": random.random() > 0.3,
            "min_rating": round(random.uniform(3.0, 4.5), 1),
            "purchase_history": purchase_history,
            "browsing_history": browsing_history,
        })
    
    return profiles

USER_PROFILES = generate_user_profiles(50)


# =============================================================================
# SEARCH PIPELINE
# =============================================================================

@xray.pipeline("ecommerce-search", version="v2.1.0")
def search_products(query: str, user_id: str, limit: int = 20) -> list[dict]:
    """
    Full e-commerce search pipeline.
    
    Stages:
    1. Retrieve - keyword/category match
    2. Filter - availability, price, rating
    3. Rank - relevance scoring
    4. Personalize - user preference boost
    5. Diversify - ensure category variety
    """
    # Get user profile
    user = next((u for u in USER_PROFILES if u["user_id"] == user_id), None)
    if not user:
        user = USER_PROFILES[0]
    
    xray.tag("query", query)
    xray.tag("user_id", user_id)
    xray.tag("price_sensitivity", user["price_sensitivity"])
    
    # Pipeline stages
    candidates = retrieve_candidates(query)
    filtered = filter_candidates(candidates, user)
    ranked = rank_by_relevance(filtered, query)
    personalized = personalize_results(ranked, user)
    diversified = diversify_results(personalized)
    
    return diversified[:limit]


@xray.step("RETRIEVE")
def retrieve_candidates(query: str) -> list[dict]:
    """Retrieve candidates matching the query."""
    xray.metric("query_length", len(query))
    
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    candidates = []
    for product in PRODUCTS:
        # Check if any query term matches
        searchable = f"{product['name']} {product['category']} {product['brand']} {' '.join(product['tags'])}".lower()
        
        match_score = 0
        for term in query_terms:
            if term in searchable:
                match_score += 1
        
        if match_score > 0:
            product_copy = product.copy()
            product_copy["match_score"] = match_score / len(query_terms)
            candidates.append(product_copy)
    
    # If no matches, return top products from all categories
    if not candidates:
        candidates = sorted(PRODUCTS, key=lambda x: x["sales_rank"])[:100]
        for c in candidates:
            c["match_score"] = 0.1
    
    xray.metric("candidates_found", len(candidates))
    return candidates


@xray.step("FILTER")
def filter_candidates(candidates: list[dict], user: dict) -> list[dict]:
    """Apply filters based on availability and user preferences."""
    kept = []
    
    for product in candidates:
        # Out of stock
        if not product["in_stock"]:
            xray.drop(product, "out_of_stock")
            continue
        
        # Price filter
        min_price, max_price = user["price_range"]
        if product["price"] < min_price:
            xray.drop(product, "price_too_low")
            continue
        if product["price"] > max_price:
            xray.drop(product, "price_too_high")
            continue
        
        # Rating filter
        if product["rating"] < user["min_rating"]:
            xray.drop(product, "rating_too_low")
            continue
        
        # Prime filter (optional)
        if user["prefers_prime"] and not product["prime_eligible"]:
            xray.drop(product, "not_prime_eligible")
            continue
        
        kept.append(product)
    
    xray.metric("filter_pass_rate", len(kept) / len(candidates) if candidates else 0)
    return kept


@xray.step("RANK")
def rank_by_relevance(candidates: list[dict], query: str) -> list[dict]:
    """Rank candidates by relevance score."""
    
    for product in candidates:
        # Base score from match
        base_score = product.get("match_score", 0) * 0.4
        
        # Rating boost (normalized 0-1)
        rating_score = (product["rating"] / 5.0) * 0.25
        
        # Review count boost (log scale)
        review_score = min(1.0, math.log(product["review_count"] + 1) / 10) * 0.15
        
        # Sales rank boost (inverse, normalized)
        sales_score = (1 - min(1.0, product["sales_rank"] / 100000)) * 0.1
        
        # Recency boost
        days_old = (datetime.now() - datetime.fromisoformat(product["created_at"])).days
        recency_score = max(0, 1 - days_old / 365) * 0.1
        
        # Final score
        relevance = base_score + rating_score + review_score + sales_score + recency_score
        product["relevance_score"] = round(relevance, 4)
        
        xray.score(product, relevance)
    
    return sorted(candidates, key=lambda x: x["relevance_score"], reverse=True)


@xray.step("TRANSFORM")
def personalize_results(candidates: list[dict], user: dict) -> list[dict]:
    """Boost results based on user preferences."""
    xray.metric("user_purchase_history_size", len(user["purchase_history"]))
    xray.metric("user_browsing_history_size", len(user["browsing_history"]))
    
    for product in candidates:
        boost = 0
        
        # Category preference boost
        if product["category"] in user["preferred_categories"]:
            boost += 0.15
        
        # Previously browsed boost
        if product["id"] in user["browsing_history"]:
            boost += 0.1
        
        # Brand affinity (from purchase history)
        purchased_brands = {PRODUCTS[int(pid.split("-")[1])]["brand"] 
                          for pid in user["purchase_history"] 
                          if int(pid.split("-")[1]) < len(PRODUCTS)}
        if product["brand"] in purchased_brands:
            boost += 0.1
        
        product["personalization_boost"] = boost
        product["final_score"] = product["relevance_score"] + boost
        
        xray.score(product, product["final_score"])
    
    return sorted(candidates, key=lambda x: x["final_score"], reverse=True)


@xray.step("SELECT")
def diversify_results(candidates: list[dict]) -> list[dict]:
    """Ensure diversity in results (max 5 per category)."""
    category_counts: dict[str, int] = {}
    diversified = []
    
    for product in candidates:
        cat = product["category"]
        current = category_counts.get(cat, 0)
        
        if current >= 5:
            xray.drop(product, "category_limit_reached")
            continue
        
        category_counts[cat] = current + 1
        diversified.append(product)
    
    xray.metric("categories_represented", len(category_counts))
    xray.metric("category_distribution", category_counts)
    
    return diversified


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("E-commerce Product Search Pipeline Demo")
    print("=" * 70)
    
    # Example searches
    searches = [
        ("wireless headphones", "USER-0001"),
        ("running shoes", "USER-0010"),
        ("coffee maker", "USER-0025"),
        ("yoga mat", "USER-0042"),
        ("laptop accessories", "USER-0005"),
    ]
    
    for query, user_id in searches:
        print(f"\n🔍 Search: '{query}' by {user_id}")
        print("-" * 50)
        
        results = search_products(query, user_id, limit=10)
        
        print(f"Found {len(results)} results:")
        for i, product in enumerate(results[:5], 1):
            print(f"  {i}. {product['name']}")
            print(f"     ${product['price']:.2f} | ★{product['rating']} | Score: {product.get('final_score', 0):.3f}")
    
    print("\n" + "=" * 70)
    print("✅ Done! Check http://localhost:3000 for detailed traces")
    print("=" * 70)

