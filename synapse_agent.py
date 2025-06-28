import asyncio
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from database import Database
from gemini_client import GroqClient
from linkedin_discovery import LinkedInDiscovery


class SynapseAgent:
    """
    Synapse's autonomous LinkedIn Sourcing Agent.
    
    Handles discovery, scoring, and outreach for job candidates.
    """
    
    def __init__(self):
        self.db = Database()
        self.groq = GroqClient()
        self.discovery = LinkedInDiscovery()
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def process_job(self, job_description: str, top_candidates: int = Config.DEFAULT_TOP_CANDIDATES) -> Dict:
        """
        Main method to process a job description and return top candidates with outreach messages.
        
        Args:
            job_description: The job description to source candidates for
            top_candidates: Number of top candidates to return with outreach messages
            
        Returns:
            Dict containing discovered candidates, scores, and outreach messages
        """
        print(f"🚀 Starting Synapse Agent for job: {job_description[:100]}...")
        
        # Step 1: Discover candidates
        print("🔍 Discovering LinkedIn profiles...")
        candidates = self._discover_candidates(job_description)
        
        if not candidates:
            return {
                'job_description': job_description,
                'candidates': [],
                'top_candidates': [],
                'outreach_messages': [],
                'error': 'No candidates found'
            }
        
        print(f"✅ Found {len(candidates)} candidates")
        
        # Step 2: Score candidates
        print("📊 Scoring candidates...")
        scored_candidates = self._score_candidates(job_description, candidates)
        
        # Step 3: Generate outreach messages for top candidates
        print(f"💬 Generating outreach messages for top candidates...")
        top_candidates_with_messages = self._generate_outreach_messages(
            job_description, scored_candidates[:top_candidates]
        )
        
        return {
            'job_description': job_description,
            'candidates': scored_candidates,
            'top_candidates': top_candidates_with_messages,
            'outreach_messages': [c['outreach_message'] for c in top_candidates_with_messages],
            'summary': {
                'total_candidates': len(scored_candidates),
                'top_candidates_count': len(top_candidates_with_messages),
                'average_score': sum(c['score'] for c in scored_candidates) / len(scored_candidates) if scored_candidates else 0
            }
        }
    
    def _discover_candidates(self, job_description: str, limit: int = Config.DEFAULT_TOP_CANDIDATES) -> List[Dict]:
        """Discover LinkedIn profiles relevant to the job description using RapidAPI only."""
        # Check cache first
        search_query = f'site:linkedin.com/in/ {job_description[:100]}'
        cached_results = self.db.get_cached_search_results(job_description, search_query)
        if cached_results:
            print("📋 Using cached search results")
            return cached_results[:limit]

        # Use RapidAPI only
        profiles = self.discovery.search_linkedin_profiles(job_description, limit=limit)

        # Cache the results
        if profiles:
            self.db.cache_search_results(job_description, search_query, profiles)

        return profiles[:limit]
    
    def _score_candidates(self, job_description: str, candidates: List[Dict]) -> List[Dict]:
        """Score candidates using the 0-10 rubric with weighted criteria."""
        scored_candidates = []
        
        # Process candidates in parallel for better performance
        futures = []
        for candidate in candidates:
            future = self.executor.submit(self._score_single_candidate, job_description, candidate)
            futures.append((candidate, future))
        
        for candidate, future in futures:
            try:
                score_result = future.result(timeout=30)
                scored_candidate = {
                    **candidate,
                    'score': score_result['score'],
                    'score_breakdown': score_result['breakdown']
                }
                scored_candidates.append(scored_candidate)
                
                # Save to database
                self.db.save_candidate(
                    linkedin_url=candidate['linkedin_url'],
                    name=candidate['name'],
                    headline=candidate['headline'],
                    score=score_result['score'],
                    score_breakdown=score_result['breakdown']
                )
                
            except Exception as e:
                print(f"Error scoring candidate {candidate.get('name', 'Unknown')}: {e}")
                # Add candidate with default score
                scored_candidates.append({
                    **candidate,
                    'score': 5.0,
                    'score_breakdown': {
                        'education': 5.0,
                        'trajectory': 5.0,
                        'company': 5.0,
                        'skills': 5.0,
                        'location': 5.0,
                        'tenure': 5.0
                    }
                })
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        return scored_candidates
    
    def _score_single_candidate(self, job_description: str, candidate: Dict) -> Dict:
        """Score a single candidate using Groq AI."""
        # Get detailed profile data if available
        profile_data = self.db.get_candidate(candidate['linkedin_url'])
        
        if not profile_data or not profile_data.get('profile_data'):
            # Try to get fresh profile data
            try:
                fresh_profile_data = self.discovery.get_profile_details(candidate['linkedin_url'])
                if fresh_profile_data:
                    self.db.save_candidate(
                        linkedin_url=candidate['linkedin_url'],
                        name=candidate['name'],
                        headline=candidate['headline'],
                        profile_data=fresh_profile_data
                    )
                    profile_data = fresh_profile_data
            except Exception as e:
                print(f"Could not get profile data for {candidate['linkedin_url']}: {e}")
        
        # Prepare candidate data for scoring
        candidate_data = {
            'name': candidate['name'],
            'headline': candidate['headline'],
            'profile_data': profile_data.get('profile_data') if profile_data else None
        }
        
        # Score using Groq
        return self.groq.score_candidate(job_description, candidate_data)
    
    def _generate_outreach_messages(self, job_description: str, top_candidates: List[Dict]) -> List[Dict]:
        """Generate personalized outreach messages for top candidates."""
        candidates_with_messages = []
        
        for candidate in top_candidates:
            try:
                # Generate personalized message
                message = self.groq.generate_outreach_message(candidate, job_description)
                
                # Save outreach message to database
                candidate_id = self.db.save_candidate(
                    linkedin_url=candidate['linkedin_url'],
                    name=candidate['name'],
                    headline=candidate['headline'],
                    score=candidate['score'],
                    score_breakdown=candidate['score_breakdown']
                )
                
                self.db.save_outreach_message(candidate_id, job_description, message)
                
                candidates_with_messages.append({
                    **candidate,
                    'outreach_message': message
                })
                
            except Exception as e:
                print(f"Error generating message for {candidate.get('name', 'Unknown')}: {e}")
                # Add candidate with default message
                candidates_with_messages.append({
                    **candidate,
                    'outreach_message': f"Hi {candidate.get('name', 'there')}, I came across your profile and would love to connect regarding a potential opportunity."
                })
        
        return candidates_with_messages
    
    def process_multiple_jobs(self, job_descriptions: List[str], top_candidates_per_job: int = 10) -> List[Dict]:
        """
        Process multiple job descriptions in parallel.
        
        Args:
            job_descriptions: List of job descriptions to process
            top_candidates_per_job: Number of top candidates per job
            
        Returns:
            List of results for each job
        """
        print(f"🚀 Processing {len(job_descriptions)} jobs in parallel...")
        
        # Process jobs in parallel
        futures = []
        for job_desc in job_descriptions:
            future = self.executor.submit(self.process_job, job_desc, top_candidates_per_job)
            futures.append((job_desc, future))
        
        results = []
        for job_desc, future in futures:
            try:
                result = future.result(timeout=300)  # 5 minutes timeout per job
                results.append(result)
                print(f"✅ Completed job: {job_desc[:50]}...")
            except Exception as e:
                print(f"❌ Error processing job {job_desc[:50]}...: {e}")
                results.append({
                    'job_description': job_desc,
                    'candidates': [],
                    'top_candidates': [],
                    'outreach_messages': [],
                    'error': str(e)
                })
        
        return results
    
    def get_top_candidates_from_database(self, limit: int = 10) -> List[Dict]:
        """Get top candidates from the database."""
        return self.db.get_top_candidates(limit)
    
    def get_candidate_details(self, linkedin_url: str) -> Optional[Dict]:
        """Get detailed information about a specific candidate."""
        return self.db.get_candidate(linkedin_url)
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True) 

    def search_linkedin_profiles_via_serpapi(self, job_description: str, limit: int = 10) -> List[Dict]:
        """Search Google for LinkedIn profiles using SerpAPI."""
        params = {
            "engine": "google",
            "q": f'site:linkedin.com/in {job_description}',
            "api_key": "<YOUR_SERPAPI_KEY>",
            "num": limit
        }
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            profiles = []
            for result in results.get("organic_results", []):
                link = result.get("link", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if "linkedin.com/in/" in link:
                    profiles.append({
                        "name": title.split(" - ")[0],
                        "linkedin_url": link,
                        "headline": snippet
                    })
                if len(profiles) >= limit:
                    break
            return profiles
        except Exception as e:
            print(f"Error using SerpAPI: {e}")
            return [] 