# Multi-Agent Research Assistant

A sophisticated multi-agent AI system that conducts comprehensive academic research using coordinated AI agents. The system breaks down complex research questions into manageable sub-questions and uses specialized agents to gather, analyze, and synthesize information.

<img width="1365" height="925" alt="Capture" src="https://github.com/user-attachments/assets/df91e39f-ad35-46d1-a009-c1db3da54ceb" />

## 🚀 Features

- **Multi-Agent Architecture**: Coordinated team of specialized AI agents
- **Intelligent Research Planning**: Automatically breaks down research questions into sub-tasks
- **Web Search Integration**: Real-time information gathering using Tavily API
- **Document Analysis**: Advanced text analysis and summarization
- **Critical Evaluation**: Quality assessment and bias detection
- **Comprehensive Reporting**: Professional research reports with citations
- **Real-time Progress Tracking**: Live updates on research progress
- **RESTful API**: Easy integration with other applications

## 🏗️ Architecture

The system consists of five specialized agents:

### 1. Research Manager Agent
- **Role**: Coordinates the entire research workflow
- **Responsibilities**: 
  - Breaks down research questions into sub-questions
  - Creates task assignments for other agents
  - Synthesizes final reports
  - Monitors overall progress

### 2. Information Retrieval Agent
- **Role**: Gathers relevant information from web sources
- **Responsibilities**:
  - Extracts optimal search keywords
  - Performs web searches using Tavily API
  - Evaluates source credibility and relevance
  - Filters and ranks search results

### 3. Document Analysis Agent
- **Role**: Analyzes and extracts insights from gathered sources
- **Responsibilities**:
  - Summarizes lengthy content
  - Extracts key findings and claims
  - Identifies methodologies and evidence
  - Assigns relevance scores

### 4. Critical Evaluation Agent
- **Role**: Assesses research quality and identifies gaps
- **Responsibilities**:
  - Evaluates information quality and comprehensiveness
  - Identifies potential biases and limitations
  - Determines if additional research is needed
  - Provides consistency analysis

### 5. Report Generation Agent
- **Role**: Creates professional research reports
- **Responsibilities**:
  - Generates properly formatted citations
  - Creates structured research reports
  - Produces executive summaries
  - Formats final deliverables

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Ollama**: Local LLM integration (Mistral model)
- **Tavily API**: Web search capabilities
- **LangChain**: AI framework for building applications
- **Pydantic**: Data validation and settings management

### Frontend
- **React**: User interface framework
- **Chakra UI**: Component library
- **Axios**: HTTP client for API communication

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## 📋 Prerequisites

Before running the application, ensure you have:

1. **Python 3.10+** installed
2. **Node.js 16+** installed
3. **Docker and Docker Compose** (optional, for containerized deployment)
4. **Ollama** installed and running locally
5. **Tavily API Key** (sign up at [tavily.com](https://tavily.com))

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/multi-agent-research-assistant.git
cd multi-agent-research-assistant
```

### 2. Environment Setup
Create a `.env` file in the root directory:
```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral

# Tavily API Key for Web Search
TAVILY_API_KEY=your_tavily_api_key_here

# Application Settings
PORT=8000
DEBUG=False
```

### 3. Install Ollama and Pull Model
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull the Mistral model (in a new terminal)
ollama pull mistral
```

### 4. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Frontend Setup (Optional)
```bash
cd frontend
npm install
npm start
```

### 6. Docker Deployment (Alternative)
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📖 API Usage

### Start Research
```bash
curl -X POST "http://localhost:8000/api/research" \
  -H "Content-Type: application/json" \
  -d '{
    "research_question": "What are the health benefits of drinking water?",
    "depth": "standard",
    "format": "report"
  }'
```

### Check Research Status
```bash
curl -X GET "http://localhost:8000/api/research/{research_id}"
```

### Get Research Messages
```bash
curl -X GET "http://localhost:8000/api/research/{research_id}/messages"
```

## 🔧 Configuration

### Research Depth Options
- **Quick** (5 min): Basic research with limited sources
- **Standard** (15 min): Comprehensive research with multiple sources
- **Deep** (30+ min): Extensive research with detailed analysis

### Output Formats
- **Report**: Full academic-style research report
- **Summary**: Executive summary with key findings
- **Bullet Points**: Structured bullet-point format

## 🧪 Testing

### Test Connections
```bash
curl -X GET "http://localhost:8000/api/test-connections"
```

### Test Research Manager
```bash
curl -X GET "http://localhost:8000/api/test-research-manager"
```

## 📁 Project Structure

```
multi-agent-research-assistant/
├── backend/
│   ├── agents/              # AI agent implementations
│   │   ├── manager.py       # Research Manager Agent
│   │   ├── retrieval.py     # Information Retrieval Agent
│   │   ├── analysis.py      # Document Analysis Agent
│   │   ├── evaluation.py    # Critical Evaluation Agent
│   │   └── report.py        # Report Generation Agent
│   ├── graph/               # Workflow orchestration
│   │   ├── research_graph.py
│   │   └── routers.py
│   ├── models/              # Data models
│   │   └── state.py
│   ├── services/            # Core services
│   │   ├── ollama_client.py
│   │   └── research_service.py
│   ├── tools/               # Utility tools
│   │   ├── web_search.py
│   │   ├── summarization.py
│   │   └── citation.py
│   ├── config.py
│   └── main.py              # FastAPI application
├── frontend/                # React frontend (optional)
│   └── src/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .gitignore
└── README.md
```

## 🔍 How It Works

1. **Research Planning**: The Research Manager breaks down your question into 3-5 sub-questions
2. **Information Gathering**: The Retrieval Agent searches for relevant sources using optimized keywords
3. **Content Analysis**: The Analysis Agent extracts key insights from each source
4. **Quality Evaluation**: The Evaluation Agent assesses information quality and identifies gaps
5. **Report Generation**: The Report Agent creates a comprehensive research report with citations

## 🎯 Use Cases

- **Academic Research**: Literature reviews, research proposals
- **Market Research**: Industry analysis, competitive intelligence
- **Content Creation**: Blog posts, articles, white papers
- **Due Diligence**: Investment research, vendor evaluation
- **Policy Analysis**: Government reports, regulatory research

## 🔐 Security Considerations

- API keys are stored in environment variables
- No sensitive data is logged
- Rate limiting on API endpoints
- Input validation for all user inputs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**1. Ollama Connection Failed**
- Ensure Ollama is running: `ollama serve`
- Check if the model is installed: `ollama list`
- Verify the OLLAMA_HOST in your .env file

**2. Tavily API Errors**
- Verify your API key is correct
- Check your Tavily account usage limits
- Ensure TAVILY_API_KEY is set in your .env file

**3. Research Stalls**
- The system includes automatic recovery mechanisms
- Check the `/api/research/{id}/messages` endpoint for detailed logs
- Restart the research if needed

### Debug Mode
Set `DEBUG=True` in your .env file for verbose logging.

## 📞 Support

For support, email [zainshafique23@gmail.com] or create an issue on GitHub.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM capabilities
- [Tavily](https://tavily.com/) for web search API
- [LangChain](https://langchain.com/) for AI framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
