#!/usr/bin/env python3
"""
Content Moderation Pipeline

A multi-stage content moderation system with:
- 1000+ pieces of user-generated content
- Multiple detection layers (spam, toxicity, PII, etc.)
- LLM-based nuanced review
- Human review queue

Run: python examples/content_moderation.py
"""
import zenray
import random
import re
import hashlib
from datetime import datetime, timedelta

zenray.init()

# =============================================================================
# DATASET: User-Generated Content
# =============================================================================

BENIGN_TEMPLATES = [
    "Just finished watching {movie}, absolutely loved it! The cinematography was stunning.",
    "Can anyone recommend a good {genre} book? I'm looking for something new to read.",
    "Had an amazing dinner at {restaurant} last night. The {dish} was incredible!",
    "Working on a new project using {technology}. Any tips for beginners?",
    "Just got back from {city}. Such a beautiful place, highly recommend visiting!",
    "Started learning {skill} today. It's challenging but fun!",
    "My {pet} just did the cutest thing. Love these little moments.",
    "Anyone else excited for the upcoming {event}? Can't wait!",
    "Finally finished my {project}. It took 3 months but worth it!",
    "Great podcast episode about {topic}. Really changed my perspective.",
]

SPAM_PATTERNS = [
    "🔥🔥🔥 CLICK HERE for FREE {product}!!! Limited time only!!! www.scam123.com",
    "Make $10,000 a week from home! DM me for details! 💰💰💰",
    "Congratulations! You've won a {prize}! Click link to claim: bit.ly/scam",
    "Hot singles in your area want to meet YOU! Visit {url}",
    "I made $5000 in one day with this simple trick! {url}",
    "FREE {product} GIVEAWAY!!! Follow + RT + DM to enter!!!",
    "URGENT: Your account will be suspended! Verify now: {phishing_url}",
]

TOXIC_PATTERNS = [
    "You're such an {insult}. Nobody likes you.",
    "This is the dumbest thing I've ever read. The author should be {threat}.",
    "People who like {thing} are complete {insult}s.",
    "{group} are ruining this country. They should all {threat}.",
    "Shut up you {insult}. Nobody asked for your opinion.",
]

PII_TEMPLATES = [
    "My phone number is {phone}, call me anytime!",
    "You can reach me at {email} for more info.",
    "I live at {address}, stop by whenever!",
    "My SSN is {ssn}, need it for the form.",
    "Credit card: {cc_number}, exp: {cc_exp}",
]

NSFW_INDICATORS = ["adult content", "explicit", "18+", "xxx", "nude"]

PLACEHOLDERS = {
    "movie": ["Inception", "The Matrix", "Interstellar", "Parasite", "Dune"],
    "genre": ["mystery", "sci-fi", "romance", "thriller", "fantasy"],
    "restaurant": ["The Olive Garden", "Le Petit Bistro", "Sakura Sushi", "Mama's Kitchen"],
    "dish": ["pasta", "steak", "sushi", "curry", "tacos"],
    "technology": ["React", "Python", "Kubernetes", "TensorFlow", "Rust"],
    "city": ["Paris", "Tokyo", "New York", "Barcelona", "Sydney"],
    "skill": ["guitar", "painting", "cooking", "photography", "coding"],
    "pet": ["dog", "cat", "rabbit", "hamster", "parrot"],
    "event": ["concert", "conference", "game", "festival", "launch"],
    "project": ["website", "app", "garden", "renovation", "book"],
    "topic": ["productivity", "history", "science", "philosophy", "economics"],
    "product": ["iPhone", "Bitcoin", "Weight loss pills", "Designer bags"],
    "prize": ["new iPhone", "$1000 gift card", "free vacation"],
    "url": ["sketchy-site.com", "win-free-stuff.net", "click-here-now.xyz"],
    "phishing_url": ["bank-security-check.com", "verify-account-now.net"],
    "insult": ["idiot", "moron", "loser", "fool"],
    "threat": ["fired", "banned", "ashamed", "gone"],
    "thing": ["pineapple on pizza", "this show", "modern art"],
    "group": ["Those people", "They"],
    "phone": ["555-123-4567", "(555) 987-6543", "555.111.2222"],
    "email": ["john.doe@email.com", "private@personal.net", "user123@mail.com"],
    "address": ["123 Main St, Springfield, IL 62701", "456 Oak Ave, Apt 2B, Chicago"],
    "ssn": ["123-45-6789", "987-65-4321"],
    "cc_number": ["4111-1111-1111-1111", "5500-0000-0000-0004"],
    "cc_exp": ["12/25", "03/26"],
}


def fill_template(template: str) -> str:
    """Fill placeholders in template."""
    result = template
    for key, values in PLACEHOLDERS.items():
        placeholder = "{" + key + "}"
        while placeholder in result:
            result = result.replace(placeholder, random.choice(values), 1)
    return result


def generate_content(count: int = 1000) -> list[dict]:
    """Generate a mix of user content."""
    content = []
    
    # Distribution: 85% benign, 8% spam, 4% toxic, 2% PII, 1% mixed
    for i in range(count):
        roll = random.random()
        
        if roll < 0.85:
            # Benign content
            text = fill_template(random.choice(BENIGN_TEMPLATES))
            category = "benign"
        elif roll < 0.93:
            # Spam
            text = fill_template(random.choice(SPAM_PATTERNS))
            category = "spam"
        elif roll < 0.97:
            # Toxic
            text = fill_template(random.choice(TOXIC_PATTERNS))
            category = "toxic"
        elif roll < 0.99:
            # PII
            text = fill_template(random.choice(PII_TEMPLATES))
            category = "pii"
        else:
            # Mixed (toxic + spam)
            text = fill_template(random.choice(TOXIC_PATTERNS)) + " " + fill_template(random.choice(SPAM_PATTERNS))
            category = "mixed"
        
        # Add some noise
        if random.random() < 0.1:
            text = text.upper() if random.random() < 0.5 else text.lower()
        
        content_id = hashlib.md5(f"{i}-{text[:20]}".encode()).hexdigest()[:12]
        
        content.append({
            "id": f"CONTENT-{content_id}",
            "text": text,
            "ground_truth": category,
            "user_id": f"USER-{random.randint(1, 10000):05d}",
            "created_at": (datetime.now() - timedelta(minutes=random.randint(1, 10000))).isoformat(),
            "platform": random.choice(["web", "ios", "android"]),
            "content_type": random.choice(["comment", "post", "message", "review"]),
            "parent_id": f"PARENT-{random.randint(1, 1000):04d}" if random.random() < 0.3 else None,
        })
    
    return content


# Generate content
CONTENT = generate_content(1000)
print(f"Generated {len(CONTENT)} content items")

# Distribution check
from collections import Counter
distribution = Counter(c["ground_truth"] for c in CONTENT)
print(f"Distribution: {dict(distribution)}")


# =============================================================================
# MODERATION PIPELINE
# =============================================================================

@zenray.pipeline("content-moderation", version="v5.2.0")
def moderate_content(content_id: str) -> dict:
    """
    Full content moderation pipeline.
    
    Stages:
    1. Pre-filters (spam detection, keyword blocklist)
    2. ML classifiers (toxicity, NSFW)
    3. PII detection
    4. LLM nuanced review (for borderline cases)
    5. Final decision
    """
    content = next((c for c in CONTENT if c["id"] == content_id), None)
    if not content:
        return {"decision": "error", "reason": "content_not_found"}
    
    zenray.tag("content_type", content["content_type"])
    zenray.tag("platform", content["platform"])
    zenray.tag("user_id", content["user_id"])
    
    # Run detection stages
    spam_result = detect_spam(content)
    if spam_result["is_spam"]:
        return finalize_decision(content, "reject", "spam", spam_result["confidence"])
    
    toxicity_result = detect_toxicity(content)
    if toxicity_result["is_toxic"] and toxicity_result["confidence"] > 0.9:
        return finalize_decision(content, "reject", "toxicity", toxicity_result["confidence"])
    
    pii_result = detect_pii(content)
    if pii_result["has_pii"]:
        return finalize_decision(content, "redact", "pii_detected", pii_result["confidence"])
    
    nsfw_result = detect_nsfw(content)
    if nsfw_result["is_nsfw"]:
        return finalize_decision(content, "reject", "nsfw", nsfw_result["confidence"])
    
    # Borderline cases go to LLM review
    if toxicity_result["confidence"] > 0.5:
        llm_result = llm_nuanced_review(content, toxicity_result)
        if llm_result["recommendation"] == "reject":
            return finalize_decision(content, "reject", "llm_toxic", llm_result["confidence"])
        elif llm_result["recommendation"] == "review":
            return finalize_decision(content, "human_review", "borderline", llm_result["confidence"])
    
    return finalize_decision(content, "approve", "passed_all_checks", 0.95)


@zenray.step("FILTER")
def detect_spam(content: dict) -> dict:
    """Detect spam content."""
    zenray.set_input_count(1)  # Single content item
    
    text = content["text"].lower()
    signals = []
    
    # URL patterns
    url_pattern = r'(https?://|www\.|\w+\.(com|net|org|xyz|io|ly))'
    urls = re.findall(url_pattern, text.lower())
    if urls:
        signals.append(("has_urls", 0.3))
    
    # Excessive caps
    caps_ratio = sum(1 for c in content["text"] if c.isupper()) / max(1, len(content["text"]))
    if caps_ratio > 0.5:
        signals.append(("excessive_caps", 0.2))
    
    # Excessive punctuation
    if content["text"].count("!") > 3 or content["text"].count("?") > 3:
        signals.append(("excessive_punctuation", 0.2))
    
    # Money mentions
    money_patterns = ["$", "money", "free", "win", "click", "limited time", "act now"]
    for pattern in money_patterns:
        if pattern in text:
            signals.append((f"has_{pattern.replace(' ', '_')}", 0.15))
    
    # Emoji spam
    emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]', content["text"]))
    if emoji_count > 5:
        signals.append(("emoji_spam", 0.2))
    
    # Calculate confidence
    confidence = min(1.0, sum(s[1] for s in signals))
    is_spam = confidence > 0.6
    
    # Record output: 0 if spam (dropped), 1 if passed
    zenray.set_output_count(0 if is_spam else 1)
    
    if is_spam:
        zenray.drop(content, "spam_detected")
    
    zenray.metric("spam_signals", [s[0] for s in signals])
    zenray.metric("spam_confidence", confidence)
    zenray.score(content, 1 - confidence)  # Score as "safe"
    
    return {
        "is_spam": is_spam,
        "confidence": round(confidence, 3),
        "signals": signals,
    }


@zenray.step("JUDGE")
def detect_toxicity(content: dict) -> dict:
    """Detect toxic content using ML classifier (simulated)."""
    zenray.set_input_count(1)
    
    text = content["text"].lower()
    
    zenray.metric("model", "distilbert-toxic-classifier")
    zenray.artifact("input", {"text": text[:200]})
    
    # Simulate ML classifier
    toxic_words = ["idiot", "moron", "stupid", "hate", "shut up", "loser", "dumb", "fool"]
    threat_words = ["kill", "die", "hurt", "destroy", "attack"]
    
    toxic_score = 0
    matched_words = []
    
    for word in toxic_words:
        if word in text:
            toxic_score += 0.3
            matched_words.append(word)
    
    for word in threat_words:
        if word in text:
            toxic_score += 0.5
            matched_words.append(word)
    
    # Caps penalty
    caps_ratio = sum(1 for c in content["text"] if c.isupper()) / max(1, len(content["text"]))
    if caps_ratio > 0.5:
        toxic_score *= 1.3
    
    confidence = min(1.0, toxic_score)
    is_toxic = confidence > 0.5
    
    zenray.artifact("output", {
        "toxic_score": confidence,
        "matched_words": matched_words,
    })
    
    if is_toxic and confidence > 0.9:
        zenray.drop(content, "high_toxicity")
    
    zenray.score(content, 1 - confidence)  # Score as "safe"
    zenray.set_output_count(0 if is_toxic and confidence > 0.9 else 1)
    
    return {
        "is_toxic": is_toxic,
        "confidence": round(confidence, 3),
        "categories": matched_words,
    }


@zenray.step("FILTER")
def detect_pii(content: dict) -> dict:
    """Detect personally identifiable information."""
    zenray.set_input_count(1)
    text = content["text"]
    
    pii_types = []
    
    # Phone numbers
    phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    if re.search(phone_pattern, text):
        pii_types.append("phone_number")
    
    # Email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, text):
        pii_types.append("email")
    
    # SSN
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    if re.search(ssn_pattern, text):
        pii_types.append("ssn")
    
    # Credit card
    cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    if re.search(cc_pattern, text):
        pii_types.append("credit_card")
    
    # Address patterns (simplified)
    address_pattern = r'\d+\s+\w+\s+(st|street|ave|avenue|rd|road|blvd|dr|drive)'
    if re.search(address_pattern, text.lower()):
        pii_types.append("address")
    
    has_pii = len(pii_types) > 0
    confidence = min(1.0, len(pii_types) * 0.4)
    
    if has_pii:
        zenray.drop(content, f"pii_detected_{','.join(pii_types)}")
    
    zenray.metric("pii_types_found", pii_types)
    zenray.set_output_count(0 if has_pii else 1)
    
    return {
        "has_pii": has_pii,
        "confidence": round(confidence, 3),
        "pii_types": pii_types,
    }


@zenray.step("FILTER")
def detect_nsfw(content: dict) -> dict:
    """Detect NSFW content."""
    zenray.set_input_count(1)
    text = content["text"].lower()
    
    # Check for NSFW indicators
    matches = [ind for ind in NSFW_INDICATORS if ind in text]
    
    is_nsfw = len(matches) > 0
    confidence = min(1.0, len(matches) * 0.4)
    
    if is_nsfw:
        zenray.drop(content, "nsfw_content")
    
    zenray.metric("nsfw_matches", matches)
    zenray.set_output_count(0 if is_nsfw else 1)
    
    return {
        "is_nsfw": is_nsfw,
        "confidence": round(confidence, 3),
        "matches": matches,
    }


@zenray.step("LLM_CALL")
def llm_nuanced_review(content: dict, toxicity_result: dict) -> dict:
    """Use LLM for nuanced content review."""
    prompt = f"""Review this content for policy violations:

Content: "{content['text']}"

Toxicity signals detected: {toxicity_result['categories']}
Confidence: {toxicity_result['confidence']}

Analyze if this content:
1. Contains genuine harassment or hate speech
2. Uses offensive language in a non-harmful context (e.g., quoting, discussing)
3. Is borderline and needs human review

Respond with: APPROVE, REJECT, or REVIEW"""

    zenray.artifact("prompt", prompt)
    zenray.metric("model", "gpt-4-turbo")
    
    # Simulate LLM response
    if toxicity_result["confidence"] > 0.8:
        recommendation = "reject"
        reasoning = "Content contains clear policy violations with high-confidence toxic signals."
    elif toxicity_result["confidence"] > 0.6:
        recommendation = "review"
        reasoning = "Content is borderline and may require human judgment for context."
    else:
        recommendation = "approve"
        reasoning = "Content uses potentially sensitive language but in acceptable context."
    
    response = f"""Based on my analysis:

The content shows {toxicity_result['confidence']*100:.0f}% toxicity confidence.
Detected signals: {', '.join(toxicity_result['categories'])}

{reasoning}

Recommendation: {recommendation.upper()}"""

    zenray.artifact("response", response)
    zenray.metric("recommendation", recommendation)
    
    return {
        "recommendation": recommendation,
        "confidence": round(random.uniform(0.7, 0.95), 2),
        "reasoning": reasoning,
    }


@zenray.step("SELECT")
def finalize_decision(content: dict, decision: str, reason: str, confidence: float) -> dict:
    """Finalize the moderation decision."""
    zenray.set_input_count(1)
    zenray.set_output_count(1 if decision == "approve" else 0)
    
    zenray.metric("decision", decision)
    zenray.metric("reason", reason)
    zenray.metric("confidence", confidence)
    
    # Actions based on decision
    actions = {
        "approve": [],
        "reject": ["delete_content", "notify_user", "log_violation"],
        "redact": ["mask_pii", "allow_content"],
        "human_review": ["add_to_queue", "flag_for_review"],
    }
    
    result = {
        "content_id": content["id"],
        "decision": decision,
        "reason": reason,
        "confidence": confidence,
        "actions": actions.get(decision, []),
        "processed_at": datetime.now().isoformat(),
    }
    
    # Track accuracy against ground truth (for demo)
    ground_truth = content["ground_truth"]
    is_correct = (
        (decision == "approve" and ground_truth == "benign") or
        (decision == "reject" and ground_truth in ["spam", "toxic", "mixed"]) or
        (decision == "redact" and ground_truth == "pii")
    )
    
    zenray.metric("ground_truth", ground_truth)
    zenray.metric("correct_decision", is_correct)
    
    return result


# =============================================================================
# BATCH PROCESSING (Realistic multi-item pipeline)
# =============================================================================

@zenray.pipeline("content-moderation-batch", version="v2.0.0")
def moderate_batch(content_items: list[dict]) -> dict:
    """
    Process a batch of content items through the moderation pipeline.
    
    This shows realistic drop rates across multiple stages.
    """
    zenray.tag("batch_size", str(len(content_items)))
    
    # Stage 1: Spam filter
    after_spam = batch_spam_filter(content_items)
    
    # Stage 2: Toxicity filter
    after_toxicity = batch_toxicity_filter(after_spam)
    
    # Stage 3: PII filter
    after_pii = batch_pii_filter(after_toxicity)
    
    # Stage 4: NSFW filter
    after_nsfw = batch_nsfw_filter(after_pii)
    
    # Stage 5: Final approval
    approved = batch_approve(after_nsfw)
    
    return {
        "input_count": len(content_items),
        "approved_count": len(approved),
        "approval_rate": len(approved) / len(content_items) if content_items else 0,
        "approved_ids": [c["id"] for c in approved],
    }


@zenray.step("FILTER")
def batch_spam_filter(items: list[dict]) -> list[dict]:
    """Filter spam from batch."""
    kept = []
    
    for content in items:
        text = content["text"].lower()
        
        # Spam signals
        spam_score = 0
        if any(p in text for p in ["click here", "www.", ".com", ".net", ".xyz"]):
            spam_score += 0.3
        if any(p in text for p in ["free", "win", "$", "money", "cash"]):
            spam_score += 0.3
        if content["text"].count("!") > 3:
            spam_score += 0.2
        if len(re.findall(r'[\U0001F600-\U0001F6FF]', content["text"])) > 5:
            spam_score += 0.2
        
        is_spam = spam_score > 0.5
        zenray.score(content, 1 - spam_score)
        
        if is_spam:
            zenray.drop(content, "spam")
        else:
            kept.append(content)
    
    zenray.metric("spam_detected", len(items) - len(kept))
    return kept


@zenray.step("JUDGE")
def batch_toxicity_filter(items: list[dict]) -> list[dict]:
    """Filter toxic content from batch."""
    zenray.metric("model", "distilbert-toxic-classifier")
    
    kept = []
    toxic_words = ["idiot", "moron", "stupid", "hate", "shut up", "loser", "dumb", "fool"]
    
    for content in items:
        text = content["text"].lower()
        
        toxic_score = sum(0.3 for w in toxic_words if w in text)
        toxic_score = min(1.0, toxic_score)
        
        is_toxic = toxic_score > 0.5
        zenray.score(content, 1 - toxic_score)
        
        if is_toxic:
            zenray.drop(content, "toxic")
        else:
            kept.append(content)
    
    zenray.metric("toxic_detected", len(items) - len(kept))
    return kept


@zenray.step("FILTER")
def batch_pii_filter(items: list[dict]) -> list[dict]:
    """Filter content with PII from batch."""
    kept = []
    
    phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    
    for content in items:
        text = content["text"]
        
        has_phone = bool(re.search(phone_pattern, text))
        has_email = bool(re.search(email_pattern, text))
        has_ssn = bool(re.search(ssn_pattern, text))
        
        has_pii = has_phone or has_email or has_ssn
        
        if has_pii:
            reason = []
            if has_phone: reason.append("phone")
            if has_email: reason.append("email")
            if has_ssn: reason.append("ssn")
            zenray.drop(content, f"pii:{','.join(reason)}")
        else:
            kept.append(content)
    
    zenray.metric("pii_detected", len(items) - len(kept))
    return kept


@zenray.step("FILTER")
def batch_nsfw_filter(items: list[dict]) -> list[dict]:
    """Filter NSFW content from batch."""
    kept = []
    
    for content in items:
        text = content["text"].lower()
        
        is_nsfw = any(ind in text for ind in NSFW_INDICATORS)
        
        if is_nsfw:
            zenray.drop(content, "nsfw")
        else:
            kept.append(content)
    
    zenray.metric("nsfw_detected", len(items) - len(kept))
    return kept


@zenray.step("SELECT")
def batch_approve(items: list[dict]) -> list[dict]:
    """Final approval - all remaining items pass."""
    for content in items:
        zenray.score(content, 1.0)  # Approved items get perfect score
    
    zenray.metric("approved_count", len(items))
    return items


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Content Moderation Pipeline Demo")
    print("=" * 70)
    
    # Process individual items (single-item pipeline)
    print("\n📝 Individual Content Moderation (5 samples)")
    print("-" * 50)
    
    # Sample one of each type
    samples = {}
    for c in CONTENT:
        if c["ground_truth"] not in samples:
            samples[c["ground_truth"]] = c
    
    for category, content in list(samples.items())[:3]:
        print(f"\n🔍 Content Type: {category.upper()}")
        print(f"   Text: {content['text'][:60]}...")
        
        result = moderate_content(content["id"])
        
        print(f"   Decision: {result['decision'].upper()}")
        print(f"   Reason: {result['reason']}")
        print(f"   Confidence: {result['confidence']:.0%}")
    
    # Batch processing - THIS SHOWS REAL DROP RATES
    print("\n\n📊 Batch Processing (500 items - shows real drop rates!)")
    print("-" * 50)
    
    # Process 500 items in one batch
    batch_items = random.sample(CONTENT, 500)
    batch_result = moderate_batch(batch_items)
    
    print(f"Input:    {batch_result['input_count']} items")
    print(f"Approved: {batch_result['approved_count']} items")
    print(f"Approval Rate: {batch_result['approval_rate']*100:.1f}%")
    print(f"Drop Rate: {(1 - batch_result['approval_rate'])*100:.1f}%")
    
    # Run another batch with 200 items
    print("\n📊 Second Batch (200 items)")
    print("-" * 50)
    
    batch_items_2 = random.sample(CONTENT, 200)
    batch_result_2 = moderate_batch(batch_items_2)
    
    print(f"Input:    {batch_result_2['input_count']} items")
    print(f"Approved: {batch_result_2['approved_count']} items")
    print(f"Approval Rate: {batch_result_2['approval_rate']*100:.1f}%")
    
    print("\n" + "=" * 70)
    print("✅ Done! Check http://localhost:3000 for detailed traces")
    print("   Look at 'content-moderation-batch' runs to see DROP RATES!")
    print("=" * 70)

