import groq
from typing import Dict, List, Optional
from config import Config
import time
from ratelimit import limits, sleep_and_retry

class GroqClient:
    def __init__(self, api_key: str = Config.GROQ_API_KEY):
        if not api_key:
            raise ValueError("GROQ_API_KEY is required")
        
        self.client = groq.Groq(api_key=api_key)
        self.model = "llama3-70b-8192"  # Using Llama 3.1 70B model
    
    @sleep_and_retry
    @limits(calls=Config.API_RATE_LIMIT, period=60)
    def call_groq(self, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
        """Make a rate-limited call to Groq API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content if response.choices else ""
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return ""
    
    def score_candidate(self, job_description: str, candidate_data: Dict) -> Dict:
        """Score a candidate based on the job description using the 0-10 rubric."""
        prompt = f"""
        You are an expert recruiter scoring candidates for a job position.
        
        Job Description:
        {job_description}
        
        Candidate Profile:
        Name: {candidate_data.get('name', 'N/A')}
        Headline: {candidate_data.get('headline', 'N/A')}
        Education: {(candidate_data.get('profile_data') or {}).get('education', '')}
        Experience: {(candidate_data.get('profile_data') or {}).get('experience', '')}
        Skills: {(candidate_data.get('profile_data') or {}).get('skills', '')}
        Location: {(candidate_data.get('profile_data') or {}).get('location', '')}
        Summary: {(candidate_data.get('profile_data') or {}).get('summary', '')}
        
        Please score this candidate from 0-10 based on the following criteria and weights:
        - Education (20%): Relevance of educational background
        - Career Trajectory (20%): Progression and growth in career
        - Company Relevance (15%): Experience at relevant companies
        - Experience Match (25%): Direct experience with required skills
        - Location Match (10%): Geographic fit
        - Tenure (10%): Length and stability of experience
        
        Return ONLY a JSON object with this exact format:
        {{
            "score": <overall_score_0-10>,
            "breakdown": {{
                "education": <score_0-10>,
                "trajectory": <score_0-10>,
                "company": <score_0-10>,
                "skills": <score_0-10>,
                "location": <score_0-10>,
                "tenure": <score_0-10>
            }}
        }}
        
        Be objective and provide scores based on the available information.
        """
        
        response = self.call_groq(prompt, temperature=0.3)
        
        try:
            import json
            if response:
                result = json.loads(response)
                return result
        except:
            pass
        
        # Fallback scoring if JSON parsing fails
        return {
            "score": 5.0,
            "breakdown": {
                "education": 5.0,
                "trajectory": 5.0,
                "company": 5.0,
                "skills": 5.0,
                "location": 5.0,
                "tenure": 5.0
            }
        }
    
    def generate_outreach_message(self, candidate: Dict, job_description: str) -> str:
        """Generate a personalized LinkedIn outreach message."""
        prompt = f"""
        Generate a professional LinkedIn outreach message for this candidate.
        
        Job Description:
        {job_description}
        
        Candidate:
        Name: {candidate.get('name', '')}
        Headline: {candidate.get('headline', '')}
        Score: {candidate.get('score', 0)}
        Key Details: {candidate.get('score_breakdown', {})}
        
        Requirements:
        1. Keep it professional and concise (~2 sentences)
        2. Reference their specific headline and 1-2 key details from their profile
        3. Make it personalized and relevant to the job opportunity
        4. Include a clear call-to-action
        5. Keep the tone warm but professional
        
        Return ONLY the message text, no additional formatting.
        """
        
        response = self.call_groq(prompt, temperature=0.7)
        return response if response else f"Hi {candidate.get('name', 'there')}, I came across your profile and would love to connect regarding a potential opportunity."
    
    def extract_profile_data(self, linkedin_url: str, raw_profile_html: str) -> Dict:
        """Extract structured profile data from LinkedIn profile HTML."""
        prompt = f"""
        Extract key information from this LinkedIn profile HTML.
        
        LinkedIn URL: {linkedin_url}
        Raw HTML: {raw_profile_html[:2000]}  # First 2000 chars for context
        
        Extract and return ONLY a JSON object with this structure:
        {{
            "name": "Full Name",
            "headline": "Current job title and company",
            "location": "City, State/Country",
            "education": ["Degree, University", "..."],
            "experience": [
                {{
                    "title": "Job Title",
                    "company": "Company Name",
                    "duration": "Duration",
                    "description": "Brief description"
                }}
            ],
            "skills": ["Skill 1", "Skill 2", "..."],
            "summary": "Brief professional summary"
        }}
        
        If any field cannot be extracted, use null or empty array/string.
        """
        
        response = self.call_groq(prompt, temperature=0.1)
        
        try:
            import json
            if response:
                return json.loads(response)
        except:
            pass
        
        return {
            "name": "",
            "headline": "",
            "location": "",
            "education": [],
            "experience": [],
            "skills": [],
            "summary": ""
        } 