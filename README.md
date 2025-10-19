# 🌟 GlobeIn - AI-Powered MSME Financial Ecosystem

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-brightgreen.svg)](https://mongodb.com)

> **Revolutionizing MSME finance through Agentic AI and real-time market intelligence**

A next-generation fintech platform that leverages advanced AI agents to democratize financial services for Micro, Small & Medium Enterprises (MSMEs). Features intelligent credit scoring, real-time news aggregation, supplier discovery, and comprehensive market analytics.

## 🚀 Features

- **AI-Powered Credit Assessment**: Alternative credit scoring using non-traditional data
- **Real-time Market Intelligence**: News aggregation and sentiment analysis
- **MSME Directory**: Advanced supplier discovery and matching
- **Performance Analytics**: Dynamic scoring and risk assessment
- **Responsive Design**: Mobile-first user interface

## 🛠️ Tech Stack

- **Backend**: Flask, Python
- **Database**: MongoDB
- **Frontend**: HTML5, CSS3, JavaScript
- **AI/ML**: PraisonAI, Pandas, NumPy
- **APIs**: NewsData.io, JWT Authentication

## 📦 Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/globein-msme-platform.git
cd globein-msme-platform
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up MongoDB
- Install MongoDB locally or use MongoDB Atlas
- Create a database named `news_aggregator`

4. Configure environment variables
```bash
cp env.example .env
# Edit .env with your actual API keys and configuration
```

5. Run the application
```bash
python main.py
```

6. Open your browser and visit `http://localhost:5000`

## 🌐 Live Demo

Visit: `http://localhost:5000`

## 📁 Project Structure

```
CodeCrest/
├── main.py                          # Main Flask application
├── requirements.txt                 # Python dependencies
├── README.md                       # Project documentation
├── .gitignore                      # Git ignore file
├── env.example                     # Environment variables template
├── models/
│   └── database.py                 # Database models and connections
├── templates/                      # HTML templates
│   ├── index.html                  # Dashboard/Analytics page
│   ├── news_new.html              # News aggregation page
│   ├── profile.html               # User profile page
│   ├── signin.html                # Sign in page
│   ├── signup.html                # Sign up page
│   ├── homepage.html              # Landing page
│   ├── buyer.html                 # Buyer dashboard
│   └── msme_directory_enhanced_search.html  # MSME directory
├── static/
│   └── images/                    # Static assets
├── MSME_32hai.csv                 # Sample MSME data
└── DataSet - SupplierMSMES.csv   # Sample supplier data
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
MONGODB_URI=mongodb://localhost:27017/news_aggregator

# News API
NEWS_API_KEY=your_news_api_key_here
NEWS_BASE_URL=https://newsdata.io/api

# JWT
JWT_SECRET_KEY=your_jwt_secret_key_here

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
```

### API Keys Required

1. **NewsData.io API Key**: Get your free API key from [NewsData.io](https://newsdata.io/)
2. **JWT Secret Key**: Generate a secure secret key for JWT authentication

## 🚀 Features in Detail

### 1. AI-Powered Credit Assessment
- Alternative credit scoring using non-traditional data
- Real-time risk assessment
- Performance scoring based on multiple factors

### 2. Real-time Market Intelligence
- News aggregation from multiple sources
- Sentiment analysis
- Market trend identification

### 3. MSME Directory
- Advanced supplier discovery
- Company matching and filtering
- Detailed company profiles

### 4. Performance Analytics
- Dynamic scoring algorithms
- Risk assessment tools
- Market performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- PraisonAI for the AI agent framework
- NewsData.io for the news API
- MongoDB for the database solution
- Flask community for the web framework

## 📞 Support

For support, email support@globein.com or join our Slack channel.

---

**Built with ❤️ for the MSME community**