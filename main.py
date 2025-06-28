#!/usr/bin/env python3


import argparse
import json
import sys
from typing import List
from synapse_agent import SynapseAgent
from config import Config

def print_banner():
    print(r"""
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│                🧠  SYNAPSE AGENT  🧠                          │
│                                                               │
│          Autonomous LinkedIn Sourcing & Outreach              │
│                                                               │
│                                                               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
""")

def print_candidate(candidate: dict, index: int = None):
    """Print candidate information in a formatted way."""
    prefix = f"{index}. " if index is not None else ""
    print(f"\n{prefix}👤 {candidate['name']}")
    print(f"   📋 {candidate['headline']}")
    print(f"   🔗 {candidate['linkedin_url']}")
    print(f"   ⭐ Score: {candidate['score']:.1f}/10")
    
    if candidate.get('score_breakdown'):
        breakdown = candidate['score_breakdown']
        print(f"   📊 Breakdown:")
        print(f"      • Education: {breakdown.get('education', 0):.1f}")
        print(f"      • Career Trajectory: {breakdown.get('trajectory', 0):.1f}")
        print(f"      • Company Relevance: {breakdown.get('company', 0):.1f}")
        print(f"      • Experience Match: {breakdown.get('skills', 0):.1f}")
        print(f"      • Location Match: {breakdown.get('location', 0):.1f}")
        print(f"      • Tenure: {breakdown.get('tenure', 0):.1f}")
    
    if candidate.get('outreach_message'):
        print(f"   💬 Outreach Message:")
        print(f"      {candidate['outreach_message']}")

def process_single_job(job_description: str, top_candidates: int = 10):
    """Process a single job description."""
    print(f"\n🎯 Processing job: {job_description}")
    print("=" * 60)
    
    agent = SynapseAgent()
    result = agent.process_job(job_description, top_candidates)
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n✅ Results Summary:")
    print(f"   • Total candidates found: {result['summary']['total_candidates']}")
    print(f"   • Top candidates: {result['summary']['top_candidates_count']}")
    print(f"   • Average score: {result['summary']['average_score']:.1f}/10")
    
    print(f"\n🏆 Top {len(result['top_candidates'])} Candidates:")
    for i, candidate in enumerate(result['top_candidates'], 1):
        print_candidate(candidate, i)
    
    # Dynamic outreach message log
    
    
    return result

def process_multiple_jobs(job_descriptions: List[str], top_candidates_per_job: int = 10):
    """Process multiple job descriptions."""
    print(f"\n🚀 Processing {len(job_descriptions)} jobs in parallel...")
    print("=" * 60)
    
    agent = SynapseAgent()
    results = agent.process_multiple_jobs(job_descriptions, top_candidates_per_job)
    
    for i, result in enumerate(results, 1):
        print(f"\n📋 Job {i}: {result['job_description'][:50]}...")
        
        if result.get('error'):
            print(f"   ❌ Error: {result['error']}")
            continue
        
        print(f"   ✅ Found {result['summary']['total_candidates']} candidates")
        print(f"   🏆 Top {len(result['top_candidates'])} candidates:")
        
        for j, candidate in enumerate(result['top_candidates'][:3], 1):  # Show top 3
            print(f"      {j}. {candidate['name']} - Score: {candidate['score']:.1f}/10")
    
    return results

def interactive_mode():
    """Run the agent in interactive mode."""
    print("\n🎮 Interactive Mode")
    print("Type 'quit' to exit, 'help' for commands")
    
    agent = SynapseAgent()
    
    while True:
        try:
            command = input("\n🤖 Synapse> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                print("👋 Goodbye!")
                break
            elif command == 'help':
                print("""
Available commands:
- process <job_description> - Process a single job
- batch <job1> | <job2> | <job3> - Process multiple jobs
- top <number> - Show top candidates from database
- candidate <linkedin_url> - Get candidate details
- help - Show this help
- quit - Exit
                """)
            elif command.startswith('process '):
                job_desc = command[8:]  # Remove 'process ' prefix
                if job_desc:
                    process_single_job(job_desc)
                else:
                    print("❌ Please provide a job description")
            elif command.startswith('batch '):
                jobs_text = command[6:]  # Remove 'batch ' prefix
                if '|' in jobs_text:
                    job_descriptions = [job.strip() for job in jobs_text.split('|')]
                    process_multiple_jobs(job_descriptions)
                else:
                    print("❌ Please separate jobs with '|'")
            elif command.startswith('top '):
                try:
                    limit = int(command[4:])
                    candidates = agent.get_top_candidates_from_database(limit)
                    print(f"\n🏆 Top {len(candidates)} Candidates from Database:")
                    for i, candidate in enumerate(candidates, 1):
                        print_candidate(candidate, i)
                except ValueError:
                    print("❌ Please provide a valid number")
            elif command.startswith('candidate '):
                linkedin_url = command[10:]  # Remove 'candidate ' prefix
                candidate = agent.get_candidate_details(linkedin_url)
                if candidate:
                    print_candidate(candidate)
                else:
                    print("❌ Candidate not found in database")
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def load_jobs_from_file(filename: str) -> List[str]:
    """Load job descriptions from a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            jobs = [line.strip() for line in f if line.strip()]
        return jobs
    except FileNotFoundError:
        print(f"❌ File '{filename}' not found")
        return []
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Synapse - Autonomous LinkedIn Sourcing Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --job "Software Engineer with Python experience"
  python main.py --jobs-file jobs.txt
  python main.py --interactive
        """
    )
    
    parser.add_argument(
        '--job', 
        type=str, 
        help='Single job description to process'
    )
    
    parser.add_argument(
        '--jobs-file', 
        type=str, 
        help='File containing job descriptions (one per line)'
    )
    
    parser.add_argument(
        '--interactive', 
        action='store_true', 
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--top-candidates', 
        type=int, 
        default=10, 
        help='Number of top candidates to return (default: 10)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        help='Output file for results (JSON format)'
    )
    
    args = parser.parse_args()
    
    # Check if GROQ_API_KEY is set
    if not Config.GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY environment variable is required")
        print("Please set it in your .env file or environment variables")
        sys.exit(1)
    
    print_banner()
    
    try:
        if args.interactive:
            interactive_mode()
        elif args.job:
            result = process_single_job(args.job, args.top_candidates)
            if args.output and result:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\n💾 Results saved to {args.output}")
        elif args.jobs_file:
            jobs = load_jobs_from_file(args.jobs_file)
            if jobs:
                results = process_multiple_jobs(jobs, args.top_candidates)
                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"\n💾 Results saved to {args.output}")
            else:
                print("❌ No jobs loaded from file")
        else:
            # Default example
            print("🔍 No arguments provided. Running example job...")
            example_job = "Senior Software Engineer with Python and React experience, 5+ years in fintech"
            process_single_job(example_job, args.top_candidates)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 