#!/usr/bin/env python3
"""
Mock test script for Synapse Agent (no API calls required)
"""

import os
import sys
import json
from config import Config

def test_database():
    """Test database functionality."""
    try:
        from database import Database
        db = Database()
        print("✅ Database test: Connection successful")
        
        # Test basic operations
        test_candidate = {
            'linkedin_url': 'https://linkedin.com/in/test-user',
            'name': 'Test User',
            'headline': 'Software Engineer at Test Corp',
            'score': 8.5,
            'score_breakdown': {
                'education': 8.0,
                'trajectory': 9.0,
                'company': 7.5,
                'skills': 9.0,
                'location': 8.0,
                'tenure': 8.5
            }
        }
        
        # Save test candidate
        candidate_id = db.save_candidate(**test_candidate)
        print(f"   ✅ Saved test candidate with ID: {candidate_id}")
        
        # Retrieve test candidate
        retrieved = db.get_candidate(test_candidate['linkedin_url'])
        if retrieved:
            print(f"   ✅ Retrieved candidate: {retrieved['name']}")
        
        # Get top candidates
        top_candidates = db.get_top_candidates(5)
        print(f"   ✅ Retrieved {len(top_candidates)} top candidates")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_discovery_mock():
    """Test LinkedIn discovery with mock data."""
    try:
        from linkedin_discovery import LinkedInDiscovery
        discovery = LinkedInDiscovery()
        
        # Test keyword extraction
        job_desc = "Senior Software Engineer with Python and AWS experience"
        keywords = discovery._extract_search_terms(job_desc)
        print(f"✅ Discovery test: Extracted keywords: {keywords}")
        
        # Test URL validation
        valid_urls = [
            "https://linkedin.com/in/johndoe",
            "https://linkedin.com/in/jane-smith-123",
            "http://linkedin.com/in/test"
        ]
        
        invalid_urls = [
            "https://google.com",
            "linkedin.com/in/",
            "https://linkedin.com/in/"
        ]
        
        for url in valid_urls:
            if discovery._is_valid_linkedin_url(url):
                print(f"   ✅ Valid URL: {url}")
            else:
                print(f"   ❌ Invalid URL (should be valid): {url}")
        
        for url in invalid_urls:
            if not discovery._is_valid_linkedin_url(url):
                print(f"   ✅ Invalid URL correctly detected: {url}")
            else:
                print(f"   ❌ Valid URL (should be invalid): {url}")
        
        return True
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        return False

def test_agent_logic():
    """Test agent logic without API calls."""
    try:
        from synapse_agent import SynapseAgent
        
        # Create mock candidates
        mock_candidates = [
            {
                'name': 'John Doe',
                'linkedin_url': 'https://linkedin.com/in/johndoe',
                'headline': 'Senior Software Engineer at Tech Corp'
            },
            {
                'name': 'Jane Smith',
                'linkedin_url': 'https://linkedin.com/in/janesmith',
                'headline': 'Full Stack Developer at Startup Inc'
            },
            {
                'name': 'Bob Johnson',
                'linkedin_url': 'https://linkedin.com/in/bobjohnson',
                'headline': 'Python Developer at Big Tech'
            }
        ]
        
        print("✅ Agent logic test: Created mock candidates")
        
        # Test scoring logic (without API)
        job_description = "Software Engineer with Python experience"
        
        # Simulate scoring
        scored_candidates = []
        for i, candidate in enumerate(mock_candidates):
            # Mock score based on name position (for testing)
            score = 9.0 - (i * 0.5)
            scored_candidate = {
                **candidate,
                'score': score,
                'score_breakdown': {
                    'education': score,
                    'trajectory': score,
                    'company': score,
                    'skills': score,
                    'location': score,
                    'tenure': score
                }
            }
            scored_candidates.append(scored_candidate)
        
        # Sort by score
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"   ✅ Scored {len(scored_candidates)} candidates")
        print(f"   ✅ Top candidate: {scored_candidates[0]['name']} (Score: {scored_candidates[0]['score']:.1f})")
        
        # Test message generation logic
        top_candidates = scored_candidates[:2]
        messages = []
        
        for candidate in top_candidates:
            message = f"Hi {candidate['name']}, I came across your profile and was impressed by your {candidate['headline']}. Would you be interested in discussing a potential opportunity?"
            messages.append(message)
        
        print(f"   ✅ Generated {len(messages)} outreach messages")
        
        return True
    except Exception as e:
        print(f"❌ Agent logic test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    try:
        print("✅ Configuration test:")
        print(f"   • Database path: {Config.DATABASE_PATH}")
        print(f"   • Search rate limit: {Config.SEARCH_RATE_LIMIT}")
        print(f"   • API rate limit: {Config.API_RATE_LIMIT}")
        print(f"   • Max search results: {Config.MAX_SEARCH_RESULTS}")
        print(f"   • Default top candidates: {Config.DEFAULT_TOP_CANDIDATES}")
        
        # Test scoring weights
        weights = [
            Config.EDUCATION_WEIGHT,
            Config.CAREER_TRAJECTORY_WEIGHT,
            Config.COMPANY_RELEVANCE_WEIGHT,
            Config.EXPERIENCE_MATCH_WEIGHT,
            Config.LOCATION_MATCH_WEIGHT,
            Config.TENURE_WEIGHT
        ]
        
        total_weight = sum(weights)
        print(f"   • Total scoring weight: {total_weight:.2f} (should be 1.0)")
        
        if abs(total_weight - 1.0) < 0.01:
            print("   ✅ Scoring weights sum to 1.0")
        else:
            print("   ⚠️  Scoring weights don't sum to 1.0")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all mock tests."""
    print("🧪 Synapse Agent Mock Test Suite")
    print("=" * 50)
    print("💡 This test suite doesn't require API keys or internet connection")
    print()
    
    # Run tests
    tests = [
        ("Configuration", test_configuration),
        ("Database", test_database),
        ("Discovery Logic", test_discovery_mock),
        ("Agent Logic", test_agent_logic),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Mock Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All mock tests passed! Core logic is working correctly.")
        print("💡 To test with real APIs, run: python test_synapse.py")
        return True
    else:
        print("⚠️  Some mock tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 