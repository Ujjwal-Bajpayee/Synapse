# 🧠 Synapse - Autonomous LinkedIn Sourcing Agent

Synapse is an intelligent, autonomous LinkedIn sourcing agent that discovers, scores, and generates personalized outreach messages for job candidates using Groq AI.

## ✨ Features

- **Discovery**: Google search for LinkedIn profiles
- **Scoring**: 0-10 rubric with weighted criteria
- **Outreach**: Personalized LinkedIn messages
- **Scale**: Parallel processing with rate limiting
- **Cache**: SQLite database for results

## 🛠️ Installation

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `env_example.txt` to `.env`
3. Add your Groq API key to `.env`

## 🚀 Usage

```bash
# Single job
python main.py --job "Software Engineer with Python experience"

# Multiple jobs
python main.py --jobs-file jobs.txt

# Interactive mode
python main.py --interactive
```

## 📊 Scoring Weights

- Education (20%)
- Career Trajectory (20%) 
- Company Relevance (15%)
- Experience Match (25%)
- Location Match (10%)
- Tenure (10%)

## ⚙️ Configuration

Set environment variables in `.env`:
- `GROQ_API_KEY`: Required Groq API key
- `DATABASE_PATH`: SQLite database path
- `SEARCH_RATE_LIMIT`: Searches per minute
- `API_RATE_LIMIT`: API calls per minute

## 🗄️ Database Schema

The agent uses SQLite to cache:

- **Search Results**: Cached LinkedIn profile searches
- **Candidates**: Profile data, scores, and breakdowns
- **Outreach Messages**: Generated messages for tracking

## 🔧 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LinkedIn      │    │   Groq AI       │    │   SQLite        │
│   Discovery     │    │   Client        │    │   Database      │
│                 │    │                 │    │                 │
│ • Google Search │    │ • Scoring       │    │ • Cache Results │
│ • Profile Parse │    │ • Message Gen   │    │ • Store Data    │
│ • Rate Limiting │    │ • Rate Limiting │    │ • Query History │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Synapse       │
                    │   Agent         │
                    │                 │
                    │ • Orchestration │
                    │ • Parallel Proc │
                    │ • Error Handling│
                    └─────────────────┘
```

## 🚨 Important Notes

### Rate Limiting
- The agent implements rate limiting to respect API and search limits
- Default: 10 searches/minute, 60 API calls/minute
- Adjust in `config.py` if needed

### LinkedIn Access
- Uses Google search to find LinkedIn profiles
- Profile data extraction is simplified (production would need LinkedIn API)
- Respects robots.txt and implements delays

### API Costs
- Groq API charges apply
- Monitor usage in Groq AI dashboard
- Consider implementing usage tracking

## 🐛 Troubleshooting

### Common Issues

1. **"GROQ_API_KEY is required"**
   - Ensure your `.env` file exists and contains the API key
   - Verify the API key is valid in Groq AI dashboard

2. **"No candidates found"**
   - Check internet connection
   - Verify job description has relevant keywords
   - Try different search terms

3. **Rate limiting errors**
   - Wait for rate limit to reset
   - Reduce parallel processing in `config.py`

4. **Database errors**
   - Check file permissions for SQLite database
   - Delete `synapse_cache.db` to reset cache

### Debug Mode

Enable debug logging by modifying the agent initialization:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Please:
- Respect LinkedIn's Terms of Service
- Follow ethical sourcing practices
- Comply with data protection regulations
- Use responsibly and with consent

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Open an issue on GitHub
4. Contact the development team 