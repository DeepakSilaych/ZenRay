#!/usr/bin/env python3
"""
Movie Recommendation System Pipeline

A collaborative filtering + content-based recommendation system with:
- 1000+ movies with rich metadata
- 500+ users with viewing history
- Multi-stage recommendation pipeline
- A/B testing with different algorithms

Run: python examples/recommendation_system.py
"""
import xray
import random
import math
from datetime import datetime, timedelta
from collections import defaultdict

xray.init()

# =============================================================================
# DATASET: Movies & Users
# =============================================================================

GENRES = ["Action", "Comedy", "Drama", "Sci-Fi", "Horror", "Romance", "Thriller", "Documentary", "Animation", "Adventure"]

DIRECTORS = [
    "Christopher Nolan", "Steven Spielberg", "Martin Scorsese", "Quentin Tarantino",
    "Denis Villeneuve", "Greta Gerwig", "Jordan Peele", "Bong Joon-ho", "Wes Anderson",
    "Guillermo del Toro", "Chloe Zhao", "David Fincher", "Ridley Scott", "James Cameron"
]

ACTORS = [
    "Leonardo DiCaprio", "Meryl Streep", "Tom Hanks", "Cate Blanchett",
    "Denzel Washington", "Viola Davis", "Brad Pitt", "Margot Robbie",
    "Timothee Chalamet", "Zendaya", "Ryan Gosling", "Emma Stone",
    "Joaquin Phoenix", "Scarlett Johansson", "Robert Downey Jr.", "Natalie Portman"
]

MOVIE_WORDS = [
    "Dark", "Light", "Last", "First", "Silent", "Eternal", "Hidden", "Lost", "Secret",
    "Rising", "Falling", "Broken", "Golden", "Silver", "Midnight", "Dawn", "Shadow"
]

MOVIE_NOUNS = [
    "Knight", "Journey", "Kingdom", "World", "Dream", "Storm", "Ocean", "Mountain",
    "City", "Heart", "Mind", "Spirit", "Legend", "Empire", "War", "Peace"
]


def generate_movies(count: int = 1000) -> list[dict]:
    """Generate a movie catalog."""
    movies = []
    
    for i in range(count):
        # Generate movie attributes
        primary_genre = random.choice(GENRES)
        secondary_genres = random.sample([g for g in GENRES if g != primary_genre], k=random.randint(0, 2))
        
        director = random.choice(DIRECTORS)
        cast = random.sample(ACTORS, k=random.randint(2, 5))
        
        # Generate title
        title_pattern = random.choice([
            f"The {random.choice(MOVIE_WORDS)} {random.choice(MOVIE_NOUNS)}",
            f"{random.choice(MOVIE_NOUNS)} of {random.choice(MOVIE_WORDS)}ness",
            f"{random.choice(MOVIE_WORDS)} {random.choice(MOVIE_NOUNS)}s",
            f"A {random.choice(MOVIE_WORDS)} {random.choice(MOVIE_NOUNS)}",
        ])
        
        # Year and rating
        year = random.randint(1990, 2024)
        rating = round(min(10.0, max(1.0, random.gauss(6.5, 1.5))), 1)
        
        # Popularity metrics
        vote_count = int(random.expovariate(0.0001)) + 100
        box_office = random.randint(1, 500) * 1_000_000 if random.random() > 0.3 else None
        
        # Runtime
        runtime = random.randint(80, 180)
        
        # Awards
        oscar_nominations = random.choices([0, 1, 2, 3, 5, 8, 10], weights=[70, 15, 7, 4, 2, 1, 1])[0]
        oscar_wins = random.randint(0, oscar_nominations)
        
        # Content features for content-based filtering
        features = {
            "action_intensity": random.random() if primary_genre in ["Action", "Thriller"] else random.random() * 0.3,
            "humor_level": random.random() if primary_genre == "Comedy" else random.random() * 0.3,
            "emotional_depth": random.random() if primary_genre in ["Drama", "Romance"] else random.random() * 0.5,
            "visual_effects": random.random() if primary_genre in ["Sci-Fi", "Action", "Animation"] else random.random() * 0.4,
            "plot_complexity": random.random(),
            "pacing": random.random(),  # 0=slow, 1=fast
        }
        
        movies.append({
            "id": f"MOV-{i:05d}",
            "title": title_pattern,
            "year": year,
            "genres": [primary_genre] + secondary_genres,
            "primary_genre": primary_genre,
            "director": director,
            "cast": cast,
            "rating": rating,
            "vote_count": vote_count,
            "runtime": runtime,
            "box_office": box_office,
            "oscar_nominations": oscar_nominations,
            "oscar_wins": oscar_wins,
            "features": features,
        })
    
    return movies


def generate_users(count: int = 500, movies: list[dict] = None) -> list[dict]:
    """Generate users with viewing history and preferences."""
    users = []
    
    for i in range(count):
        # User preferences
        favorite_genres = random.sample(GENRES, k=random.randint(1, 4))
        favorite_directors = random.sample(DIRECTORS, k=random.randint(0, 3))
        favorite_actors = random.sample(ACTORS, k=random.randint(0, 5))
        
        # Viewing history (movies they've watched with ratings)
        watched_count = random.randint(10, 100)
        watched_movies = random.sample(movies, k=min(watched_count, len(movies)))
        
        watch_history = {}
        for movie in watched_movies:
            # User rating influenced by their preferences
            base_rating = movie["rating"]
            genre_boost = 1.0 if movie["primary_genre"] in favorite_genres else -0.5
            director_boost = 0.5 if movie["director"] in favorite_directors else 0
            
            user_rating = round(min(10.0, max(1.0, base_rating + genre_boost + director_boost + random.gauss(0, 1))), 1)
            watch_history[movie["id"]] = {
                "rating": user_rating,
                "watched_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "completed": random.random() > 0.1,
            }
        
        # Activity level
        activity_level = random.choice(["casual", "regular", "power_user"])
        
        users.append({
            "id": f"USER-{i:05d}",
            "favorite_genres": favorite_genres,
            "favorite_directors": favorite_directors,
            "favorite_actors": favorite_actors,
            "watch_history": watch_history,
            "activity_level": activity_level,
            "account_age_days": random.randint(30, 1825),
            "subscription_tier": random.choice(["free", "basic", "premium"]),
        })
    
    return users


# Generate datasets
MOVIES = generate_movies(1000)
USERS = generate_users(500, MOVIES)
print(f"Generated {len(MOVIES)} movies and {len(USERS)} users")

# Build movie lookup
MOVIE_BY_ID = {m["id"]: m for m in MOVIES}


# =============================================================================
# RECOMMENDATION PIPELINE
# =============================================================================

@xray.pipeline("movie-recommendations", version="v4.0.0")
def get_recommendations(user_id: str, context: str = "home", limit: int = 20) -> list[dict]:
    """
    Generate personalized movie recommendations.
    
    Stages:
    1. Candidate generation (collaborative + content-based)
    2. Feature engineering
    3. Scoring and ranking
    4. Filtering (already watched, age-restricted, etc.)
    5. Diversification
    6. Business rules (new releases, promotions)
    """
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        user = USERS[0]
    
    xray.tag("user_id", user_id)
    xray.tag("context", context)
    xray.tag("activity_level", user["activity_level"])
    xray.tag("subscription", user["subscription_tier"])
    
    # Generate candidates from multiple sources
    collab_candidates = collaborative_filtering(user)
    content_candidates = content_based_filtering(user)
    popular_candidates = popularity_based(user)
    
    # Merge candidates
    all_candidates = merge_candidates([collab_candidates, content_candidates, popular_candidates])
    
    # Score and rank
    scored = score_candidates(all_candidates, user)
    
    # Filter
    filtered = apply_filters(scored, user)
    
    # Diversify
    diversified = diversify_recommendations(filtered)
    
    # Apply business rules
    final = apply_business_rules(diversified, context)
    
    return final[:limit]


@xray.step("RETRIEVE")
def collaborative_filtering(user: dict) -> list[dict]:
    """Find movies liked by similar users."""
    xray.metric("algorithm", "user-user-knn")
    xray.metric("k_neighbors", 50)
    
    user_ratings = user["watch_history"]
    
    # Find similar users (simplified)
    similar_users = []
    for other_user in USERS:
        if other_user["id"] == user["id"]:
            continue
        
        # Calculate similarity based on common ratings
        common_movies = set(user_ratings.keys()) & set(other_user["watch_history"].keys())
        if len(common_movies) < 3:
            continue
        
        # Pearson correlation (simplified)
        sum_diff = 0
        for movie_id in common_movies:
            sum_diff += abs(user_ratings[movie_id]["rating"] - other_user["watch_history"][movie_id]["rating"])
        
        similarity = 1 / (1 + sum_diff / len(common_movies))
        similar_users.append((other_user, similarity))
    
    similar_users.sort(key=lambda x: x[1], reverse=True)
    top_similar = similar_users[:50]
    
    xray.metric("similar_users_found", len(similar_users))
    
    # Get movies from similar users that this user hasn't watched
    candidates = {}
    for sim_user, similarity in top_similar:
        for movie_id, rating_info in sim_user["watch_history"].items():
            if movie_id not in user_ratings and rating_info["rating"] >= 7.0:
                if movie_id not in candidates:
                    candidates[movie_id] = {"weighted_score": 0, "count": 0}
                candidates[movie_id]["weighted_score"] += rating_info["rating"] * similarity
                candidates[movie_id]["count"] += 1
    
    # Convert to list
    result = []
    for movie_id, scores in candidates.items():
        movie = MOVIE_BY_ID.get(movie_id)
        if movie:
            movie_copy = movie.copy()
            movie_copy["cf_score"] = scores["weighted_score"] / scores["count"]
            movie_copy["cf_support"] = scores["count"]
            movie_copy["source"] = "collaborative"
            result.append(movie_copy)
    
    result.sort(key=lambda x: x["cf_score"], reverse=True)
    return result[:200]


@xray.step("RETRIEVE")
def content_based_filtering(user: dict) -> list[dict]:
    """Find movies similar to what the user likes."""
    xray.metric("algorithm", "content-similarity")
    
    # Build user profile from watch history
    user_profile = {
        "genres": defaultdict(float),
        "directors": defaultdict(float),
        "actors": defaultdict(float),
        "features": defaultdict(float),
    }
    
    history = user["watch_history"]
    total_weight = 0
    
    for movie_id, rating_info in history.items():
        movie = MOVIE_BY_ID.get(movie_id)
        if not movie:
            continue
        
        # Weight by rating
        weight = rating_info["rating"] / 10.0
        total_weight += weight
        
        for genre in movie["genres"]:
            user_profile["genres"][genre] += weight
        user_profile["directors"][movie["director"]] += weight
        for actor in movie["cast"]:
            user_profile["actors"][actor] += weight
        for feature, value in movie["features"].items():
            user_profile["features"][feature] += value * weight
    
    # Normalize
    if total_weight > 0:
        for key in user_profile["features"]:
            user_profile["features"][key] /= total_weight
    
    # Score all unwatched movies
    candidates = []
    for movie in MOVIES:
        if movie["id"] in history:
            continue
        
        score = 0
        
        # Genre match
        for genre in movie["genres"]:
            score += user_profile["genres"].get(genre, 0) * 0.3
        
        # Director match
        score += user_profile["directors"].get(movie["director"], 0) * 0.2
        
        # Actor match
        for actor in movie["cast"]:
            score += user_profile["actors"].get(actor, 0) * 0.1
        
        # Feature similarity
        for feature, user_value in user_profile["features"].items():
            movie_value = movie["features"].get(feature, 0)
            score += (1 - abs(user_value - movie_value)) * 0.05
        
        movie_copy = movie.copy()
        movie_copy["content_score"] = round(score, 4)
        movie_copy["source"] = "content"
        candidates.append(movie_copy)
    
    candidates.sort(key=lambda x: x["content_score"], reverse=True)
    return candidates[:200]


@xray.step("RETRIEVE")
def popularity_based(user: dict) -> list[dict]:
    """Get popular movies as fallback/exploration."""
    xray.metric("algorithm", "popularity")
    
    history = user["watch_history"]
    
    # Filter unwatched and sort by popularity
    candidates = []
    for movie in MOVIES:
        if movie["id"] in history:
            continue
        
        # Popularity score
        pop_score = (
            math.log(movie["vote_count"] + 1) * 0.4 +
            (movie["rating"] / 10.0) * 0.3 +
            (movie["oscar_nominations"] / 10.0) * 0.2 +
            (1 if movie["year"] >= 2020 else 0.5) * 0.1
        )
        
        movie_copy = movie.copy()
        movie_copy["pop_score"] = round(pop_score, 4)
        movie_copy["source"] = "popularity"
        candidates.append(movie_copy)
    
    candidates.sort(key=lambda x: x["pop_score"], reverse=True)
    return candidates[:100]


@xray.step("TRANSFORM")
def merge_candidates(candidate_lists: list[list[dict]]) -> list[dict]:
    """Merge candidates from multiple sources."""
    merged = {}
    
    for candidates in candidate_lists:
        for movie in candidates:
            movie_id = movie["id"]
            if movie_id not in merged:
                merged[movie_id] = movie.copy()
                merged[movie_id]["sources"] = []
            
            # Track sources
            merged[movie_id]["sources"].append(movie.get("source", "unknown"))
            
            # Aggregate scores
            for key in ["cf_score", "content_score", "pop_score"]:
                if key in movie:
                    merged[movie_id][key] = movie[key]
    
    result = list(merged.values())
    xray.metric("total_unique_candidates", len(result))
    xray.metric("multi_source_candidates", sum(1 for m in result if len(m["sources"]) > 1))
    
    return result


@xray.step("RANK")
def score_candidates(candidates: list[dict], user: dict) -> list[dict]:
    """Calculate final scores for all candidates."""
    xray.metric("scoring_model", "gradient-boosted-ranker")
    
    for movie in candidates:
        # Combine different signals
        cf = movie.get("cf_score", 0) * 0.35
        content = movie.get("content_score", 0) * 0.30
        pop = movie.get("pop_score", 0) * 0.15
        
        # Recency boost
        recency = (movie["year"] - 1990) / (2024 - 1990) * 0.10
        
        # Quality boost
        quality = (movie["rating"] / 10.0) * 0.10
        
        final_score = cf + content + pop + recency + quality
        movie["final_score"] = round(final_score, 4)
        
        xray.score(movie, final_score)
    
    return sorted(candidates, key=lambda x: x["final_score"], reverse=True)


@xray.step("FILTER")
def apply_filters(candidates: list[dict], user: dict) -> list[dict]:
    """Apply filtering rules."""
    kept = []
    
    for movie in candidates:
        # Already watched (double-check)
        if movie["id"] in user["watch_history"]:
            xray.drop(movie, "already_watched")
            continue
        
        # Very low rated
        if movie["rating"] < 4.0:
            xray.drop(movie, "low_rating")
            continue
        
        # Very low score
        if movie["final_score"] < 0.1:
            xray.drop(movie, "low_score")
            continue
        
        # Too old (for casual users)
        if user["activity_level"] == "casual" and movie["year"] < 2010:
            xray.drop(movie, "too_old_for_casual")
            continue
        
        kept.append(movie)
    
    return kept


@xray.step("SELECT")
def diversify_recommendations(candidates: list[dict]) -> list[dict]:
    """Ensure diversity in genres and content types."""
    diversified = []
    genre_counts = defaultdict(int)
    director_counts = defaultdict(int)
    
    for movie in candidates:
        primary_genre = movie["primary_genre"]
        director = movie["director"]
        
        # Max 4 per genre
        if genre_counts[primary_genre] >= 4:
            xray.drop(movie, "genre_saturation")
            continue
        
        # Max 2 per director
        if director_counts[director] >= 2:
            xray.drop(movie, "director_saturation")
            continue
        
        diversified.append(movie)
        genre_counts[primary_genre] += 1
        director_counts[director] += 1
        
        if len(diversified) >= 50:
            break
    
    xray.metric("genres_represented", len(genre_counts))
    xray.metric("directors_represented", len(director_counts))
    
    return diversified


@xray.step("TRANSFORM")
def apply_business_rules(candidates: list[dict], context: str) -> list[dict]:
    """Apply business rules and promotions."""
    xray.metric("context", context)
    
    # Boost new releases for home context
    if context == "home":
        for movie in candidates:
            if movie["year"] >= 2023:
                movie["final_score"] *= 1.2
                movie["boosted"] = "new_release"
    
    # For search context, don't apply boosts
    if context == "search":
        pass
    
    # Re-sort after business rules
    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    
    boosted_count = sum(1 for m in candidates if m.get("boosted"))
    xray.metric("boosted_count", boosted_count)
    
    return candidates


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Movie Recommendation System Demo")
    print("=" * 70)
    
    # Sample one user for demo
    test_users = random.sample(USERS, 1)
    
    for user in test_users:
        print(f"\n👤 User: {user['id']}")
        print(f"   Favorite genres: {', '.join(user['favorite_genres'])}")
        print(f"   Watch history: {len(user['watch_history'])} movies")
        print("-" * 50)
        
        recommendations = get_recommendations(user["id"], context="home", limit=10)
        
        print(f"🎬 Top Recommendations:")
        for i, movie in enumerate(recommendations[:5], 1):
            sources = movie.get("sources", ["unknown"])
            print(f"   {i}. {movie['title']} ({movie['year']})")
            print(f"      {movie['primary_genre']} | ★{movie['rating']} | Score: {movie['final_score']:.3f}")
            print(f"      Sources: {', '.join(sources)}")
    
    print("\n" + "=" * 70)
    print("✅ Done! Check http://localhost:3000 for detailed traces")
    print("=" * 70)

