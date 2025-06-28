import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from config import Config

class Database:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Search cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_description TEXT NOT NULL,
                    search_query TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_description, search_query)
                )
            ''')
            
            # Candidates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    linkedin_url TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    headline TEXT,
                    profile_data TEXT,
                    score REAL,
                    score_breakdown TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Outreach messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outreach_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER,
                    job_description TEXT,
                    message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (id)
                )
            ''')
            
            conn.commit()
    
    def cache_search_results(self, job_description: str, search_query: str, results: List[Dict]) -> None:
        """Cache search results to avoid re-fetching."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO search_cache (job_description, search_query, results)
                VALUES (?, ?, ?)
            ''', (job_description, search_query, json.dumps(results)))
            conn.commit()
    
    def get_cached_search_results(self, job_description: str, search_query: str) -> Optional[List[Dict]]:
        """Retrieve cached search results if they exist and are recent."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT results FROM search_cache 
                WHERE job_description = ? AND search_query = ?
                AND created_at > datetime('now', '-1 day')
            ''', (job_description, search_query))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
    
    def save_candidate(self, linkedin_url: str, name: str, headline: str, 
                      profile_data: Dict = None, score: float = None, 
                      score_breakdown: Dict = None) -> int:
        """Save or update candidate information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if candidate exists
            cursor.execute('SELECT id FROM candidates WHERE linkedin_url = ?', (linkedin_url,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing candidate
                cursor.execute('''
                    UPDATE candidates 
                    SET name = ?, headline = ?, profile_data = ?, score = ?, 
                        score_breakdown = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE linkedin_url = ?
                ''', (name, headline, json.dumps(profile_data) if profile_data else None,
                     score, json.dumps(score_breakdown) if score_breakdown else None, linkedin_url))
                return existing[0]
            else:
                # Insert new candidate
                cursor.execute('''
                    INSERT INTO candidates (linkedin_url, name, headline, profile_data, score, score_breakdown)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (linkedin_url, name, headline, 
                     json.dumps(profile_data) if profile_data else None,
                     score, json.dumps(score_breakdown) if score_breakdown else None))
                return cursor.lastrowid
    
    def get_candidate(self, linkedin_url: str) -> Optional[Dict]:
        """Retrieve candidate information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, headline, profile_data, score, score_breakdown
                FROM candidates WHERE linkedin_url = ?
            ''', (linkedin_url,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'headline': result[2],
                    'profile_data': json.loads(result[3]) if result[3] else None,
                    'score': result[4],
                    'score_breakdown': json.loads(result[5]) if result[5] else None
                }
            return None
    
    def save_outreach_message(self, candidate_id: int, job_description: str, message: str) -> int:
        """Save outreach message."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO outreach_messages (candidate_id, job_description, message)
                VALUES (?, ?, ?)
            ''', (candidate_id, job_description, message))
            return cursor.lastrowid
    
    def get_top_candidates(self, limit: int = 10) -> List[Dict]:
        """Get top candidates by score."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, headline, linkedin_url, score, score_breakdown
                FROM candidates 
                WHERE score IS NOT NULL
                ORDER BY score DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            return [{
                'id': row[0],
                'name': row[1],
                'headline': row[2],
                'linkedin_url': row[3],
                'score': row[4],
                'score_breakdown': json.loads(row[5]) if row[5] else None
            } for row in results] 