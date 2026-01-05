#!/usr/bin/env python3
"""
Enterprise Job Application Screening Pipeline - X-Ray Demo

A comprehensive 12-stage screening pipeline with 2000-4000 candidates.

This example demonstrates X-Ray's debugging capabilities:

1. DEPTH ANALYSIS
   - See drop rates at each of 12 pipeline stages
   - Identify bottlenecks (which stage drops the most?)
   - Understand WHY candidates are being filtered (reason histograms)
   - View score distributions to tune thresholds

2. CANDIDATE SEARCH (Trace)
   - Search for any applicant by name/ID
   - See their journey through all 12 stages
   - Understand exactly WHERE and WHY they were rejected

PIPELINE STAGES:
  1. Resume Parsing         - Parse and validate resume format
  2. Duplicate Detection    - Remove duplicate applications
  3. Basic Eligibility      - Age, work authorization, location
  4. Skills Matching        - Required and preferred skills
  5. Experience Evaluation  - Years, relevance, progression
  6. Education Verification - Degree, GPA, institution
  7. Background Screening   - Employment gaps, red flags
  8. Technical Assessment   - Coding test scores
  9. Culture Fit            - Values alignment, team fit
  10. Compensation Check    - Salary expectations vs budget
  11. Availability Check    - Start date, notice period
  12. Final Selection       - Top N for interview slots

Run: python examples/job_screening_pipeline.py
Then: Open http://localhost:3000 to explore the trace
"""
import zenray
import random
import hashlib
from datetime import datetime, timedelta
from typing import Optional

zenray.init()

# =============================================================================
# EXTENSIVE DATASET: 2000-4000 Job Applicants
# =============================================================================

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Aisha", "Wei", "Priya", "Carlos", "Fatima", "Hiroshi", "Olga", "Ahmed",
    "Svetlana", "Kumar", "Yuki", "Maria", "Chen", "Amara", "Raj", "Elena",
    "Oliver", "Emma", "Liam", "Sophia", "Noah", "Ava", "Ethan", "Isabella",
    "Lucas", "Mia", "Mason", "Charlotte", "Logan", "Amelia", "Alexander", "Harper",
    "Sebastian", "Evelyn", "Jack", "Abigail", "Aiden", "Ella", "Owen", "Avery",
    "Samuel", "Scarlett", "Ryan", "Grace", "Nathan", "Chloe", "Caleb", "Victoria",
    "Dylan", "Riley", "Luke", "Aria", "Gabriel", "Lily", "Henry", "Aurora",
    "Jayden", "Zoey", "Leo", "Penelope", "Isaac", "Layla", "Lincoln", "Nora",
    "Muhammad", "Camila", "Julian", "Hannah", "Mateo", "Addison", "Levi", "Eleanor",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Patel", "Kim", "Nguyen", "Chen", "Wang", "Singh", "Kumar", "Ali", "Zhang",
    "Liu", "Yamamoto", "Tanaka", "Ivanova", "Petrov", "Mueller", "Schmidt", "Costa",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales",
    "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson",
    "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
]

UNIVERSITIES = [
    # Tier 1: Elite
    ("MIT", 98), ("Stanford", 97), ("Carnegie Mellon", 95), ("Harvard", 95),
    ("Caltech", 94), ("Princeton", 93), ("Yale", 92), ("Columbia", 91),
    # Tier 2: Excellent
    ("UC Berkeley", 90), ("Georgia Tech", 89), ("UIUC", 88), ("University of Michigan", 87),
    ("Cornell", 87), ("UCLA", 86), ("UT Austin", 85), ("University of Washington", 85),
    # Tier 3: Very Good
    ("Purdue", 82), ("Penn State", 80), ("Wisconsin", 80), ("Virginia Tech", 79),
    ("NC State", 78), ("Ohio State", 77), ("USC", 77), ("Boston University", 76),
    # Tier 4: Good
    ("Arizona State", 72), ("University of Colorado", 71), ("Northeastern", 70),
    ("RIT", 69), ("Drexel", 68), ("San Jose State", 67), ("Florida State", 66),
    # Tier 5: Average
    ("State University", 60), ("Regional College", 55), ("Community College", 50),
    # Tier 6: Non-traditional
    ("Online Bootcamp - Hack Reactor", 58), ("Online Bootcamp - App Academy", 56),
    ("Online Bootcamp - General Assembly", 52), ("Self-taught", 45), ("No Degree", 40),
]

SKILLS = {
    "required": ["Python", "SQL", "Git"],
    "highly_preferred": ["AWS", "Docker", "Kubernetes"],
    "preferred": ["React", "TypeScript", "Go", "Java", "PostgreSQL", "Redis"],
    "bonus": ["Machine Learning", "System Design", "Leadership", "Agile", "GraphQL", "Terraform"],
    "languages": ["English", "Spanish", "Mandarin", "Hindi", "French", "German", "Japanese"],
}

COMPANIES = [
    # FAANG+
    ("Google", 100), ("Meta", 98), ("Amazon", 97), ("Apple", 97), ("Microsoft", 96),
    ("Netflix", 94), ("NVIDIA", 93),
    # Top Tech
    ("Stripe", 92), ("Airbnb", 90), ("Uber", 89), ("LinkedIn", 88), ("Twitter", 87),
    ("Salesforce", 86), ("Adobe", 85), ("Spotify", 84), ("Shopify", 83),
    # Growth Stage
    ("Databricks", 82), ("Snowflake", 81), ("Figma", 80), ("Notion", 79),
    ("Discord", 78), ("Plaid", 77), ("Ramp", 76), ("Rippling", 75),
    # Mid-tier
    ("Oracle", 72), ("IBM", 70), ("Cisco", 69), ("Intel", 68), ("Dell", 67),
    ("HP", 66), ("VMware", 65), ("SAP", 64),
    # Consulting
    ("McKinsey", 75), ("Bain", 74), ("BCG", 73), ("Deloitte", 65), ("Accenture", 62),
    # Startups
    ("Series A Startup", 60), ("Series B Startup", 58), ("Seed Startup", 55),
    ("Local Agency", 50), ("Freelance", 48), ("Unrelated Industry", 40),
]

REFERRAL_SOURCES = [
    "LinkedIn", "Employee Referral", "Career Fair", "Company Website", 
    "Indeed", "AngelList", "Hired.com", "Glassdoor", "Hacker News Jobs",
    "University Career Center", "Conference", "GitHub", "Stack Overflow"
]

LOCATIONS = [
    ("San Francisco, CA", True), ("New York, NY", True), ("Seattle, WA", True),
    ("Austin, TX", True), ("Boston, MA", True), ("Denver, CO", True),
    ("Los Angeles, CA", True), ("Chicago, IL", True), ("Atlanta, GA", True),
    ("Remote - US", True), ("Remote - International", False),
    ("London, UK", False), ("Toronto, Canada", False), ("Berlin, Germany", False),
    ("Bangalore, India", False), ("Singapore", False), ("Sydney, Australia", False),
]


def generate_applicants(count: int) -> list[dict]:
    """Generate realistic job applicants with varied backgrounds."""
    applicants = []
    
    for i in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        
        # Education
        university, uni_prestige = random.choice(UNIVERSITIES)
        degree = random.choice(["BS Computer Science", "MS Computer Science", "BS Software Engineering",
                                 "MS Data Science", "PhD Computer Science", "BS Mathematics", 
                                 "Bootcamp Certificate", "Self-taught", "BS Electrical Engineering"])
        gpa = round(random.gauss(3.2, 0.5), 2)
        gpa = max(2.0, min(4.0, gpa))
        graduation_year = random.randint(2005, 2024)
        
        # Experience
        years_exp = max(0, random.gauss(6, 4))
        years_exp = round(min(25, years_exp), 1)
        
        # Work history (1-6 previous jobs)
        num_jobs = min(6, max(1, int(years_exp / 2) + random.randint(0, 2)))
        work_history = []
        for j in range(num_jobs):
            company, company_prestige = random.choice(COMPANIES)
            duration = round(random.uniform(0.3, 5), 1)
            title_level = random.choice(["Junior", "Mid-level", "Senior", "Staff", "Principal", "Lead"])
            work_history.append({
                "company": company,
                "prestige": company_prestige,
                "duration_years": duration,
                "title": f"{title_level} Software Engineer",
                "left_reason": random.choice(["Growth", "Layoff", "Better Offer", "Relocation", "Current"]),
            })
        
        # Skills
        has_all_required = random.random() > 0.20  # 80% have all required skills
        if has_all_required:
            skills = SKILLS["required"].copy()
        else:
            skills = random.sample(SKILLS["required"], k=random.randint(0, 2))
        
        skills += random.sample(SKILLS["highly_preferred"], k=random.randint(0, 3))
        skills += random.sample(SKILLS["preferred"], k=random.randint(0, 5))
        skills += random.sample(SKILLS["bonus"], k=random.randint(0, 3))
        languages = random.sample(SKILLS["languages"], k=random.randint(1, 3))
        
        # Technical assessment (simulated coding test)
        took_assessment = random.random() > 0.15  # 85% complete the test
        if took_assessment:
            coding_score = random.gauss(65, 20)
            coding_score = max(0, min(100, coding_score))
            system_design_score = random.gauss(60, 25)
            system_design_score = max(0, min(100, system_design_score))
        else:
            coding_score = None
            system_design_score = None
        
        # Resume quality
        resume_quality = random.choices(
            ["excellent", "good", "average", "poor", "unparseable"],
            weights=[15, 35, 30, 15, 5]
        )[0]
        
        # Location and authorization
        location, us_authorized = random.choice(LOCATIONS)
        needs_sponsorship = not us_authorized and random.random() > 0.3
        
        # Application metadata
        applied_date = datetime.now() - timedelta(days=random.randint(1, 45))
        source = random.choice(REFERRAL_SOURCES)
        
        # Salary expectations
        base_expectation = 100000 + (years_exp * 10000) + (uni_prestige * 200)
        salary_expectation = int(base_expectation * random.uniform(0.7, 1.6))
        
        # Availability
        notice_period = random.choice([0, 14, 21, 30, 45, 60, 90, 120])
        earliest_start = datetime.now() + timedelta(days=notice_period + random.randint(0, 14))
        
        # Employment gaps
        has_gap = random.random() > 0.85  # 15% have gaps
        gap_months = random.randint(3, 24) if has_gap else 0
        gap_reason = random.choice(["Personal", "Health", "Caregiving", "Travel", "Education", "Startup"]) if has_gap else None
        
        # Red flags
        has_criminal_record = random.random() > 0.98  # 2%
        failed_reference = random.random() > 0.95  # 5%
        
        # Culture indicators
        values_alignment = random.uniform(0.3, 1.0)
        communication_score = random.gauss(70, 15)
        collaboration_preference = random.choice(["Team-oriented", "Independent", "Hybrid"])
        
        # Generate unique ID
        applicant_id = hashlib.md5(f"{first}{last}{i}{random.random()}".encode()).hexdigest()[:8].upper()
        
        applicants.append({
            "id": f"APP-{applicant_id}",
            "name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}{random.randint(1,999)}@email.com",
            "phone": f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
            "age": max(21, min(65, 22 + int(years_exp) + random.randint(-2, 5))),
            
            # Education
            "university": university,
            "university_prestige": uni_prestige,
            "degree": degree,
            "gpa": gpa,
            "graduation_year": graduation_year,
            
            # Experience
            "years_experience": years_exp,
            "work_history": work_history,
            "current_company": work_history[-1]["company"] if work_history else None,
            "current_title": work_history[-1]["title"] if work_history else None,
            
            # Skills
            "skills": list(set(skills)),
            "languages": languages,
            "has_required_skills": all(s in skills for s in SKILLS["required"]),
            
            # Technical Assessment
            "took_assessment": took_assessment,
            "coding_score": round(coding_score, 1) if coding_score else None,
            "system_design_score": round(system_design_score, 1) if system_design_score else None,
            
            # Resume
            "resume_quality": resume_quality,
            "resume_keywords": random.randint(5, 25),
            
            # Location & Authorization
            "location": location,
            "us_authorized": us_authorized,
            "needs_sponsorship": needs_sponsorship,
            "willing_to_relocate": random.random() > 0.4,
            
            # Application
            "applied_date": applied_date.isoformat(),
            "source": source,
            "is_referral": source == "Employee Referral",
            
            # Compensation
            "salary_expectation": salary_expectation,
            "equity_expectation": random.choice(["Low", "Medium", "High", "Very High"]),
            
            # Availability
            "notice_period_days": notice_period,
            "earliest_start": earliest_start.isoformat(),
            "open_to_contract": random.random() > 0.7,
            
            # Background
            "has_employment_gap": has_gap,
            "gap_months": gap_months,
            "gap_reason": gap_reason,
            "criminal_record": has_criminal_record,
            "reference_issue": failed_reference,
            
            # Culture
            "values_alignment": round(values_alignment, 2),
            "communication_score": round(min(100, max(0, communication_score)), 1),
            "collaboration_style": collaboration_preference,
            
            # Scores (computed during pipeline)
            "resume_score": None,
            "skills_score": None,
            "experience_score": None,
            "education_score": None,
            "technical_score": None,
            "culture_score": None,
            "final_score": None,
        })
    
    return applicants


# Generate applicants (random between 2000-4000)
APPLICANT_COUNT = random.randint(2000, 4000)
print(f"Generating {APPLICANT_COUNT} job applicants...")
APPLICANTS = generate_applicants(APPLICANT_COUNT)
print(f"Generated {len(APPLICANTS)} applicants from {len(set(a['source'] for a in APPLICANTS))} sources")
print(f"Locations: {len(set(a['location'] for a in APPLICANTS))} unique")
print(f"Companies: {len(set(a['current_company'] for a in APPLICANTS if a['current_company']))} unique")


# =============================================================================
# 12-STAGE SCREENING PIPELINE
# =============================================================================

@zenray.pipeline("enterprise-engineer-screening", version="v3.0.0")
def screen_applicants(job_id: str, position: str = "Senior Software Engineer", max_interviews: int = 30) -> list[dict]:
    """
    Enterprise 12-stage applicant screening pipeline.
    
    STAGES:
    1. Resume Parsing         - Parse and validate resume format
    2. Duplicate Detection    - Remove duplicate applications  
    3. Basic Eligibility      - Age, work authorization, location
    4. Skills Matching        - Required and preferred skills
    5. Experience Evaluation  - Years, relevance, career progression
    6. Education Verification - Degree, GPA, institution tier
    7. Background Screening   - Employment gaps, red flags
    8. Technical Assessment   - Coding test and system design scores
    9. Culture Fit           - Values alignment, communication
    10. Compensation Check    - Salary expectations vs budget
    11. Availability Check    - Start date, notice period
    12. Final Selection       - Top N for interview slots
    """
    zenray.tag("job_id", job_id)
    zenray.tag("position", position)
    zenray.tag("total_applicants", str(len(APPLICANTS)))
    zenray.tag("max_interviews", str(max_interviews))
    
    # Stage 1: Resume Parsing
    stage1 = parse_resumes(APPLICANTS)
    
    # Stage 2: Duplicate Detection
    stage2 = detect_duplicates(stage1)
    
    # Stage 3: Basic Eligibility
    stage3 = check_eligibility(stage2)
    
    # Stage 4: Skills Matching
    stage4 = match_skills(stage3)
    
    # Stage 5: Experience Evaluation
    stage5 = evaluate_experience(stage4)
    
    # Stage 6: Education Verification
    stage6 = verify_education(stage5)
    
    # Stage 7: Background Screening
    stage7 = screen_background(stage6)
    
    # Stage 8: Technical Assessment
    stage8 = evaluate_technical(stage7)
    
    # Stage 9: Culture Fit
    stage9 = assess_culture(stage8)
    
    # Stage 10: Compensation Check
    stage10 = check_compensation(stage9)
    
    # Stage 11: Availability Check
    stage11 = check_availability(stage10)
    
    # Stage 12: Final Selection
    final = select_interviews(stage11, max_interviews)
    
    return final


# -----------------------------------------------------------------------------
# STAGE 1: Resume Parsing
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def parse_resumes(applicants: list[dict]) -> list[dict]:
    """
    Stage 1: Parse and validate resume format.
    
    DROP REASONS:
    - unparseable_resume: PDF/format issues, images only, corrupted
    - poor_formatting: Parseable but extremely poor quality
    - missing_contact: No valid email or phone
    - suspicious_content: Detected AI-generated or plagiarized content
    """
    zenray.metric("stage", 1)
    zenray.metric("stage_name", "resume_parsing")
    
    kept = []
    
    for applicant in applicants:
        # Unparseable check
        if applicant["resume_quality"] == "unparseable":
            zenray.drop(applicant, "unparseable_resume")
            continue
        
        # Poor formatting
        if applicant["resume_quality"] == "poor" and random.random() > 0.5:
            zenray.drop(applicant, "poor_formatting")
            continue
        
        # Missing contact (simulated)
        if random.random() < 0.02:
            zenray.drop(applicant, "missing_contact_info")
            continue
        
        # Suspicious content detection (AI-generated resumes)
        if random.random() < 0.03:
            zenray.drop(applicant, "suspicious_ai_generated")
            continue
        
        # Compute resume score
        quality_scores = {"excellent": 1.0, "good": 0.85, "average": 0.65, "poor": 0.4}
        applicant["resume_score"] = quality_scores.get(applicant["resume_quality"], 0.5)
        
        kept.append(applicant)
    
    zenray.metric("pass_rate", len(kept) / len(applicants) if applicants else 0)
    return kept


# -----------------------------------------------------------------------------
# STAGE 2: Duplicate Detection
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def detect_duplicates(applicants: list[dict]) -> list[dict]:
    """
    Stage 2: Remove duplicate applications.
    
    DROP REASONS:
    - duplicate_email: Same email already seen
    - duplicate_phone: Same phone number
    - duplicate_name_company: Same name + current company (likely same person)
    """
    zenray.metric("stage", 2)
    zenray.metric("stage_name", "duplicate_detection")
    
    kept = []
    seen_emails = set()
    seen_phones = set()
    seen_name_company = set()
    
    for applicant in applicants:
        email = applicant["email"].lower()
        phone = applicant["phone"]
        name_company = f"{applicant['name'].lower()}_{applicant['current_company']}"
        
        if email in seen_emails:
            zenray.drop(applicant, "duplicate_email")
            continue
        
        if phone in seen_phones:
            zenray.drop(applicant, "duplicate_phone")
            continue
        
        if name_company in seen_name_company and applicant["current_company"]:
            zenray.drop(applicant, "duplicate_name_company")
            continue
        
        seen_emails.add(email)
        seen_phones.add(phone)
        if applicant["current_company"]:
            seen_name_company.add(name_company)
        
        kept.append(applicant)
    
    zenray.metric("duplicates_removed", len(applicants) - len(kept))
    return kept


# -----------------------------------------------------------------------------
# STAGE 3: Basic Eligibility
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def check_eligibility(applicants: list[dict]) -> list[dict]:
    """
    Stage 3: Basic eligibility checks.
    
    DROP REASONS:
    - age_requirement: Under 18 or retirement age concerns
    - no_work_authorization: Cannot legally work in US
    - sponsorship_unavailable: Needs visa sponsorship (company doesn't sponsor)
    - location_ineligible: In a location we cannot hire from
    """
    zenray.metric("stage", 3)
    zenray.metric("stage_name", "basic_eligibility")
    
    kept = []
    
    for applicant in applicants:
        # Age check
        if applicant["age"] < 18:
            zenray.drop(applicant, "under_minimum_age")
            continue
        
        # Work authorization
        if not applicant["us_authorized"] and not applicant["willing_to_relocate"]:
            zenray.drop(applicant, "no_work_authorization")
            continue
        
        # Sponsorship (company doesn't sponsor in this scenario)
        if applicant["needs_sponsorship"]:
            zenray.drop(applicant, "sponsorship_unavailable")
            continue
        
        # Location eligibility (some locations have legal restrictions)
        if "International" in applicant["location"] and random.random() > 0.3:
            zenray.drop(applicant, "location_ineligible")
            continue
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 4: Skills Matching
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def match_skills(applicants: list[dict]) -> list[dict]:
    """
    Stage 4: Match required and preferred skills.
    
    DROP REASONS:
    - missing_python: Required skill missing
    - missing_sql: Required skill missing
    - missing_git: Required skill missing
    - insufficient_cloud_skills: No AWS/Docker/Kubernetes
    - too_few_preferred_skills: Has required but < 3 preferred
    """
    zenray.metric("stage", 4)
    zenray.metric("stage_name", "skills_matching")
    zenray.metric("required_skills", SKILLS["required"])
    
    kept = []
    
    for applicant in applicants:
        skills = set(applicant["skills"])
        
        # Check each required skill
        if "Python" not in skills:
            zenray.drop(applicant, "missing_python")
            continue
        
        if "SQL" not in skills:
            zenray.drop(applicant, "missing_sql")
            continue
        
        if "Git" not in skills:
            zenray.drop(applicant, "missing_git")
            continue
        
        # Cloud skills check (need at least one)
        cloud_skills = skills & set(SKILLS["highly_preferred"])
        if len(cloud_skills) == 0:
            zenray.drop(applicant, "no_cloud_experience")
            continue
        
        # Preferred skills count
        preferred_count = len(skills & set(SKILLS["preferred"]))
        bonus_count = len(skills & set(SKILLS["bonus"]))
        
        if preferred_count < 2:
            zenray.drop(applicant, "insufficient_preferred_skills")
            continue
        
        # Compute skills score
        applicant["skills_score"] = min(1.0, 
            0.4 +  # Base for having required
            len(cloud_skills) * 0.1 +
            preferred_count * 0.08 +
            bonus_count * 0.05
        )
        
        kept.append(applicant)
    
    zenray.metric("avg_skills_score", sum(a["skills_score"] for a in kept) / len(kept) if kept else 0)
    return kept


# -----------------------------------------------------------------------------
# STAGE 5: Experience Evaluation
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def evaluate_experience(applicants: list[dict]) -> list[dict]:
    """
    Stage 5: Evaluate work experience.
    
    DROP REASONS:
    - insufficient_experience: Less than 4 years
    - no_relevant_companies: No experience at known tech companies
    - job_hopper: 3+ jobs under 1 year each
    - stagnant_career: Same title/level for 5+ years
    - overqualified: Principal/Staff applying for Senior role
    """
    zenray.metric("stage", 5)
    zenray.metric("stage_name", "experience_evaluation")
    zenray.metric("min_years", 4)
    
    kept = []
    
    for applicant in applicants:
        years = applicant["years_experience"]
        history = applicant["work_history"]
        
        # Minimum experience
        if years < 4:
            zenray.drop(applicant, "insufficient_experience")
            continue
        
        # Relevant experience (at least one decent company)
        has_relevant = any(job["prestige"] >= 55 for job in history)
        if not has_relevant:
            zenray.drop(applicant, "no_relevant_experience")
            continue
        
        # Job hopper detection
        short_stints = sum(1 for job in history if job["duration_years"] < 1)
        if short_stints >= 3:
            zenray.drop(applicant, "job_hopper_pattern")
            continue
        
        # Career progression check (not stuck at same level)
        if years > 8:
            titles = [job["title"] for job in history]
            if all("Junior" in t or "Mid-level" in t for t in titles):
                zenray.drop(applicant, "stagnant_career")
                continue
        
        # Overqualified check
        if applicant["current_title"] and ("Principal" in applicant["current_title"] or "Director" in applicant["current_title"]):
            zenray.drop(applicant, "overqualified_for_role")
            continue
        
        # Compute experience score
        avg_prestige = sum(job["prestige"] for job in history) / len(history) if history else 0
        applicant["experience_score"] = min(1.0,
            (min(years, 15) / 15) * 0.5 +
            (avg_prestige / 100) * 0.5
        )
        zenray.score(applicant, applicant["experience_score"])
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 6: Education Verification
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def verify_education(applicants: list[dict]) -> list[dict]:
    """
    Stage 6: Verify education credentials.
    
    DROP REASONS:
    - no_cs_degree: No CS/related degree (for this role)
    - low_gpa: GPA below 2.5
    - unaccredited_institution: Diploma mill or unverified
    - degree_mismatch: Claimed degree doesn't match verification
    """
    zenray.metric("stage", 6)
    zenray.metric("stage_name", "education_verification")
    
    kept = []
    
    for applicant in applicants:
        degree = applicant["degree"]
        gpa = applicant["gpa"]
        prestige = applicant["university_prestige"]
        
        # Degree relevance (flexible for senior roles)
        non_cs_degrees = ["No Degree"]
        if degree in non_cs_degrees and applicant["years_experience"] < 8:
            zenray.drop(applicant, "no_relevant_degree")
            continue
        
        # GPA check (only for recent grads)
        years_since_grad = 2024 - applicant["graduation_year"]
        if years_since_grad < 5 and gpa < 2.5:
            zenray.drop(applicant, "low_gpa")
            continue
        
        # Institution check
        if prestige < 40:
            zenray.drop(applicant, "unaccredited_institution")
            continue
        
        # Verification failure (simulated)
        if random.random() < 0.02:
            zenray.drop(applicant, "degree_verification_failed")
            continue
        
        # Compute education score
        gpa_factor = (gpa - 2.0) / 2.0  # 2.0 -> 0, 4.0 -> 1
        applicant["education_score"] = min(1.0,
            (prestige / 100) * 0.6 +
            gpa_factor * 0.4
        )
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 7: Background Screening
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def screen_background(applicants: list[dict]) -> list[dict]:
    """
    Stage 7: Background and reference checks.
    
    DROP REASONS:
    - criminal_record: Failed criminal background check
    - reference_failed: Negative reference from previous employer
    - unexplained_gap: Large employment gap without explanation
    - employment_fraud: Misrepresented employment history
    """
    zenray.metric("stage", 7)
    zenray.metric("stage_name", "background_screening")
    
    kept = []
    
    for applicant in applicants:
        # Criminal check
        if applicant["criminal_record"]:
            zenray.drop(applicant, "criminal_record")
            continue
        
        # Reference check
        if applicant["reference_issue"]:
            zenray.drop(applicant, "negative_reference")
            continue
        
        # Employment gap check
        if applicant["has_employment_gap"]:
            if applicant["gap_months"] > 12 and applicant["gap_reason"] in ["Personal", None]:
                zenray.drop(applicant, "unexplained_employment_gap")
                continue
        
        # Employment fraud detection (simulated)
        if random.random() < 0.01:
            zenray.drop(applicant, "employment_fraud_detected")
            continue
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 8: Technical Assessment
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def evaluate_technical(applicants: list[dict]) -> list[dict]:
    """
    Stage 8: Evaluate technical assessment scores.
    
    DROP REASONS:
    - assessment_incomplete: Did not complete the assessment
    - coding_score_low: Coding test score < 50
    - system_design_low: System design score < 40
    - overall_technical_weak: Combined score below threshold
    """
    zenray.metric("stage", 8)
    zenray.metric("stage_name", "technical_assessment")
    zenray.metric("coding_threshold", 50)
    zenray.metric("system_design_threshold", 40)
    
    kept = []
    
    for applicant in applicants:
        # Incomplete assessment
        if not applicant["took_assessment"]:
            zenray.drop(applicant, "assessment_incomplete")
            continue
        
        coding = applicant["coding_score"] or 0
        sysdesign = applicant["system_design_score"] or 0
        
        # Coding threshold
        if coding < 50:
            zenray.drop(applicant, "coding_score_low")
            continue
        
        # System design threshold
        if sysdesign < 40:
            zenray.drop(applicant, "system_design_low")
            continue
        
        # Combined score
        combined = (coding * 0.6 + sysdesign * 0.4)
        if combined < 55:
            zenray.drop(applicant, "combined_technical_weak")
            continue
        
        applicant["technical_score"] = combined / 100
        zenray.score(applicant, applicant["technical_score"])
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 9: Culture Fit
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def assess_culture(applicants: list[dict]) -> list[dict]:
    """
    Stage 9: Assess culture and values alignment.
    
    DROP REASONS:
    - values_misalignment: Core values don't match company culture
    - poor_communication: Communication skills below threshold
    - collaboration_mismatch: Strong preference against team's style
    """
    zenray.metric("stage", 9)
    zenray.metric("stage_name", "culture_fit")
    
    kept = []
    
    for applicant in applicants:
        # Values alignment
        if applicant["values_alignment"] < 0.4:
            zenray.drop(applicant, "values_misalignment")
            continue
        
        # Communication skills
        if applicant["communication_score"] < 50:
            zenray.drop(applicant, "poor_communication_skills")
            continue
        
        # Collaboration style (team prefers hybrid/team-oriented)
        if applicant["collaboration_style"] == "Independent" and random.random() > 0.7:
            zenray.drop(applicant, "collaboration_style_mismatch")
            continue
        
        # Compute culture score
        referral_boost = 0.15 if applicant["is_referral"] else 0
        applicant["culture_score"] = min(1.0,
            applicant["values_alignment"] * 0.4 +
            (applicant["communication_score"] / 100) * 0.4 +
            referral_boost +
            0.1
        )
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 10: Compensation Check
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def check_compensation(applicants: list[dict]) -> list[dict]:
    """
    Stage 10: Check salary and equity expectations.
    
    DROP REASONS:
    - salary_above_budget: Expectations exceed $220k max
    - equity_unrealistic: Demanding VP-level equity for IC role
    - total_comp_mismatch: Overall expectations way off
    """
    zenray.metric("stage", 10)
    zenray.metric("stage_name", "compensation_check")
    zenray.metric("max_salary", 220000)
    
    kept = []
    
    for applicant in applicants:
        salary = applicant["salary_expectation"]
        equity = applicant["equity_expectation"]
        
        # Salary cap
        if salary > 220000:
            zenray.drop(applicant, "salary_above_budget")
            continue
        
        # Unrealistic equity
        if equity == "Very High" and applicant["years_experience"] < 10:
            zenray.drop(applicant, "equity_expectations_unrealistic")
            continue
        
        # Too far below (might indicate quality issues or flight risk)
        if salary < 80000 and applicant["years_experience"] > 5:
            zenray.drop(applicant, "salary_suspiciously_low")
            continue
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 11: Availability Check
# -----------------------------------------------------------------------------

@zenray.step("FILTER")
def check_availability(applicants: list[dict]) -> list[dict]:
    """
    Stage 11: Check availability and start date.
    
    DROP REASONS:
    - notice_too_long: Notice period > 90 days
    - start_date_too_late: Cannot start within 120 days
    - not_available_fulltime: Only available for contract
    """
    zenray.metric("stage", 11)
    zenray.metric("stage_name", "availability_check")
    zenray.metric("max_notice_days", 90)
    
    kept = []
    
    for applicant in applicants:
        notice = applicant["notice_period_days"]
        start = datetime.fromisoformat(applicant["earliest_start"])
        days_until_start = (start - datetime.now()).days
        
        # Notice period check
        if notice > 90:
            zenray.drop(applicant, "notice_period_too_long")
            continue
        
        # Start date check
        if days_until_start > 120:
            zenray.drop(applicant, "start_date_too_late")
            continue
        
        # Full-time availability (not just contract)
        if applicant["open_to_contract"] and random.random() > 0.8:
            # Some contract-only folks filtered
            if not applicant["willing_to_relocate"]:
                zenray.drop(applicant, "contract_only_preference")
                continue
        
        kept.append(applicant)
    
    return kept


# -----------------------------------------------------------------------------
# STAGE 12: Final Selection
# -----------------------------------------------------------------------------

@zenray.step("SELECT")
def select_interviews(applicants: list[dict], max_slots: int) -> list[dict]:
    """
    Stage 12: Final ranking and interview slot selection.
    
    DROP REASONS:
    - below_score_threshold: Final score < 0.55
    - interview_slots_full: Top N already selected
    - diversity_limit: Too many from same company (max 3)
    - source_diversity: Too many from same referral source
    """
    zenray.metric("stage", 12)
    zenray.metric("stage_name", "final_selection")
    zenray.metric("max_slots", max_slots)
    zenray.metric("score_threshold", 0.55)
    
    # Compute final scores
    for applicant in applicants:
        final = (
            applicant["skills_score"] * 0.25 +
            applicant["experience_score"] * 0.25 +
            applicant["education_score"] * 0.10 +
            applicant["technical_score"] * 0.25 +
            applicant["culture_score"] * 0.15
        )
        applicant["final_score"] = round(final, 4)
        zenray.score(applicant, final)
    
    # Sort by final score
    ranked = sorted(applicants, key=lambda x: x["final_score"], reverse=True)
    
    selected = []
    company_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    
    for applicant in ranked:
        # Score threshold
        if applicant["final_score"] < 0.55:
            zenray.drop(applicant, "below_score_threshold")
            continue
        
        # Slots full
        if len(selected) >= max_slots:
            zenray.drop(applicant, "interview_slots_full")
            continue
        
        # Company diversity
        company = applicant["current_company"]
        if company and company_counts.get(company, 0) >= 3:
            zenray.drop(applicant, "company_diversity_limit")
            continue
        
        # Source diversity
        source = applicant["source"]
        if source_counts.get(source, 0) >= 8:
            zenray.drop(applicant, "source_diversity_limit")
            continue
        
        selected.append(applicant)
        if company:
            company_counts[company] = company_counts.get(company, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1
    
    zenray.metric("selected_count", len(selected))
    zenray.metric("unique_companies", len(company_counts))
    zenray.metric("top_score", selected[0]["final_score"] if selected else 0)
    zenray.metric("cutoff_score", selected[-1]["final_score"] if selected else 0)
    
    return selected


# =============================================================================
# RUN THE DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("   ENTERPRISE JOB SCREENING PIPELINE - X-Ray Debugging Demo")
    print("=" * 80)
    
    print(f"\n📋 Processing {APPLICANT_COUNT} applicants through 12 screening stages...")
    print("-" * 60)
    
    # Run the pipeline
    selected = screen_applicants("JOB-2024-SR-ENG-001", "Senior Software Engineer", max_interviews=30)
    
    print(f"\n✅ Pipeline complete!")
    print(f"   Total applicants: {APPLICANT_COUNT}")
    print(f"   Selected for interview: {len(selected)}")
    print(f"   Conversion rate: {len(selected)/APPLICANT_COUNT*100:.2f}%")
    
    print("\n" + "-" * 60)
    print("🏆 TOP 10 CANDIDATES FOR INTERVIEW:")
    print("-" * 60)
    for i, c in enumerate(selected[:10], 1):
        print(f"{i:2}. {c['name']:<25} Score: {c['final_score']:.3f}")
        print(f"    {c['current_title'] or 'N/A':<30} @ {c['current_company'] or 'N/A'}")
        print(f"    {c['years_experience']:.0f} yrs exp | {c['university'][:30]}")
        print()
    
    # Find examples for demo
    print("=" * 80)
    print("🔍 DEBUGGING DEMO - Try these searches in X-Ray:")
    print("=" * 80)
    
    # Find some interesting cases
    all_candidates = {a["id"]: a for a in APPLICANTS}
    rejected = [a for a in APPLICANTS if a not in selected]
    
    print("\n📊 1. DEPTH ANALYSIS:")
    print("   → Open http://localhost:3000 and click on this run")
    print("   → View the 12-step funnel to see where candidates drop off")
    print("   → Click on any step to see the REASON HISTOGRAM")
    print("   → Example: Click 'match_skills' to see skill gap analysis")
    
    print("\n🔎 2. CANDIDATE SEARCH (Trace):")
    print("   → Use the search box to trace any candidate's journey")
    print("\n   SELECTED CANDIDATES (passed all 12 stages):")
    for c in selected[:3]:
        print(f"      • {c['name']} ({c['id']})")
    
    print("\n   REJECTED CANDIDATES (try to find WHY):")
    # Find candidates rejected at different stages
    rejected_samples = random.sample(rejected, min(5, len(rejected)))
    for c in rejected_samples:
        print(f"      • {c['name']} ({c['id']})")
    
    print("\n" + "=" * 80)
    print("🌐 Open http://localhost:3000 to explore the full trace!")
    print("=" * 80)
