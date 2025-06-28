import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
    
    # Database
    DATABASE_PATH = 'synapse_cache.db'
    
    # Rate Limiting
    SEARCH_RATE_LIMIT = 10  # searches per minute
    API_RATE_LIMIT = 60     # API calls per minute
    
    # Search Settings
    MAX_SEARCH_RESULTS = 50
    SEARCH_TIMEOUT = 30
    
    # Scoring Weights
    EDUCATION_WEIGHT = 0.20
    CAREER_TRAJECTORY_WEIGHT = 0.20
    COMPANY_RELEVANCE_WEIGHT = 0.15
    EXPERIENCE_MATCH_WEIGHT = 0.25
    LOCATION_MATCH_WEIGHT = 0.10
    TENURE_WEIGHT = 0.10
    
    # Outreach Settings
    DEFAULT_TOP_CANDIDATES = 10
    MESSAGE_TEMPLATE = """
    Hi {name},
    
    I came across your profile and was impressed by your {headline}. Your experience in {key_detail} particularly caught my attention.
    
    I'm reaching out because we have an exciting opportunity that aligns well with your background. Would you be interested in a brief conversation about potential collaboration?
    
    Best regards,
    Synapse Team
    """ 