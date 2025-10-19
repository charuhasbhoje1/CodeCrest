# PraisonAI MSME News Aggregator - Setup and Usage Guide

This project implements an enhanced Flask + MongoDB RAG-powered news aggregator specifically designed for MSME (Micro, Small, and Medium Enterprises) sector analysis using **PraisonAI multi-agent system** and NewsData.io API.

## 🚀 **New Features with PraisonAI Integration**

- **🤖 Multi-Agent AI System**: Specialized agents for news analysis, financial insights, company matching, and dashboard generation
- **🧠 Intelligent Analysis**: Advanced AI-powered analysis of news articles and company data
- **📊 Smart Dashboards**: Dynamic dashboard generation based on user queries and AI insights
- **💰 Financial Intelligence**: Automated financial analysis and performance benchmarking
- **🎯 Strategic Recommendations**: AI-powered growth strategies and market insights
- **🔄 Self-Reflection**: Agents that learn and improve from interactions

## 🏗️ **Architecture Overview**

### **PraisonAI Agent System**
1. **News Analyzer Agent**: Analyzes news for MSME relevance and sentiment
2. **Financial Advisor Agent**: Provides financial analysis and benchmarking
3. **Company Matcher Agent**: Finds relevant companies based on criteria
4. **Dashboard Generator Agent**: Creates intelligent visualizations
5. **Market Intelligence Agent**: Provides strategic market insights

### **Enhanced Workflow**
```
User Query → Multi-Agent Analysis → Enhanced Response → Intelligent Dashboard
     ↓              ↓                    ↓                    ↓
News Search → AI Analysis → Strategic Insights → Dynamic Charts
Company Search → Financial Analysis → Recommendations → Visualizations
```

## 📋 **Installation Guide**

### **Prerequisites**
- Python 3.8 or higher
- MongoDB (local or Atlas)
- OpenAI API key
- NewsData.io API key

### **Step 1: Environment Setup**

```bash
# Create project directory
mkdir msme-praison-news-aggregator
cd msme-praison-news-aggregator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install enhanced dependencies
pip install -r requirements-praison-enhanced.txt
```

### **Step 2: API Keys Configuration**

Create a `.env` file:
```bash
# OpenAI API Key (Required for PraisonAI)
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
DB_NAME=news_aggregator

# NewsData.io API Key
NEWS_API_KEY=pub_179e18cbbc0c4e7091371a2d67fba1c0

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### **Step 3: PraisonAI Configuration**

The system uses the `praison_agents_config.yaml` file for agent configuration. This file defines:
- Agent roles and capabilities
- Workflow definitions
- Use case configurations
- Agent collaboration patterns

### **Step 4: Data Files**

Ensure you have the CSV files:
- `DataSet - SupplierMSMES.csv` - MSME companies data
- `MSME_32hai.csv` - Financial data

## 🚀 **Usage Guide**

### **Starting the Enhanced Application**

```bash
# Start the enhanced Flask application
python flask-rag-praison-enhanced.py
```

The application will start on `http://localhost:8000`

### **Initial Setup Steps**

1. **Load MSME Data**
   ```bash
   curl -X POST http://localhost:8000/api/load-data
   ```

2. **Check PraisonAI Status**
   ```bash
   curl -X GET http://localhost:8000/api/praison-status
   ```

3. **Fetch News**
   ```bash
   curl -X POST http://localhost:8000/api/fetch-news \
     -H "Content-Type: application/json" \
     -d '{"query": "MSME manufacturing technology", "country": "in"}'
   ```

### **Enhanced Chat Interface**

The chatbot now provides:
- **AI-powered analysis** of news articles
- **Financial insights** for companies
- **Strategic recommendations**
- **Market intelligence**

#### **Example Queries**

1. **Financial Analysis**
   ```
   "Analyze the financial performance of manufacturing companies in Tamil Nadu"
   ```

2. **Market Trends**
   ```
   "What are the latest trends in MSME technology adoption?"
   ```

3. **Strategic Insights**
   ```
   "Recommend growth strategies for textile MSMEs based on current market conditions"
   ```

4. **Company Matching**
   ```
   "Find healthcare companies with good export performance and growth potential"
   ```

## 🔧 **API Endpoints**

### **Enhanced Endpoints**

- `GET /api/praison-status` - Check PraisonAI integration status
- `POST /api/chat` - Enhanced chatbot with AI agents
- `POST /api/dashboard` - Intelligent dashboard generation

### **Example API Usage**

**Enhanced Chat with AI Analysis:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze the impact of recent government policies on MSME manufacturing sector"
  }'
```

**Response includes:**
- News analysis with sentiment scores
- Financial insights and benchmarking
- Strategic recommendations
- Market intelligence insights
- Enhanced dashboard data

## 🎯 **PraisonAI Agent Capabilities**

### **News Analyzer Agent**
- Sentiment analysis of news articles
- Trend identification and pattern recognition
- Policy impact assessment
- Sector-specific relevance scoring

### **Financial Advisor Agent**
- Performance benchmarking against industry standards
- Financial health scoring (0-100)
- Growth opportunity identification
- Risk assessment and mitigation strategies

### **Company Matcher Agent**
- Semantic matching based on user criteria
- Sector and location-based filtering
- Performance-based ranking
- Recommendation rationale

### **Dashboard Generator Agent**
- Dynamic chart generation based on data
- Interactive visualization recommendations
- Trend analysis charts
- Comparative analysis visualizations

### **Market Intelligence Agent**
- Competitive landscape analysis
- Market trend forecasting
- Strategic growth recommendations
- Risk assessment and opportunities

## 📊 **Enhanced Dashboard Features**

### **Intelligent Visualizations**
- **News Analysis Charts**: Sentiment distribution, trend analysis
- **Financial Performance Charts**: Benchmarking, growth metrics
- **Company Analysis Charts**: Sector distribution, performance rankings
- **Market Intelligence Charts**: Trend analysis, opportunity mapping

### **Dynamic Filtering**
- User query-based chart generation
- AI-recommended visualizations
- Interactive filtering options
- Real-time data updates

## 🔍 **Advanced Features**

### **Self-Reflection Capabilities**
- Agents learn from user interactions
- Continuous improvement of analysis quality
- Adaptive response generation
- Context-aware recommendations

### **Multi-Agent Collaboration**
- Agents work together for comprehensive analysis
- Cross-agent insights and recommendations
- Integrated workflow execution
- Holistic business intelligence

### **Intelligent Caching**
- AI-powered result caching
- Context-aware data retrieval
- Performance optimization
- Smart recommendation engine

## 🛠️ **Configuration Options**

### **Agent Customization**
Modify `praison_agents_config.yaml` to:
- Add new agent types
- Customize agent instructions
- Define new workflows
- Configure agent collaboration patterns

### **Model Configuration**
- OpenAI model selection
- Temperature and token settings
- Response length configuration
- Agent-specific parameters

## 🚨 **Troubleshooting**

### **Common Issues**

1. **PraisonAI Not Available**
   ```
   Error: PraisonAI not installed
   ```
   **Solution**: Install with `pip install praisonaiagents`

2. **OpenAI API Key Missing**
   ```
   Error: OPENAI_API_KEY not configured
   ```
   **Solution**: Set environment variable or add to .env file

3. **Agent Initialization Failed**
   ```
   Error: Agents not initialized
   ```
   **Solution**: Check OpenAI API key and internet connectivity

4. **Enhanced Features Not Working**
   ```
   Warning: Using fallback system
   ```
   **Solution**: Ensure PraisonAI is properly installed and configured

### **Performance Optimization**

1. **Agent Response Time**
   - Use appropriate OpenAI model for your needs
   - Configure token limits appropriately
   - Implement response caching

2. **Memory Management**
   - Monitor agent memory usage
   - Implement agent cleanup procedures
   - Use efficient data structures

3. **API Rate Limits**
   - Implement request throttling
   - Use batch processing where possible
   - Monitor OpenAI API usage

## 📈 **Scaling and Production**

### **Production Deployment**

1. **Environment Configuration**
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=False
   export OPENAI_API_KEY=your_production_key
   ```

2. **WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 flask-rag-praison-enhanced:app
   ```

3. **Database Optimization**
   - Enable MongoDB authentication
   - Use SSL/TLS connections
   - Implement connection pooling

### **Monitoring and Analytics**

- Monitor agent performance metrics
- Track API usage and costs
- Implement logging and error tracking
- Set up health checks and alerts

## 🔮 **Future Enhancements**

### **Planned Features**
- **Voice Interface**: Real-time voice interaction with agents
- **Mobile App**: Native mobile application
- **Advanced Analytics**: Machine learning-powered insights
- **Integration APIs**: Third-party system integrations
- **Custom Agent Training**: Domain-specific agent training

### **Extension Possibilities**
- **Industry-Specific Agents**: Specialized agents for different sectors
- **Multi-Language Support**: Agents in multiple languages
- **Real-Time Streaming**: Live data processing and analysis
- **Blockchain Integration**: Decentralized data and analysis

## 📚 **Documentation and Support**

### **Additional Resources**
- [PraisonAI Documentation](https://docs.praison.ai/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

### **Community Support**
- GitHub Issues for bug reports
- Community forums for discussions
- Documentation contributions welcome
- Feature request submissions

## 📄 **License and Compliance**

This project integrates multiple technologies:
- **PraisonAI**: MIT License
- **OpenAI**: Commercial License
- **MongoDB**: Community License
- **Flask**: BSD License

Ensure compliance with all license terms and API usage policies.

---

**Note**: This enhanced implementation provides a production-ready MSME news aggregator with advanced AI capabilities. The PraisonAI integration enables sophisticated analysis, intelligent recommendations, and dynamic insights that go far beyond basic RAG functionality.
