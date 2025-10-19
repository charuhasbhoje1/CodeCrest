# PraisonAI Integration for MSME News Aggregator
# Enhanced Flask application with PraisonAI multi-agent system

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import pymongo
from pymongo import MongoClient
import pandas as pd
import numpy as np
import requests
import plotly.graph_objs as go
import plotly.utils
import re
from collections import Counter
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# PraisonAI imports
try:
    from praisonaiagents import Agent, PraisonAIAgents
    PRAISON_AVAILABLE = True
except ImportError:
    PRAISON_AVAILABLE = False
    print("Warning: PraisonAI not installed. Install with: pip install praisonaiagents")

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    NEWS_API_KEY = "pub_179e18cbbc0c4e7091371a2d67fba1c0"
    DB_NAME = "news_aggregator"
    NEWS_BASE_URL = "https://newsdata.io/api/1"
    BASE_DIR = Path(__file__).resolve().parent
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # PraisonAI Configuration
    PRAISON_CONFIG_PATH = BASE_DIR / "praison_agents_config.yaml"

# ==============================================================================
# PRAISONAI AGENT SYSTEM
# ==============================================================================

class PraisonAIManager:
    def __init__(self):
        self.agents = {}
        self.initialized = False
        
    def initialize_agents(self):
        """Initialize PraisonAI agents based on configuration"""
        if not PRAISON_AVAILABLE:
            print("PraisonAI not available. Using fallback system.")
            return False
            
        try:
            # Initialize 3 main agents matching architecture diagram
            self.agents = {
                'financial_analyst': Agent(
                    instructions="""You are a Financial Analyst specializing in MSME financial analysis and performance evaluation.

Your role is to:
- Analyze financial data and calculate key ratios (ROA, ROE, profit margins, debt-to-equity)
- Provide financial health scores and performance benchmarking
- Identify financial strengths, weaknesses, and improvement opportunities
- Generate financial reports with actionable insights

Available Tools:
- get_stock_data(company): Get real-time stock prices and market data
- get_financial_ratios(company_data): Calculate financial ratios and metrics
- get_market_data(sector): Get sector performance data

Always provide:
- Financial health score (0-100)
- Key performance indicators
- Comparative analysis against industry benchmarks
- Specific recommendations for financial improvement
- Risk assessment and mitigation strategies

IMPORTANT: Do not use emoji characters or special Unicode symbols in your responses. Use only standard ASCII characters."""
                ),
                
                'news_analyst': Agent(
                    instructions="""You are a News Analyst specializing in MSME-relevant news analysis and market intelligence.

Your role is to:
- Analyze news articles for MSME relevance and impact
- Perform sentiment analysis on market trends
- Identify policy changes affecting MSMEs
- Monitor sector-specific developments and opportunities

Available Tools:
- search_news(query, filters): Search for relevant news articles
- search_web(query): Search web for additional market intelligence
- search_market_trends(sector, location): Get comprehensive market trends

Always provide:
- Sentiment analysis (positive/negative/neutral)
- Key themes and trends affecting MSMEs
- Policy impact assessment
- Market opportunity identification
- Risk factors from news analysis

IMPORTANT: Do not use emoji characters or special Unicode symbols in your responses. Use only standard ASCII characters."""
                ),
                
                'growth_strategist': Agent(
                    instructions="""You are a Growth Strategist specializing in MSME growth strategies and market expansion.

Your role is to:
- Develop comprehensive growth strategies for MSMEs
- Analyze market opportunities and competitive landscapes
- Provide strategic recommendations for expansion
- Create actionable business development plans

Available Tools:
- search_market_trends(sector, location): Analyze market trends and opportunities
- get_market_data(sector): Get sector performance data
- search_web(query): Research competitive landscape

Always provide:
- Growth opportunity analysis
- Strategic recommendations (short/medium/long-term)
- Competitive analysis and positioning
- Risk assessment and mitigation
- Implementation roadmap with specific actions

IMPORTANT: Do not use emoji characters or special Unicode symbols in your responses. Use only standard ASCII characters."""
                )
            }
            
            # Create multi-agent system
            self.multi_agent_system = PraisonAIAgents(
                agents=list(self.agents.values())
            )
            
            self.initialized = True
            print("PraisonAI agents initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing PraisonAI agents: {e}")
            return False
    
    def analyze_news_with_agents(self, news_articles, user_query):
        """Use PraisonAI agents to analyze news articles"""
        if not self.initialized:
            return self._fallback_news_analysis(news_articles, user_query)
        
        try:
            # Prepare news data for analysis
            news_summary = self._prepare_news_summary(news_articles)
            
            # Use news analyzer agent
            analysis_prompt = f"""
            Analyze these news articles for MSME sector relevance:
            
            User Query: {user_query}
            
            News Articles:
            {news_summary}
            
            Provide:
            1. Relevance analysis for each article
            2. Sentiment assessment
            3. Key trends identified
            4. Sector impact assessment
            5. Actionable insights for MSMEs
            """
            
            news_analysis = self.agents['news_analyzer'].start(analysis_prompt)
            
            # Use market intelligence agent for strategic insights
            intelligence_prompt = f"""
            Based on the news analysis, provide market intelligence insights:
            
            News Analysis: {news_analysis}
            User Query: {user_query}
            
            Provide:
            1. Market trend analysis
            2. Strategic recommendations
            3. Growth opportunities
            4. Risk assessment
            5. Action plan for MSMEs
            """
            
            market_insights = self.agents['market_intelligence'].start(intelligence_prompt)
            
            return {
                'news_analysis': news_analysis,
                'market_insights': market_insights,
                'enhanced': True
            }
            
        except Exception as e:
            print(f"Error in PraisonAI news analysis: {e}")
            return self._fallback_news_analysis(news_articles, user_query)
    
    def analyze_companies_with_agents(self, companies, user_query):
        """Use PraisonAI agents to analyze companies"""
        if not self.initialized:
            return self._fallback_company_analysis(companies, user_query)
        
        try:
            # Prepare company data for analysis
            company_summary = self._prepare_company_summary(companies)
            
            # Use company matcher agent
            matching_prompt = f"""
            Analyze these MSME companies based on user requirements:
            
            User Query: {user_query}
            
            Companies:
            {company_summary}
            
            Provide:
            1. Company matching scores
            2. Sector analysis
            3. Performance comparison
            4. Recommendation rationale
            5. Best-fit companies for the query
            """
            
            company_analysis = self.agents['company_matcher'].start(matching_prompt)
            
            # Use financial advisor for financial insights
            financial_prompt = f"""
            Provide financial analysis for these companies:
            
            Company Analysis: {company_analysis}
            User Query: {user_query}
            
            Provide:
            1. Financial health assessment
            2. Performance benchmarking
            3. Growth opportunities
            4. Risk analysis
            5. Strategic recommendations
            """
            
            financial_insights = self.agents['financial_advisor'].start(financial_prompt)
            
            return {
                'company_analysis': company_analysis,
                'financial_insights': financial_insights,
                'enhanced': True
            }
            
        except Exception as e:
            print(f"Error in PraisonAI company analysis: {e}")
            return self._fallback_company_analysis(companies, user_query)
    
    def generate_dashboard_with_agents(self, data, user_query):
        """Use PraisonAI agents to generate intelligent dashboards"""
        if not self.initialized:
            return self._fallback_dashboard_generation(data, user_query)
        
        try:
            # Use dashboard generator agent
            dashboard_prompt = f"""
            Generate an intelligent dashboard based on the data and user requirements:
            
            User Query: {user_query}
            
            Data Summary:
            {json.dumps(data, indent=2)}
            
            Provide:
            1. Recommended chart types
            2. Data visualization strategy
            3. Interactive dashboard design
            4. Key metrics to highlight
            5. Trend analysis visualizations
            """
            
            dashboard_recommendations = self.agents['dashboard_generator'].start(dashboard_prompt)
            
            return {
                'dashboard_recommendations': dashboard_recommendations,
                'enhanced': True
            }
            
        except Exception as e:
            print(f"Error in PraisonAI dashboard generation: {e}")
            return self._fallback_dashboard_generation(data, user_query)
    
    def _prepare_news_summary(self, news_articles):
        """Prepare news articles summary for agent analysis"""
        summary = []
        for i, article in enumerate(news_articles[:10], 1):
            summary.append(f"""
            Article {i}:
            Title: {article.get('title', 'No Title')}
            Description: {article.get('description', 'No Description')}
            Source: {article.get('source_name', 'Unknown')}
            Date: {article.get('pubDate', 'Unknown')}
            """)
        return "\n".join(summary)
    
    def _prepare_company_summary(self, companies):
        """Prepare company data summary for agent analysis"""
        summary = []
        for i, company in enumerate(companies[:10], 1):
            summary.append(f"""
            Company {i}:
            Name: {company.get('Company_Name', 'Unknown')}
            Sector: {company.get('Sector', 'Unknown')}
            Location: {company.get('Location', 'Unknown')}
            Products: {company.get('Primary_Products', 'Not specified')}
            Performance Score: {company.get('Overall_Performance_Score', 'N/A')}
            """)
        return "\n".join(summary)
    
    def _fallback_news_analysis(self, news_articles, user_query):
        """Fallback news analysis when PraisonAI is not available"""
        return {
            'news_analysis': f"Found {len(news_articles)} relevant news articles for query: {user_query}",
            'market_insights': "Basic news analysis completed. For enhanced insights, ensure PraisonAI is properly configured.",
            'enhanced': False
        }
    
    def _fallback_company_analysis(self, companies, user_query):
        """Fallback company analysis when PraisonAI is not available"""
        return {
            'company_analysis': f"Found {len(companies)} relevant companies for query: {user_query}",
            'financial_insights': "Basic company analysis completed. For enhanced insights, ensure PraisonAI is properly configured.",
            'enhanced': False
        }
    
    def _fallback_dashboard_generation(self, data, user_query):
        """Fallback dashboard generation when PraisonAI is not available"""
        return {
            'dashboard_recommendations': f"Basic dashboard generated for query: {user_query}",
            'enhanced': False
        }

# ==============================================================================
# FINANCIAL TOOLS MANAGER
# ==============================================================================

class FinancialToolsManager:
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        
    def get_stock_data(self, company_name):
        """Get stock data using YFinance"""
        try:
            import yfinance as yf
            
            # Try to find stock symbol for the company
            ticker = self._find_ticker_symbol(company_name)
            if not ticker:
                return {"error": f"No stock data available for {company_name}"}
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                "company": company_name,
                "ticker": ticker,
                "current_price": info.get("currentPrice", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                "volume": info.get("volume", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A")
            }
        except ImportError:
            return {"error": "YFinance not installed. Install with: pip install yfinance"}
        except Exception as e:
            return {"error": f"Error fetching stock data: {str(e)}"}
    
    def _find_ticker_symbol(self, company_name):
        """Find ticker symbol for company name"""
        # Common Indian company mappings
        ticker_mappings = {
            "reliance": "RELIANCE.NS",
            "tata": "TATAMOTORS.NS",
            "infosys": "INFY.NS",
            "tcs": "TCS.NS",
            "hdfc": "HDFCBANK.NS",
            "icici": "ICICIBANK.NS",
            "wipro": "WIPRO.NS",
            "bharti": "BHARTIARTL.NS",
            "itc": "ITC.NS",
            "hindalco": "HINDALCO.NS"
        }
        
        company_lower = company_name.lower()
        for key, ticker in ticker_mappings.items():
            if key in company_lower:
                return ticker
        
        # For MSME companies, most won't be publicly traded
        return None
    
    def get_financial_ratios(self, company_data):
        """Calculate financial ratios from company data"""
        try:
            ratios = {}
            
            # Extract financial data if available
            revenue = company_data.get('Revenue', 0)
            profit = company_data.get('Profit', 0)
            assets = company_data.get('Assets', 0)
            equity = company_data.get('Equity', 0)
            debt = company_data.get('Debt', 0)
            
            # Calculate ratios
            if revenue and revenue > 0:
                ratios['profit_margin'] = (profit / revenue) * 100 if profit else 0
                ratios['revenue_growth'] = company_data.get('Revenue_Growth', 0)
            
            if assets and assets > 0:
                ratios['roa'] = (profit / assets) * 100 if profit else 0  # Return on Assets
            
            if equity and equity > 0:
                ratios['roe'] = (profit / equity) * 100 if profit else 0  # Return on Equity
            
            if debt and equity:
                ratios['debt_to_equity'] = debt / equity if equity > 0 else 0
            
            # Performance score calculation
            performance_score = company_data.get('Overall_Performance_Score', 0)
            ratios['performance_score'] = performance_score
            
            # Export performance
            export_markets = company_data.get('Export_Markets', '')
            ratios['export_presence'] = len(export_markets.split(',')) if export_markets else 0
            
            return ratios
            
        except Exception as e:
            return {"error": f"Error calculating financial ratios: {str(e)}"}
    
    def get_market_data(self, sector):
        """Get market data for a sector"""
        try:
            import yfinance as yf
            
            # Sector-specific ETF mappings for Indian markets
            sector_etfs = {
                'technology': 'NIFTYIT.NS',
                'banking': 'NIFTYBANK.NS',
                'pharmaceutical': 'NIFTYPHARMA.NS',
                'automotive': 'NIFTYAUTO.NS',
                'energy': 'NIFTYENERGY.NS',
                'fmcg': 'NIFTYFMCG.NS',
                'metal': 'NIFTYMETAL.NS',
                'realty': 'NIFTYREALTY.NS',
                'media': 'NIFTYMEDIA.NS',
                'psu': 'NIFTYPSU.NS'
            }
            
            sector_lower = sector.lower()
            ticker = None
            
            for key, etf in sector_etfs.items():
                if key in sector_lower:
                    ticker = etf
                    break
            
            if not ticker:
                return {"error": f"No market data available for sector: {sector}"}
            
            etf = yf.Ticker(ticker)
            info = etf.info
            
            return {
                "sector": sector,
                "ticker": ticker,
                "current_price": info.get("currentPrice", "N/A"),
                "change_percent": info.get("regularMarketChangePercent", "N/A"),
                "volume": info.get("volume", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A")
            }
            
        except ImportError:
            return {"error": "YFinance not installed. Install with: pip install yfinance"}
        except Exception as e:
            return {"error": f"Error fetching market data: {str(e)}"}

# ==============================================================================
# SEARCH TOOLS MANAGER
# ==============================================================================

class SearchToolsManager:
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY", "")
        
    def search_news(self, query, filters=None):
        """Enhanced news search using NewsData.io API"""
        try:
            params = {
                "apikey": self.news_api_key,
                "q": query,
                "language": "en",
                "country": "in",
                "size": 20
            }
            
            if filters:
                if 'category' in filters:
                    params['category'] = filters['category']
                if 'from_date' in filters:
                    params['from_date'] = filters['from_date']
                if 'to_date' in filters:
                    params['to_date'] = filters['to_date']
            
            response = requests.get("https://newsdata.io/api/1/news", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                articles = data.get("results", [])
                return {
                    "success": True,
                    "articles": articles,
                    "total_results": len(articles)
                }
            else:
                return {
                    "success": False,
                    "error": data.get("message", "Unknown error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching news: {str(e)}"
            }
    
    def search_web(self, query):
        """Search web using DuckDuckGo"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=10))
                
            return {
                "success": True,
                "results": results,
                "total_results": len(results)
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "DuckDuckGo search not installed. Install with: pip install duckduckgo-search"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching web: {str(e)}"
            }
    
    def search_market_trends(self, sector, location=None):
        """Combined search for market intelligence"""
        try:
            # Build search query
            query_parts = [f"{sector} market trends"]
            if location:
                query_parts.append(f"in {location}")
            
            query = " ".join(query_parts)
            
            # Search news
            news_results = self.search_news(query, {"category": "business"})
            
            # Search web for additional insights
            web_results = self.search_web(f"{query} analysis report")
            
            return {
                "sector": sector,
                "location": location,
                "news_results": news_results,
                "web_results": web_results,
                "combined_query": query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching market trends: {str(e)}"
            }

# ==============================================================================
# DATA PROCESSING LAYER
# ==============================================================================

class DataProcessingLayer:
    def __init__(self):
        pass
    
    def process_financial_data(self, raw_data):
        """Transform raw financial data to Financial Reports format"""
        try:
            processed = {
                "financial_reports": {
                    "company_name": raw_data.get("company", "Unknown"),
                    "stock_data": raw_data.get("stock_data", {}),
                    "financial_ratios": raw_data.get("ratios", {}),
                    "performance_metrics": {
                        "profit_margin": raw_data.get("ratios", {}).get("profit_margin", 0),
                        "roa": raw_data.get("ratios", {}).get("roa", 0),
                        "roe": raw_data.get("ratios", {}).get("roe", 0),
                        "debt_to_equity": raw_data.get("ratios", {}).get("debt_to_equity", 0),
                        "performance_score": raw_data.get("ratios", {}).get("performance_score", 0)
                    },
                    "export_analysis": {
                        "export_presence": raw_data.get("ratios", {}).get("export_presence", 0),
                        "export_markets": raw_data.get("export_markets", "")
                    }
                }
            }
            
            return processed
            
        except Exception as e:
            return {"error": f"Error processing financial data: {str(e)}"}
    
    def process_news_data(self, raw_news):
        """Transform raw news data to News Analysis format"""
        try:
            articles = raw_news.get("articles", [])
            
            processed = {
                "news_analysis": {
                    "total_articles": len(articles),
                    "articles": [],
                    "sentiment_summary": {
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0
                    },
                    "key_themes": [],
                    "sources": []
                }
            }
            
            for article in articles[:10]:  # Limit to top 10
                article_data = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source_name", ""),
                    "url": article.get("link", ""),
                    "published_date": article.get("pubDate", ""),
                    "category": article.get("category", [])
                }
                processed["news_analysis"]["articles"].append(article_data)
                
                # Track sources
                source = article.get("source_name", "Unknown")
                if source not in processed["news_analysis"]["sources"]:
                    processed["news_analysis"]["sources"].append(source)
            
            return processed
            
        except Exception as e:
            return {"error": f"Error processing news data: {str(e)}"}
    
    def process_growth_data(self, market_data, company_data):
        """Transform market and company data to Growth Recommendations format"""
        try:
            processed = {
                "growth_recommendations": {
                    "market_analysis": {
                        "sector_performance": market_data.get("sector_data", {}),
                        "market_trends": market_data.get("trends", {}),
                        "growth_opportunities": []
                    },
                    "company_analysis": {
                        "current_position": company_data.get("position", {}),
                        "strengths": company_data.get("strengths", []),
                        "weaknesses": company_data.get("weaknesses", []),
                        "growth_potential": company_data.get("growth_potential", 0)
                    },
                    "strategic_recommendations": {
                        "short_term": [],
                        "medium_term": [],
                        "long_term": []
                    },
                    "risk_assessment": {
                        "market_risks": [],
                        "operational_risks": [],
                        "financial_risks": []
                    }
                }
            }
            
            return processed
            
        except Exception as e:
            return {"error": f"Error processing growth data: {str(e)}"}
    
    def generate_structured_output(self, agent_results):
        """Format agent results for frontend display"""
        try:
            structured = {
                "financial_reports": {},
                "news_analysis": {},
                "growth_recommendations": {},
                "summary": {
                    "query": agent_results.get("query", ""),
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": agent_results.get("agents_used", []),
                    "confidence_score": agent_results.get("confidence", 0)
                }
            }
            
            # Process each agent's results
            if "financial_analysis" in agent_results:
                structured["financial_reports"] = self.process_financial_data(
                    agent_results["financial_analysis"]
                )
            
            if "news_analysis" in agent_results:
                structured["news_analysis"] = self.process_news_data(
                    agent_results["news_analysis"]
                )
            
            if "growth_strategy" in agent_results:
                structured["growth_recommendations"] = self.process_growth_data(
                    agent_results["growth_strategy"].get("market_data", {}),
                    agent_results["growth_strategy"].get("company_data", {})
                )
            
            return structured
            
        except Exception as e:
            return {"error": f"Error generating structured output: {str(e)}"}

# ==============================================================================
# ENHANCED SERVICES WITH PRAISONAI INTEGRATION
# ==============================================================================

class EnhancedRAGService:
    def __init__(self, db_manager, similarity_service, praison_manager):
        self.db_manager = db_manager
        self.similarity_service = similarity_service
        self.praison_manager = praison_manager
        
        # Initialize tools managers
        self.financial_tools = FinancialToolsManager()
        self.search_tools = SearchToolsManager()
        self.data_processor = DataProcessingLayer()
        
    def enhanced_semantic_search_news(self, query, limit=10):
        """Enhanced news search with PraisonAI analysis"""
        # Get basic search results
        news_articles = self._basic_news_search(query, limit)
        
        # Enhance with PraisonAI analysis
        enhanced_analysis = self.praison_manager.analyze_news_with_agents(news_articles, query)
        
        return {
            'articles': news_articles,
            'analysis': enhanced_analysis,
            'enhanced': enhanced_analysis.get('enhanced', False)
        }
    
    def enhanced_find_related_companies(self, query, limit=10):
        """Enhanced company search with PraisonAI analysis"""
        # Get basic search results
        companies = self._basic_company_search(query, limit)
        
        # Enhance with PraisonAI analysis
        enhanced_analysis = self.praison_manager.analyze_companies_with_agents(companies, query)
        
        return {
            'companies': companies,
            'analysis': enhanced_analysis,
            'enhanced': enhanced_analysis.get('enhanced', False)
        }
    
    def generate_enhanced_response(self, query, news_results, company_results):
        """Generate enhanced response using PraisonAI insights"""
        response_parts = []
        
        # Add news analysis
        if news_results.get('articles'):
            response_parts.append("📰 **News Analysis:**")
            response_parts.append(news_results['analysis']['news_analysis'])
            
            if news_results['analysis'].get('market_insights'):
                response_parts.append("\n🎯 **Market Intelligence:**")
                response_parts.append(news_results['analysis']['market_insights'])
        
        # Add company analysis
        if company_results.get('companies'):
            response_parts.append("\n🏢 **Company Analysis:**")
            response_parts.append(company_results['analysis']['company_analysis'])
            
            if company_results['analysis'].get('financial_insights'):
                response_parts.append("\n💰 **Financial Insights:**")
                response_parts.append(company_results['analysis']['financial_insights'])
        
        # Add enhancement indicator
        if news_results.get('enhanced') or company_results.get('enhanced'):
            response_parts.append("\n✨ *Analysis powered by PraisonAI multi-agent system*")
        
        return "\n".join(response_parts) if response_parts else f"No relevant information found for query: {query}"
    
    def _basic_news_search(self, query, limit):
        """Basic news search functionality"""
        query_keywords = set(self.similarity_service.find_keywords(query))
        articles = list(self.db_manager.news_collection.find())
        
        results = []
        for article in articles:
            article_keywords = set(article.get("keywords", []))
            
            if query_keywords and article_keywords:
                similarity = len(query_keywords.intersection(article_keywords)) / len(query_keywords.union(article_keywords))
            else:
                article_text = f"{article.get('title', '')} {article.get('description', '')}"
                similarity = self.similarity_service.calculate_similarity(query, article_text)
            
            if similarity > 0.1:
                article["similarity"] = similarity
                results.append(article)
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def _basic_company_search(self, query, limit):
        """Enhanced company search with location and sector filtering"""
        # Extract location and sector keywords
        locations = self._extract_locations(query)
        sectors = self._extract_sectors(query)
        query_keywords = set(self.similarity_service.find_keywords(query))
        
        companies = list(self.db_manager.companies_collection.find())
        
        # Check for generic queries that should return all companies
        query_lower = query.lower()
        generic_queries = ['msmes', 'msme', 'companies', 'company', 'list', 'all', 'show me', 'give me']
        is_generic_query = any(generic in query_lower for generic in generic_queries)
        
        # Pre-filter by location if specified
        if locations:
            companies = [c for c in companies if any(loc.lower() in c.get('Location', '').lower() for loc in locations)]
        
        # Pre-filter by sector if specified
        if sectors:
            companies = [c for c in companies if any(sect.lower() in c.get('Sector', '').lower() for sect in sectors)]
        
        results = []
        for company in companies:
            company_keywords = set(company.get("keywords", []))
            
            # Calculate similarity with multiple methods
            similarity_scores = []
            
            # Method 1: Keyword intersection
            if query_keywords and company_keywords:
                keyword_similarity = len(query_keywords.intersection(company_keywords)) / len(query_keywords.union(company_keywords))
                similarity_scores.append(keyword_similarity)
            
            # Method 2: Text similarity
            company_text = f"{company.get('Company_Name', '')} {company.get('Sector', '')} {company.get('Primary_Products', '')}"
            text_similarity = self.similarity_service.calculate_similarity(query, company_text)
            similarity_scores.append(text_similarity)
            
            # Method 3: Location bonus
            location_bonus = 0.0
            if locations:
                location_match = any(loc.lower() in company.get('Location', '').lower() for loc in locations)
                if location_match:
                    location_bonus = 0.2
            
            # Method 4: Sector bonus
            sector_bonus = 0.0
            if sectors:
                sector_match = any(sect.lower() in company.get('Sector', '').lower() for sect in sectors)
                if sector_match:
                    sector_bonus = 0.15
            
            # Method 5: Generic query bonus
            generic_bonus = 0.0
            if is_generic_query and not locations and not sectors:
                # For generic queries without specific filters, give all companies a base score
                generic_bonus = 0.1
            
            # Take the maximum similarity and add bonuses
            max_similarity = max(similarity_scores) if similarity_scores else 0.0
            final_similarity = min(1.0, max_similarity + location_bonus + sector_bonus + generic_bonus)
            
            # Lower threshold for better results, or use generic threshold for generic queries
            threshold = 0.03 if is_generic_query else 0.05
            
            if final_similarity > threshold:
                company["similarity"] = final_similarity
                results.append(company)
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def _extract_locations(self, query):
        """Extract location names from query"""
        locations = []
        query_lower = query.lower()
        
        # Common Indian cities and states
        indian_locations = [
            'tamil nadu', 'chennai', 'madras', 'coimbatore', 'salem', 'tiruchirapalli',
            'maharashtra', 'mumbai', 'pune', 'nagpur', 'nashik', 'aurangabad',
            'gujarat', 'ahmedabad', 'surat', 'vadodara', 'rajkot', 'gandhinagar',
            'karnataka', 'bangalore', 'mysore', 'hubli', 'mangalore',
            'delhi', 'new delhi', 'noida', 'gurgaon', 'faridabad',
            'west bengal', 'kolkata', 'howrah', 'durgapur',
            'rajasthan', 'jaipur', 'jodhpur', 'udaipur', 'kota',
            'uttar pradesh', 'lucknow', 'kanpur', 'agra', 'varanasi',
            'andhra pradesh', 'hyderabad', 'visakhapatnam', 'vijayawada',
            'telangana', 'telengana',
            'kerala', 'kochi', 'thiruvananthapuram', 'kozhikode',
            'punjab', 'chandigarh', 'ludhiana', 'amritsar',
            'haryana', 'panipat', 'rohtak', 'hisar',
            'madhya pradesh', 'bhopal', 'indore', 'gwalior', 'jabalpur',
            'odisha', 'bhubaneswar', 'cuttack', 'rourkela',
            'assam', 'guwahati', 'silchar', 'dibrugarh',
            'jammu and kashmir', 'srinagar', 'jammu',
            'himachal pradesh', 'shimla', 'dharamshala',
            'uttarakhand', 'dehradun', 'haridwar', 'rishikesh',
            'goa', 'panaji', 'margao',
            'manipur', 'imphal',
            'meghalaya', 'shillong',
            'mizoram', 'aizawl',
            'nagaland', 'kohima',
            'tripura', 'agartala',
            'sikkim', 'gangtok',
            'arunachal pradesh', 'itanagar',
            'chhattisgarh', 'raipur', 'bilaspur',
            'jharkhand', 'ranchi', 'jamshedpur', 'dhanbad',
            'bihar', 'patna', 'gaya', 'muzaffarpur'
        ]
        
        for location in indian_locations:
            if location in query_lower:
                locations.append(location)
        
        return locations
    
    def _extract_sectors(self, query):
        """Extract sector keywords from query"""
        sectors = []
        query_lower = query.lower()
        
        # Common MSME sectors
        sector_keywords = [
            'manufacturing', 'textile', 'textiles', 'chemical', 'chemicals',
            'pharmaceutical', 'pharma', 'food processing', 'food',
            'technology', 'tech', 'software', 'it', 'cybersecurity',
            'packaging', 'automotive', 'auto', 'electronics',
            'engineering', 'construction', 'infrastructure',
            'healthcare', 'medical', 'biotech', 'biotechnology',
            'agriculture', 'agri', 'farming', 'petrochemical',
            'petrochemicals', 'oil', 'gas', 'energy', 'power',
            'renewable', 'solar', 'wind', 'mining', 'metals',
            'steel', 'iron', 'aluminum', 'copper', 'plastic',
            'rubber', 'leather', 'garments', 'apparel', 'fashion',
            'furniture', 'wood', 'paper', 'printing', 'publishing',
            'tourism', 'hospitality', 'retail', 'wholesale',
            'logistics', 'transport', 'shipping', 'aviation',
            'banking', 'finance', 'insurance', 'real estate',
            'education', 'training', 'consulting', 'services'
        ]
        
        for sector in sector_keywords:
            if sector in query_lower:
                sectors.append(sector)
        
        return sectors

# ==============================================================================
# ENHANCED DASHBOARD SERVICE
# ==============================================================================

class EnhancedDashboardService:
    def __init__(self, db_manager, praison_manager):
        self.db_manager = db_manager
        self.praison_manager = praison_manager
    
    def generate_intelligent_dashboard(self, data, user_query):
        """Generate intelligent dashboard using PraisonAI agents"""
        # Get PraisonAI recommendations
        dashboard_recommendations = self.praison_manager.generate_dashboard_with_agents(data, user_query)
        
        # Generate enhanced charts based on recommendations
        charts = self._generate_enhanced_charts(data, dashboard_recommendations)
        
        return {
            'charts': charts,
            'recommendations': dashboard_recommendations,
            'enhanced': dashboard_recommendations.get('enhanced', False)
        }
    
    def _generate_enhanced_charts(self, data, recommendations):
        """Generate enhanced charts based on PraisonAI recommendations"""
        charts = {}
        
        # News charts
        news_data = data.get('news', {})
        if news_data.get('source_distribution'):
            charts['news_sources'] = self._create_enhanced_chart(
                'pie', news_data['source_distribution'], 
                'News Sources Distribution', 
                'Enhanced with PraisonAI insights'
            )
        
        if news_data.get('category_distribution'):
            charts['news_categories'] = self._create_enhanced_chart(
                'bar', news_data['category_distribution'], 
                'News Categories Analysis',
                'Trend analysis powered by AI'
            )
        
        # Company charts
        company_data = data.get('companies', {})
        if company_data.get('sector_distribution'):
            charts['company_sectors'] = self._create_enhanced_chart(
                'pie', company_data['sector_distribution'], 
                'MSME Sectors Distribution',
                'Intelligent sector analysis'
            )
        
        if company_data.get('location_distribution'):
            charts['company_locations'] = self._create_enhanced_chart(
                'bar', company_data['location_distribution'], 
                'MSME Companies by State',
                'Geographic analysis with insights'
            )
        
        return charts
    
    def _create_enhanced_chart(self, chart_type, data, title, subtitle):
        """Create enhanced chart with PraisonAI insights"""
        if not data:
            return None
            
        if chart_type == "pie":
            fig = go.Figure(data=[go.Pie(
                labels=list(data.keys()), 
                values=list(data.values()),
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
        elif chart_type == "bar":
            fig = go.Figure(data=[go.Bar(
                x=list(data.keys()), 
                y=list(data.values()),
                text=list(data.values()),
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
            )])
        else:
            return None
        
        fig.update_layout(
            title=f"{title}<br><sub>{subtitle}</sub>",
            showlegend=True,
            hovermode='closest'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

# ==============================================================================
# SIMPLE TEXT SIMILARITY (Keep existing implementation)
# ==============================================================================

class SimpleTextSimilarity:
    def __init__(self):
        pass
    
    def preprocess_text(self, text):
        """Simple text preprocessing"""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return text
    
    def get_word_vector(self, text):
        """Create simple word frequency vector"""
        words = self.preprocess_text(text).split()
        word_count = Counter(words)
        return word_count
    
    def calculate_similarity(self, text1, text2):
        """Calculate Jaccard similarity"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(self.preprocess_text(text1).split())
        words2 = set(self.preprocess_text(text2).split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def find_keywords(self, text):
        """Extract important keywords"""
        if not text:
            return []
        
        words = self.preprocess_text(text).split()
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'or', 'but', 'in', 'with', 'a', 'an', 'as', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        word_freq = Counter(keywords)
        return [word for word, count in word_freq.most_common(10)]

# ==============================================================================
# DATABASE MANAGER (Keep existing implementation)
# ==============================================================================

class DatabaseManager:
    def __init__(self, mongo_uri, db_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.news_collection = self.db.news_articles
        self.companies_collection = self.db.msme_companies
        self.financial_collection = self.db.msme_financial
    
    def ping(self):
        """Ping MongoDB to verify connection."""
        try:
            self.client.admin.command('ping')
            return True, None
        except Exception as exc:
            return False, str(exc)
        
    def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            self.news_collection.create_index([
                ("title", "text"),
                ("description", "text"),
                ("content", "text")
            ])
        except:
            pass
        
        try:
            self.companies_collection.create_index("Company_Name")
        except:
            pass
        
    def insert_news_article(self, article_data, keywords):
        """Insert news article with keywords (avoid duplicates)"""
        existing_article = self.news_collection.find_one({
            "$or": [
                {"title": article_data.get("title")},
                {"link": article_data.get("link")}
            ]
        })
        
        if existing_article:
            return None
        
        document = {
            "article_id": article_data.get("article_id"),
            "title": article_data.get("title"),
            "description": article_data.get("description", ""),
            "content": article_data.get("content", ""),
            "link": article_data.get("link"),
            "source_id": article_data.get("source_id"),
            "source_name": article_data.get("source_name", ""),
            "pubDate": article_data.get("pubDate"),
            "image_url": article_data.get("image_url"),
            "category": article_data.get("category", []),
            "country": article_data.get("country", []),
            "keywords": keywords,
            "indexed_at": datetime.utcnow()
        }
        return self.news_collection.insert_one(document)
    
    def load_msme_data(self, companies_df, financial_df):
        """Load MSME company and financial data (legacy method)"""
        self.companies_collection.delete_many({})
        self.financial_collection.delete_many({})
        
        companies_records = companies_df.to_dict('records')
        for record in companies_records:
            company_text = f"{record.get('Company_Name', '')} {record.get('Sector', '')} {record.get('Primary_Products', '')} {record.get('Location', '')}"
            similarity_service = SimpleTextSimilarity()
            keywords = similarity_service.find_keywords(company_text)
            record['keywords'] = keywords
            
        self.companies_collection.insert_many(companies_records)
        
        financial_records = financial_df.to_dict('records')
        self.financial_collection.insert_many(financial_records)

    def load_merged_msme_data(self, merged_df):
        """Load merged MSME data from all three CSV files"""
        # Clear existing data
        self.companies_collection.delete_many({})
        self.financial_collection.delete_many({})
        
        # Convert DataFrame to records
        companies_records = merged_df.to_dict('records')
        
        # Add keywords to each company record
        similarity_service = SimpleTextSimilarity()
        for record in companies_records:
            company_text = f"{record.get('Company_Name', '')} {record.get('Sector', '')} {record.get('Primary_Products', '')} {record.get('Location', '')}"
            keywords = similarity_service.find_keywords(company_text)
            record['keywords'] = keywords
            
            # Clean up NaN values and convert to appropriate types
            for key, value in record.items():
                if value is None:
                    record[key] = None
                elif isinstance(value, (int, float)) and (value != value):  # Check for NaN
                    record[key] = None
                elif isinstance(value, str) and value.lower() in ['nan', 'null', '']:
                    record[key] = None
        
        # Insert merged records
        self.companies_collection.insert_many(companies_records)
        
        # Also store financial data separately for compatibility
        financial_records = []
        for record in companies_records:
            if record.get('Total_Revenue') is not None:
                financial_records.append({
                    'Company_Name': record.get('Company_Name'),
                    'Total_Revenue': record.get('Total_Revenue'),
                    'Gross_Profit_Margin': record.get('Gross_Profit_Margin'),
                    'Net_Profit_Margin': record.get('Net_Profit_Margin'),
                    'Debt_to_Equity': record.get('Debt_to_Equity'),
                    'Operating_Profit': record.get('Operating_Profit'),
                    'Sales_Growth': record.get('Sales_Growth')
                })
        
        if financial_records:
            self.financial_collection.insert_many(financial_records)

# ==============================================================================
# NEWS SERVICE (Keep existing implementation)
# ==============================================================================

class NewsService:
    def __init__(self, api_key, db_manager, similarity_service):
        self.api_key = api_key
        self.base_url = Config.NEWS_BASE_URL
        self.db_manager = db_manager
        self.similarity_service = similarity_service
        
    def fetch_latest_news(self, query=None, country="in", category=None, language="en"):
        """Fetch latest news from NewsData.io API"""
        endpoint = f"{self.base_url}/latest"
        
        params = {
            "apikey": self.api_key,
            "language": language,
            "country": country,
            "size": 10
        }
        
        if query:
            params["q"] = query
        if category:
            params["category"] = category
            
        try:
            if not self.api_key or self.api_key.strip() == "":
                return {"success": False, "error": "NEWS_API_KEY missing. Set it via env var NEWS_API_KEY or Config."}
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                articles = data.get("results", [])
                stored_count = 0
                
                for article in articles:
                    if article.get("title") and article.get("description"):
                        content_text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
                        keywords = self.similarity_service.find_keywords(content_text)
                        
                        result = self.db_manager.insert_news_article(article, keywords)
                        if result:
                            stored_count += 1
                        
                return {"success": True, "articles_stored": stored_count}
            else:
                return {"success": False, "error": data.get("message", "Unknown error"), "details": data}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "News API request timed out"}
        except requests.exceptions.HTTPError as http_err:
            try:
                err_json = response.json()
            except Exception:
                err_json = None
            return {"success": False, "error": f"News API HTTP error: {http_err}", "details": err_json}
        except Exception as e:
            return {"success": False, "error": str(e)}

# ==============================================================================
# FLASK APPLICATION
# ==============================================================================

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Global service instances
db_manager = DatabaseManager(Config.MONGO_URI, Config.DB_NAME)
similarity_service = SimpleTextSimilarity()
news_service = NewsService(Config.NEWS_API_KEY, db_manager, similarity_service)

# Initialize PraisonAI manager
praison_manager = PraisonAIManager()
praison_manager.initialize_agents()

# Initialize enhanced services
enhanced_rag_service = EnhancedRAGService(db_manager, similarity_service, praison_manager)
enhanced_dashboard_service = EnhancedDashboardService(db_manager, praison_manager)

# Initialize database
db_manager.create_indexes()

# ==============================================================================
# ENHANCED ROUTES
# ==============================================================================

@app.route('/')
def index():
    index_path = Config.BASE_DIR / 'index.html'
    if index_path.exists():
        return send_from_directory(str(Config.BASE_DIR), 'index.html')
    return jsonify({
        "message": "MSME News Aggregator with PraisonAI Integration",
        "status": "Enhanced with AI Agents",
        "praison_available": PRAISON_AVAILABLE,
        "endpoints": {
            "fetch_news": "/api/fetch-news",
            "chat": "/api/chat",
            "dashboard": "/api/dashboard",
            "companies": "/api/companies",
            "load_data": "/api/load-data",
            "health": "/api/health",
            "praison_status": "/api/praison-status"
        }
    })

@app.route('/news')
def news_page():
    """Serve the news articles page"""
    news_path = Config.BASE_DIR / 'news.html'
    if news_path.exists():
        return send_from_directory(str(Config.BASE_DIR), 'news.html')
    return jsonify({
        "error": "News page not found",
        "message": "news.html file not found in project directory"
    }), 404

@app.route('/api/praison-status', methods=['GET'])
def praison_status():
    """Check PraisonAI integration status"""
    return jsonify({
        "praison_available": PRAISON_AVAILABLE,
        "agents_initialized": praison_manager.initialized,
        "openai_key_configured": bool(Config.OPENAI_API_KEY),
        "agents": list(praison_manager.agents.keys()) if praison_manager.initialized else []
    })

@app.route('/api/chat', methods=['POST'])
def enhanced_chat():
    """Enhanced RAG-powered chatbot with PraisonAI integration and structured outputs"""
    data = request.json
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Initialize structured response
        structured_response = {
            "financial_reports": {},
            "news_analysis": {},
            "growth_recommendations": {},
            "summary": {
                "query": user_query,
                "timestamp": datetime.now().isoformat(),
                "agents_used": [],
                "confidence_score": 0
            }
        }
        
        # Determine query intent and route to appropriate agents
        query_lower = user_query.lower()
        
        # Financial analysis queries
        financial_keywords = ['financial', 'revenue', 'profit', 'performance', 'ratios', 'roa', 'roe', 'debt', 'equity', 'stock', 'market cap']
        is_financial_query = any(keyword in query_lower for keyword in financial_keywords)
        
        # News analysis queries
        news_keywords = ['news', 'latest', 'recent', 'update', 'trend', 'market', 'policy', 'government', 'industry']
        is_news_query = any(keyword in query_lower for keyword in news_keywords)
        
        # Growth strategy queries
        growth_keywords = ['growth', 'strategy', 'expansion', 'opportunity', 'development', 'plan', 'recommendation']
        is_growth_query = any(keyword in query_lower for keyword in growth_keywords)
        
        # Execute agent workflows based on query intent
        if is_financial_query:
            # Use Financial Analyst agent
            try:
                # Get company data for financial analysis
                company_results = enhanced_rag_service.enhanced_find_related_companies(user_query, limit=5)
                
                if company_results.get('companies'):
                    company = company_results['companies'][0]  # Use first company
                    
                    # Get financial ratios
                    ratios = enhanced_rag_service.financial_tools.get_financial_ratios(company)
                    
                    # Get stock data if available
                    stock_data = enhanced_rag_service.financial_tools.get_stock_data(company.get('Company_Name', ''))
                    
                    # Process financial data
                    financial_data = {
                        "company": company.get('Company_Name', ''),
                        "ratios": ratios,
                        "stock_data": stock_data,
                        "export_markets": company.get('Export_Markets', '')
                    }
                    
                    structured_response["financial_reports"] = enhanced_rag_service.data_processor.process_financial_data(financial_data)
                    
                    # Add company analysis to structured response
                    if company_results.get('companies'):
                        # Convert ObjectId to string for JSON serialization
                        companies_data = []
                        for company in company_results['companies']:
                            company_dict = dict(company)
                            if '_id' in company_dict:
                                company_dict['_id'] = str(company_dict['_id'])
                            companies_data.append(company_dict)
                        
                        structured_response["company_analysis"] = {
                            "companies": companies_data,
                            "total_found": len(companies_data),
                            "query": user_query
                        }
                    
                    structured_response["summary"]["agents_used"].append("financial_analyst")
                    
            except Exception as e:
                print(f"Financial analysis error: {e}")
        
        if is_news_query:
            # Use News Analyst agent
            try:
                # Enhanced news search
                news_results = enhanced_rag_service.enhanced_semantic_search_news(user_query, limit=10)
                
                # Auto-fetch more news if needed
                if len(news_results.get('articles', [])) < 3:
                    fetch_result = news_service.fetch_latest_news(query=user_query, country="in")
                    if fetch_result.get("success"):
                        news_results = enhanced_rag_service.enhanced_semantic_search_news(user_query, limit=10)
                
                # Process news data
                structured_response["news_analysis"] = enhanced_rag_service.data_processor.process_news_data(news_results)
                structured_response["summary"]["agents_used"].append("news_analyst")
                
            except Exception as e:
                print(f"News analysis error: {e}")
        
        if is_growth_query:
            # Use Growth Strategist agent
            try:
                # Extract sector and location from query
                locations = enhanced_rag_service._extract_locations(user_query)
                sectors = enhanced_rag_service._extract_sectors(user_query)
                
                sector = sectors[0] if sectors else "general"
                location = locations[0] if locations else None
                
                # Get market trends
                market_trends = enhanced_rag_service.search_tools.search_market_trends(sector, location)
                
                # Get company data for growth analysis
                company_results = enhanced_rag_service.enhanced_find_related_companies(user_query, limit=5)
                
                # Process growth data
                growth_data = {
                    "market_data": market_trends,
                    "company_data": company_results.get('companies', [])[:3] if company_results.get('companies') else []
                }
                
                structured_response["growth_recommendations"] = enhanced_rag_service.data_processor.process_growth_data(
                    growth_data["market_data"], 
                    {"companies": growth_data["company_data"]}
                )
                
                # Add company analysis to structured response
                if company_results.get('companies'):
                    # Convert ObjectId to string for JSON serialization
                    companies_data = []
                    for company in company_results['companies']:
                        company_dict = dict(company)
                        if '_id' in company_dict:
                            company_dict['_id'] = str(company_dict['_id'])
                        companies_data.append(company_dict)
                    
                    structured_response["company_analysis"] = {
                        "companies": companies_data,
                        "total_found": len(companies_data),
                        "query": user_query
                    }
                
                structured_response["summary"]["agents_used"].append("growth_strategist")
                
            except Exception as e:
                print(f"Growth strategy error: {e}")
        
        # Fallback: If no specific intent detected, use basic search
        if not any([is_financial_query, is_news_query, is_growth_query]):
            # Basic news and company search
            news_results = enhanced_rag_service.enhanced_semantic_search_news(user_query, limit=5)
            company_results = enhanced_rag_service.enhanced_find_related_companies(user_query, limit=5)
            
            structured_response["news_analysis"] = enhanced_rag_service.data_processor.process_news_data(news_results)
            
            # Add company analysis to structured response
            if company_results.get('companies'):
                # Convert ObjectId to string for JSON serialization
                companies_data = []
                for company in company_results['companies']:
                    company_dict = dict(company)
                    if '_id' in company_dict:
                        company_dict['_id'] = str(company_dict['_id'])
                    companies_data.append(company_dict)
                
                structured_response["company_analysis"] = {
                    "companies": companies_data,
                    "total_found": len(companies_data),
                    "query": user_query
                }
            
            structured_response["summary"]["agents_used"].append("basic_search")
        
        # Generate enhanced dashboard data
        news_dashboard = enhanced_dashboard_service.generate_intelligent_dashboard({
            'news': structured_response.get("news_analysis", {}),
            'companies': company_results.get('analysis', {}) if 'company_results' in locals() else {}
        }, user_query)
        
        # Calculate confidence score
        confidence_score = min(100, len(structured_response["summary"]["agents_used"]) * 25)
        structured_response["summary"]["confidence_score"] = confidence_score
        
        # Generate response text
        response_text = enhanced_rag_service.generate_enhanced_response(user_query, news_results if 'news_results' in locals() else {}, company_results if 'company_results' in locals() else {})
        
        # Enhanced logging for debugging
        print(f"\n=== CHAT DEBUG INFO ===")
        print(f"Query: {user_query}")
        print(f"Intent Detection:")
        print(f"  - Financial Query: {is_financial_query}")
        print(f"  - News Query: {is_news_query}")
        print(f"  - Growth Query: {is_growth_query}")
        print(f"Agents Used: {structured_response['summary']['agents_used']}")
        print(f"Confidence Score: {structured_response['summary']['confidence_score']}")
        print(f"Structured Data Keys: {list(structured_response.keys())}")
        print(f"=======================\n")
        
        return jsonify({
            "response": response_text,
            "structured_data": structured_response,
            "dashboard_data": news_dashboard,
            "enhanced": True,
            "agents_used": structured_response["summary"]["agents_used"],
            "debug_info": {
                "intent_detection": {
                    "financial": is_financial_query,
                    "news": is_news_query,
                    "growth": is_growth_query
                },
                "confidence_score": structured_response["summary"]["confidence_score"],
                "timestamp": structured_response["summary"]["timestamp"]
            }
        })
        
    except Exception as e:
        print(f"Enhanced chat error: {e}")
        return jsonify({"error": f"Enhanced chat error: {str(e)}"}), 500

@app.route('/api/tools-status', methods=['GET'])
def tools_status():
    """Check status of all integrated tools/APIs"""
    try:
        status = {
            "praisonai": {
                "available": PRAISON_AVAILABLE,
                "initialized": praison_manager.initialized if praison_manager else False,
                "agents": list(praison_manager.agents.keys()) if praison_manager and praison_manager.initialized else []
            },
            "financial_tools": {
                "yfinance": False,
                "alpha_vantage": bool(os.getenv("ALPHA_VANTAGE_API_KEY", "")),
                "status": "Checking..."
            },
            "search_tools": {
                "news_api": bool(os.getenv("NEWS_API_KEY", "")),
                "duckduckgo": False,
                "status": "Checking..."
            },
            "data_processing": {
                "available": True,
                "status": "Ready"
            }
        }
        
        # Test YFinance
        try:
            import yfinance as yf
            status["financial_tools"]["yfinance"] = True
        except ImportError:
            status["financial_tools"]["yfinance"] = False
        
        # Test DuckDuckGo
        try:
            from duckduckgo_search import DDGS
            status["search_tools"]["duckduckgo"] = True
        except ImportError:
            status["search_tools"]["duckduckgo"] = False
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": f"Error checking tools status: {str(e)}"}), 500

@app.route('/api/debug/company-search', methods=['POST'])
def debug_company_search():
    """Debug company search with detailed breakdown"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        debug_info = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        # Step 1: Extract locations and sectors
        locations = enhanced_rag_service._extract_locations(query)
        sectors = enhanced_rag_service._extract_sectors(query)
        
        debug_info["steps"].append({
            "step": 1,
            "action": "Extract keywords",
            "locations_found": locations,
            "sectors_found": sectors,
            "query_keywords": list(enhanced_rag_service.similarity_service.find_keywords(query))
        })
        
        # Step 2: Get all companies
        all_companies = list(enhanced_rag_service.db_manager.companies_collection.find())
        debug_info["steps"].append({
            "step": 2,
            "action": "Load companies from DB",
            "total_companies": len(all_companies),
            "sample_companies": [
                {
                    "name": c.get("Company_Name", ""),
                    "location": c.get("Location", ""),
                    "sector": c.get("Sector", "")
                } for c in all_companies[:3]
            ]
        })
        
        # Step 3: Pre-filtering
        pre_filtered = all_companies.copy()
        if locations:
            pre_filtered = [c for c in pre_filtered if any(loc.lower() in c.get('Location', '').lower() for loc in locations)]
        
        if sectors:
            pre_filtered = [c for c in pre_filtered if any(sect.lower() in c.get('Sector', '').lower() for sect in sectors)]
        
        debug_info["steps"].append({
            "step": 3,
            "action": "Pre-filtering",
            "after_location_filter": len([c for c in all_companies if any(loc.lower() in c.get('Location', '').lower() for loc in locations)]) if locations else "N/A",
            "after_sector_filter": len([c for c in all_companies if any(sect.lower() in c.get('Sector', '').lower() for sect in sectors)]) if sectors else "N/A",
            "final_pre_filtered": len(pre_filtered)
        })
        
        # Step 4: Similarity calculations
        similarity_details = []
        for company in pre_filtered[:5]:  # Show details for first 5
            company_keywords = set(company.get("keywords", []))
            query_keywords = set(enhanced_rag_service.similarity_service.find_keywords(query))
            
            # Calculate similarities
            keyword_similarity = 0
            if query_keywords and company_keywords:
                keyword_similarity = len(query_keywords.intersection(company_keywords)) / len(query_keywords.union(company_keywords))
            
            company_text = f"{company.get('Company_Name', '')} {company.get('Sector', '')} {company.get('Primary_Products', '')}"
            text_similarity = enhanced_rag_service.similarity_service.calculate_similarity(query, company_text)
            
            # Bonuses
            location_bonus = 0.2 if locations and any(loc.lower() in company.get('Location', '').lower() for loc in locations) else 0
            sector_bonus = 0.15 if sectors and any(sect.lower() in company.get('Sector', '').lower() for sect in sectors) else 0
            
            max_similarity = max(keyword_similarity, text_similarity)
            final_similarity = min(1.0, max_similarity + location_bonus + sector_bonus)
            
            similarity_details.append({
                "company": company.get("Company_Name", ""),
                "keyword_similarity": round(keyword_similarity, 3),
                "text_similarity": round(text_similarity, 3),
                "location_bonus": location_bonus,
                "sector_bonus": sector_bonus,
                "final_similarity": round(final_similarity, 3),
                "passes_threshold": final_similarity > 0.05
            })
        
        debug_info["steps"].append({
            "step": 4,
            "action": "Similarity calculations",
            "threshold": 0.05,
            "similarity_details": similarity_details
        })
        
        # Step 5: Final results
        final_results = enhanced_rag_service.enhanced_find_related_companies(query, limit=10)
        debug_info["steps"].append({
            "step": 5,
            "action": "Final results",
            "results_count": len(final_results.get('companies', [])),
            "results": [
                {
                    "name": c.get("Company_Name", ""),
                    "similarity": round(c.get("similarity", 0), 3),
                    "location": c.get("Location", ""),
                    "sector": c.get("Sector", "")
                } for c in final_results.get('companies', [])[:5]
            ]
        })
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": f"Debug error: {str(e)}"}), 500

@app.route('/api/debug/database', methods=['GET'])
def debug_database():
    """Debug database state and collections"""
    try:
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "collections": {}
        }
        
        # Check MongoDB connection
        ok, err = enhanced_rag_service.db_manager.ping()
        debug_info["connection"] = {
            "status": "OK" if ok else "ERROR",
            "error": err if err else None
        }
        
        # Check each collection
        collections = ['news', 'companies']
        for collection_name in collections:
            try:
                if collection_name == 'news':
                    collection = enhanced_rag_service.db_manager.news_collection
                else:
                    collection = enhanced_rag_service.db_manager.companies_collection
                
                count = collection.count_documents({})
                sample_docs = list(collection.find().limit(3))
                
                debug_info["collections"][collection_name] = {
                    "count": count,
                    "sample_documents": [
                        {
                            "keys": list(doc.keys()),
                            "sample_data": {k: str(v)[:100] + "..." if len(str(v)) > 100 else v 
                                          for k, v in doc.items() if k in ['title', 'Company_Name', 'Location', 'Sector', 'description']}
                        } for doc in sample_docs
                    ]
                }
                
            except Exception as e:
                debug_info["collections"][collection_name] = {
                    "error": str(e)
                }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": f"Database debug error: {str(e)}"}), 500

@app.route('/api/debug/agents', methods=['POST'])
def debug_agents():
    """Debug agent routing and execution"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        debug_info = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "agent_analysis": {}
        }
        
        query_lower = query.lower()
        
        # Analyze query intent
        financial_keywords = ['financial', 'revenue', 'profit', 'performance', 'ratios', 'roa', 'roe', 'debt', 'equity', 'stock', 'market cap']
        news_keywords = ['news', 'latest', 'recent', 'update', 'trend', 'market', 'policy', 'government', 'industry']
        growth_keywords = ['growth', 'strategy', 'expansion', 'opportunity', 'development', 'plan', 'recommendation']
        
        debug_info["agent_analysis"]["intent_detection"] = {
            "financial_keywords_found": [kw for kw in financial_keywords if kw in query_lower],
            "news_keywords_found": [kw for kw in news_keywords if kw in query_lower],
            "growth_keywords_found": [kw for kw in growth_keywords if kw in query_lower],
            "is_financial_query": any(kw in query_lower for kw in financial_keywords),
            "is_news_query": any(kw in query_lower for kw in news_keywords),
            "is_growth_query": any(kw in query_lower for kw in growth_keywords)
        }
        
        # Check PraisonAI status
        debug_info["agent_analysis"]["praisonai_status"] = {
            "available": PRAISON_AVAILABLE,
            "initialized": praison_manager.initialized if praison_manager else False,
            "agents": list(praison_manager.agents.keys()) if praison_manager and praison_manager.initialized else [],
            "openai_key_configured": bool(os.getenv("OPENAI_API_KEY", ""))
        }
        
        # Test agent execution (simulation)
        if praison_manager and praison_manager.initialized:
            debug_info["agent_analysis"]["simulation"] = {
                "would_trigger_financial_analyst": debug_info["agent_analysis"]["intent_detection"]["is_financial_query"],
                "would_trigger_news_analyst": debug_info["agent_analysis"]["intent_detection"]["is_news_query"],
                "would_trigger_growth_strategist": debug_info["agent_analysis"]["intent_detection"]["is_growth_query"],
                "fallback_mode": not any([
                    debug_info["agent_analysis"]["intent_detection"]["is_financial_query"],
                    debug_info["agent_analysis"]["intent_detection"]["is_news_query"],
                    debug_info["agent_analysis"]["intent_detection"]["is_growth_query"]
                ])
            }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": f"Agent debug error: {str(e)}"}), 500

@app.route('/api/debug/test-tools', methods=['GET'])
def debug_test_tools():
    """Test all tools and return detailed results"""
    try:
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "tool_tests": {}
        }
        
        # Test Financial Tools
        try:
            ratios = enhanced_rag_service.financial_tools.get_financial_ratios({
                'Revenue': 1000000,
                'Profit': 100000,
                'Assets': 2000000,
                'Equity': 1500000,
                'Debt': 500000,
                'Overall_Performance_Score': 75,
                'Export_Markets': 'USA,UK,Germany'
            })
            debug_info["tool_tests"]["financial_ratios"] = {
                "status": "SUCCESS",
                "result": ratios
            }
        except Exception as e:
            debug_info["tool_tests"]["financial_ratios"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        # Test Stock Data
        try:
            stock_data = enhanced_rag_service.financial_tools.get_stock_data("Reliance")
            debug_info["tool_tests"]["stock_data"] = {
                "status": "SUCCESS",
                "result": stock_data
            }
        except Exception as e:
            debug_info["tool_tests"]["stock_data"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        # Test News Search
        try:
            news_results = enhanced_rag_service.search_tools.search_news("MSME", {"category": "business"})
            debug_info["tool_tests"]["news_search"] = {
                "status": "SUCCESS",
                "result": {
                    "success": news_results.get("success", False),
                    "total_results": news_results.get("total_results", 0),
                    "sample_articles": len(news_results.get("articles", []))
                }
            }
        except Exception as e:
            debug_info["tool_tests"]["news_search"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        # Test Web Search
        try:
            web_results = enhanced_rag_service.search_tools.search_web("MSME India")
            debug_info["tool_tests"]["web_search"] = {
                "status": "SUCCESS",
                "result": {
                    "success": web_results.get("success", False),
                    "total_results": web_results.get("total_results", 0)
                }
            }
        except Exception as e:
            debug_info["tool_tests"]["web_search"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        # Test Data Processing
        try:
            processed = enhanced_rag_service.data_processor.process_financial_data({
                "company": "Test Company",
                "ratios": {"profit_margin": 10, "roa": 5, "roe": 8},
                "stock_data": {"current_price": 100},
                "export_markets": "USA,UK"
            })
            debug_info["tool_tests"]["data_processing"] = {
                "status": "SUCCESS",
                "result": processed
            }
        except Exception as e:
            debug_info["tool_tests"]["data_processing"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": f"Tool test error: {str(e)}"}), 500

@app.route('/api/debug/query-breakdown', methods=['POST'])
def debug_query_breakdown():
    """Complete query breakdown with all processing steps"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        debug_info = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "processing_steps": []
        }
        
        # Step 1: Query Analysis
        query_lower = query.lower()
        locations = enhanced_rag_service._extract_locations(query)
        sectors = enhanced_rag_service._extract_sectors(query)
        keywords = enhanced_rag_service.similarity_service.find_keywords(query)
        
        debug_info["processing_steps"].append({
            "step": 1,
            "name": "Query Analysis",
            "details": {
                "original_query": query,
                "lowercase_query": query_lower,
                "extracted_locations": locations,
                "extracted_sectors": sectors,
                "extracted_keywords": keywords,
                "query_length": len(query),
                "word_count": len(query.split())
            }
        })
        
        # Step 2: Intent Detection
        financial_keywords = ['financial', 'revenue', 'profit', 'performance', 'ratios', 'roa', 'roe', 'debt', 'equity', 'stock', 'market cap']
        news_keywords = ['news', 'latest', 'recent', 'update', 'trend', 'market', 'policy', 'government', 'industry']
        growth_keywords = ['growth', 'strategy', 'expansion', 'opportunity', 'development', 'plan', 'recommendation']
        
        intent_scores = {
            "financial": len([kw for kw in financial_keywords if kw in query_lower]),
            "news": len([kw for kw in news_keywords if kw in query_lower]),
            "growth": len([kw for kw in growth_keywords if kw in query_lower])
        }
        
        debug_info["processing_steps"].append({
            "step": 2,
            "name": "Intent Detection",
            "details": {
                "intent_scores": intent_scores,
                "primary_intent": max(intent_scores, key=intent_scores.get) if max(intent_scores.values()) > 0 else "general",
                "confidence": max(intent_scores.values()) / len(query.split()) if query.split() else 0
            }
        })
        
        # Step 3: Database Query
        companies_count = enhanced_rag_service.db_manager.companies_collection.count_documents({})
        news_count = enhanced_rag_service.db_manager.news_collection.count_documents({})
        
        debug_info["processing_steps"].append({
            "step": 3,
            "name": "Database State",
            "details": {
                "companies_in_db": companies_count,
                "news_in_db": news_count,
                "db_accessible": companies_count >= 0
            }
        })
        
        # Step 4: Search Execution
        try:
            company_results = enhanced_rag_service.enhanced_find_related_companies(query, limit=5)
            news_results = enhanced_rag_service.enhanced_semantic_search_news(query, limit=5)
            
            debug_info["processing_steps"].append({
                "step": 4,
                "name": "Search Execution",
                "details": {
                    "company_search": {
                        "success": True,
                        "results_count": len(company_results.get('companies', [])),
                        "enhanced": company_results.get('enhanced', False)
                    },
                    "news_search": {
                        "success": True,
                        "results_count": len(news_results.get('articles', [])),
                        "enhanced": news_results.get('enhanced', False)
                    }
                }
            })
        except Exception as e:
            debug_info["processing_steps"].append({
                "step": 4,
                "name": "Search Execution",
                "details": {
                    "error": str(e)
                }
            })
        
        # Step 5: Agent Routing
        if praison_manager and praison_manager.initialized:
            agents_to_use = []
            if intent_scores["financial"] > 0:
                agents_to_use.append("financial_analyst")
            if intent_scores["news"] > 0:
                agents_to_use.append("news_analyst")
            if intent_scores["growth"] > 0:
                agents_to_use.append("growth_strategist")
            
            if not agents_to_use:
                agents_to_use = ["basic_search"]
            
            debug_info["processing_steps"].append({
                "step": 5,
                "name": "Agent Routing",
                "details": {
                    "agents_to_use": agents_to_use,
                    "praisonai_available": True,
                    "fallback_mode": agents_to_use == ["basic_search"]
                }
            })
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": f"Query breakdown error: {str(e)}"}), 500

@app.route('/api/debug/help', methods=['GET'])
def debug_help():
    """Show all available debugging endpoints and their usage"""
    debug_endpoints = {
        "debug_endpoints": {
            "GET /api/debug/help": {
                "description": "Show this help page with all debugging endpoints",
                "parameters": "None",
                "example": "GET http://localhost:8000/api/debug/help"
            },
            "GET /api/debug/database": {
                "description": "Check database state, collections, and sample documents",
                "parameters": "None",
                "example": "GET http://localhost:8000/api/debug/database"
            },
            "GET /api/debug/test-tools": {
                "description": "Test all integrated tools (YFinance, DuckDuckGo, NewsAPI, etc.)",
                "parameters": "None",
                "example": "GET http://localhost:8000/api/debug/test-tools"
            },
            "POST /api/debug/company-search": {
                "description": "Debug company search with step-by-step breakdown",
                "parameters": {"query": "string"},
                "example": "POST http://localhost:8000/api/debug/company-search\n{\"query\": \"manufacturing companies in Tamil Nadu\"}"
            },
            "POST /api/debug/agents": {
                "description": "Debug agent routing and intent detection",
                "parameters": {"query": "string"},
                "example": "POST http://localhost:8000/api/debug/agents\n{\"query\": \"financial performance of companies\"}"
            },
            "POST /api/debug/query-breakdown": {
                "description": "Complete query processing breakdown with all steps",
                "parameters": {"query": "string"},
                "example": "POST http://localhost:8000/api/debug/query-breakdown\n{\"query\": \"Show me manufacturing companies in Tamil Nadu\"}"
            }
        },
        "status_endpoints": {
            "GET /api/health": "Basic health check (DB connection, collection counts)",
            "GET /api/praison-status": "PraisonAI agents status and configuration",
            "GET /api/tools-status": "All integrated tools status (YFinance, DuckDuckGo, etc.)"
        },
        "testing_guide": {
            "step_1": "First, check if data is loaded: GET /api/debug/database",
            "step_2": "If companies count is 0, click 'Load MSME Data' button in UI",
            "step_3": "Test company search: POST /api/debug/company-search with your query",
            "step_4": "Check agent routing: POST /api/debug/agents with your query",
            "step_5": "Get complete breakdown: POST /api/debug/query-breakdown with your query",
            "step_6": "Test all tools: GET /api/debug/test-tools"
        },
        "common_issues": {
            "no_companies_found": {
                "symptom": "Company search returns 0 results",
                "diagnosis": "Check /api/debug/database - companies count should be > 0",
                "solution": "Click 'Load MSME Data' button in UI"
            },
            "agents_not_triggering": {
                "symptom": "Only basic_search agent used",
                "diagnosis": "Check /api/praison-status - should show initialized: true",
                "solution": "Verify OPENAI_API_KEY in .env file"
            },
            "tools_not_working": {
                "symptom": "YFinance/DuckDuckGo errors",
                "diagnosis": "Check /api/debug/test-tools for specific tool failures",
                "solution": "Install missing packages: pip install yfinance duckduckgo-search"
            }
        },
        "curl_examples": {
            "check_database": "curl -X GET http://localhost:8000/api/debug/database",
            "test_company_search": "curl -X POST http://localhost:8000/api/debug/company-search -H 'Content-Type: application/json' -d '{\"query\": \"manufacturing companies in Tamil Nadu\"}'",
            "test_agents": "curl -X POST http://localhost:8000/api/debug/agents -H 'Content-Type: application/json' -d '{\"query\": \"financial performance\"}'",
            "test_tools": "curl -X GET http://localhost:8000/api/debug/test-tools"
        }
    }
    
    return jsonify(debug_endpoints)

# Keep existing routes for compatibility
@app.route('/api/health', methods=['GET'])
def health():
    """Health check: DB connectivity and collection counts."""
    ok, err = db_manager.ping()
    status = {
        "mongo_connected": ok,
        "error": err,
        "db_name": Config.DB_NAME,
        "praison_available": PRAISON_AVAILABLE,
        "praison_initialized": praison_manager.initialized
    }
    if ok:
        try:
            status["counts"] = {
                "news_articles": db_manager.news_collection.count_documents({}),
                "msme_companies": db_manager.companies_collection.count_documents({}),
                "msme_financial": db_manager.financial_collection.count_documents({})
            }
        except Exception as exc:
            status["counts_error"] = str(exc)
    http_code = 200 if ok else 503
    return jsonify(status), http_code

@app.route('/api/fetch-news', methods=['POST'])
def fetch_news():
    """Fetch and store news articles"""
    data = request.json or {}
    query = data.get('query', 'MSME business manufacturing')
    category = data.get('category')
    country = data.get('country', 'in')
    
    result = news_service.fetch_latest_news(query=query, category=category, country=country)
    return jsonify(result)

@app.route('/api/dashboard', methods=['POST'])
def generate_dashboard():
    """Generate enhanced dashboard charts with PraisonAI insights"""
    data = request.json
    dashboard_data = data.get('dashboard_data', {})
    user_query = data.get('user_query', 'General Analysis')
    
    # Generate intelligent dashboard
    enhanced_dashboard = enhanced_dashboard_service.generate_intelligent_dashboard(dashboard_data, user_query)
    
    return jsonify(enhanced_dashboard['charts'])

@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Get all MSME companies"""
    companies = list(db_manager.companies_collection.find({}, {"keywords": 0}))
    return jsonify([{**company, "_id": str(company["_id"])} for company in companies])

@app.route('/api/latest-news', methods=['GET'])
def get_latest_news():
    """Get latest news articles from database"""
    try:
        pipeline = [
            {"$sort": {"pubDate": -1}},
            {"$group": {
                "_id": "$title",
                "article": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$article"}},
            {"$limit": 10}
        ]
        
        articles = list(db_manager.news_collection.aggregate(pipeline))
        
        formatted_articles = []
        for article in articles:
            formatted_articles.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "link": article.get("link"),
                "source": article.get("source_name"),
                "pubDate": article.get("pubDate"),
                "similarity": 1.0
            })
        
        return jsonify({
            "success": True,
            "articles": formatted_articles
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/clear-duplicates', methods=['POST'])
def clear_duplicates():
    """Clear duplicate news articles from database"""
    try:
        pipeline = [
            {"$sort": {"pubDate": -1}},
            {"$group": {
                "_id": "$title",
                "duplicates": {"$push": "$_id"},
                "keep": {"$first": "$_id"}
            }},
            {"$match": {"duplicates.1": {"$exists": True}}},
            {"$project": {
                "duplicates": {
                    "$slice": ["$duplicates", 1, {"$size": "$duplicates"}]
                }
            }},
            {"$unwind": "$duplicates"}
        ]
        
        duplicates_to_remove = list(db_manager.news_collection.aggregate(pipeline))
        duplicate_ids = [doc["duplicates"] for doc in duplicates_to_remove]
        
        if duplicate_ids:
            result = db_manager.news_collection.delete_many({"_id": {"$in": duplicate_ids}})
            return jsonify({
                "success": True,
                "message": f"Removed {result.deleted_count} duplicate articles"
            })
        else:
            return jsonify({
                "success": True,
                "message": "No duplicates found"
            })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """Load MSME data from all three CSV files with enhanced debugging and merging"""
    try:
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "steps": [],
            "files_found": {},
            "data_loaded": {},
            "merge_info": {}
        }
        
        # Define paths for all four CSV files
        companies_path = Config.BASE_DIR / 'DataSet - SupplierMSMES.csv'
        performance_path = Config.BASE_DIR / 'MSME_32hai.csv'
        financial_path = Config.BASE_DIR / 'DataSet - SupplierFinancials (1).csv'
        additional_financial_path = Config.BASE_DIR / 'financial_msme.csv'
        
        # Step 1: Check file existence
        companies_exists = companies_path.exists()
        performance_exists = performance_path.exists()
        financial_exists = financial_path.exists()
        additional_financial_exists = additional_financial_path.exists()
        
        debug_info["files_found"] = {
            "companies_csv": {
                "path": str(companies_path),
                "exists": companies_exists
            },
            "performance_csv": {
                "path": str(performance_path),
                "exists": performance_exists
            },
            "financial_csv": {
                "path": str(financial_path),
                "exists": financial_exists
            },
            "additional_financial_csv": {
                "path": str(additional_financial_path),
                "exists": additional_financial_exists
            }
        }
        
        debug_info["steps"].append({
            "step": "Check CSV files",
            "companies_found": companies_exists,
            "performance_found": performance_exists,
            "financial_found": financial_exists,
            "additional_financial_found": additional_financial_exists,
            "status": "SUCCESS" if all([companies_exists, performance_exists, financial_exists, additional_financial_exists]) else "PARTIAL"
        })
        
        if not companies_exists:
            return jsonify({
                "success": False,
                "error": "Companies CSV not found",
                "expected_path": str(companies_path),
                "debug_info": debug_info
            }), 400
            
        if not performance_exists:
            return jsonify({
                "success": False,
                "error": "Performance CSV not found", 
                "expected_path": str(performance_path),
                "debug_info": debug_info
            }), 400
            
        if not additional_financial_exists:
            return jsonify({
                "success": False,
                "error": "Additional Financial CSV not found", 
                "expected_path": str(additional_financial_path),
                "debug_info": debug_info
            }), 400
        
        # Step 2: Load CSV files
        companies_df = pd.read_csv(companies_path)
        performance_df = pd.read_csv(performance_path)
        financial_df = pd.read_csv(financial_path)
        additional_financial_df = pd.read_csv(additional_financial_path)
        
        debug_info["steps"].append({
            "step": "Load CSV files",
            "companies_rows": len(companies_df),
            "performance_rows": len(performance_df),
            "financial_rows": len(financial_df),
            "additional_financial_rows": len(additional_financial_df),
            "companies_columns": list(companies_df.columns),
            "performance_columns": list(performance_df.columns),
            "financial_columns": list(financial_df.columns),
            "additional_financial_columns": list(additional_financial_df.columns),
            "status": "SUCCESS"
        })
        
        # Step 3: Merge datasets
        # First merge companies with performance data
        merged_df = pd.merge(
            companies_df, 
            performance_df, 
            on='Company_Name', 
            how='left',
            suffixes=('', '_perf')
        )
        
        # Then merge with financial data
        merged_df = pd.merge(
            merged_df,
            financial_df,
            left_on='Company_Name',
            right_on='Company_name',
            how='left',
            suffixes=('', '_fin')
        )
        
        # Finally merge with additional financial data
        # Try different column names for company identification
        additional_financial_merge_key = None
        for col in additional_financial_df.columns:
            if 'company' in col.lower() or 'name' in col.lower():
                additional_financial_merge_key = col
                break
        
        if additional_financial_merge_key:
            merged_df = pd.merge(
                merged_df,
                additional_financial_df,
                left_on='Company_Name',
                right_on=additional_financial_merge_key,
                how='left',
                suffixes=('', '_additional')
            )
        
        # Clean up duplicate columns and standardize names
        if 'Company_name' in merged_df.columns:
            merged_df = merged_df.drop('Company_name', axis=1)
        
        # Standardize column names for financial data
        column_mapping = {
            'Total revenue (in Cr)': 'Total_Revenue',
            'Gross profit margin': 'Gross_Profit_Margin',
            'Net profit margin': 'Net_Profit_Margin',
            'Operating profit (in Cr)': 'Operating_Profit',
            'Sales growth': 'Sales_Growth',
            'Debt-to-equity ratio': 'Debt_to_Equity',
            'Total revenue(in Cr)': 'Total_Revenue',
            'net profit margin': 'Net_Profit_Margin',
            'operating profit (in Cr)': 'Operating_Profit',
            'sales growth': 'Sales_Growth',
            'Debt-to-equity ratio_additional': 'Debt_to_Equity'
        }
        
        # Rename columns
        merged_df = merged_df.rename(columns=column_mapping)
        
        # Handle duplicate columns by keeping the first occurrence and cleaning up suffixes
        cols_to_drop = []
        for col in merged_df.columns:
            if col.endswith('_additional') or col.endswith('_perf') or col.endswith('_fin'):
                cols_to_drop.append(col)
            elif col.endswith('_x') or col.endswith('_y'):
                # Keep the column without suffix if it exists, otherwise keep the suffixed one
                base_col = col.rsplit('_', 1)[0]
                if base_col in merged_df.columns and base_col != col:
                    cols_to_drop.append(col)
        
        merged_df = merged_df.drop(columns=cols_to_drop)
        
        # Clean up remaining suffix columns
        merged_df.columns = [col.replace('_x', '').replace('_y', '') for col in merged_df.columns]
        
        # Debug: Print the final merged dataframe structure
        print(f"Final merged dataframe shape: {merged_df.shape}")
        print(f"Final columns: {list(merged_df.columns)}")
        print(f"Sample data:")
        print(merged_df.head(2).to_dict('records'))
        
        debug_info["merge_info"] = {
            "companies_rows": len(companies_df),
            "performance_rows": len(performance_df),
            "financial_rows": len(financial_df),
            "additional_financial_rows": len(additional_financial_df),
            "merged_rows": len(merged_df),
            "merge_success": len(merged_df) > 0,
            "additional_financial_merge_key": additional_financial_merge_key
        }
        
        debug_info["steps"].append({
            "step": "Merge datasets",
            "final_columns": list(merged_df.columns),
            "merged_rows": len(merged_df),
            "status": "SUCCESS"
        })
        
        # Step 4: Load merged data into database
        db_manager.load_merged_msme_data(merged_df)
        
        # Step 5: Verify data was loaded
        final_count = db_manager.companies_collection.count_documents({})
        
        debug_info["data_loaded"] = {
            "companies_loaded": len(companies_df),
            "performance_loaded": len(performance_df),
            "financial_loaded": len(financial_df),
            "additional_financial_loaded": len(additional_financial_df),
            "merged_loaded": len(merged_df),
            "total_in_db": final_count
        }
        
        debug_info["steps"].append({
            "step": "Verify database",
            "total_documents": final_count,
            "status": "SUCCESS"
        })
        
        return jsonify({
            "success": True,
            "message": f"Loaded and merged {len(merged_df)} companies from 4 datasets. Total in DB: {final_count}",
            "debug_info": debug_info
        })
        
    except Exception as e:
        debug_info["steps"].append({
            "step": "Error occurred",
            "status": "ERROR",
            "error": str(e)
        })
        
        return jsonify({
            "success": False,
            "error": str(e),
            "debug_info": debug_info
        }), 500

# ==============================================================================
# DASHBOARD API ENDPOINTS
# ==============================================================================

@app.route('/api/dashboard/companies', methods=['GET'])
def get_dashboard_companies():
    """Get filtered companies for dashboard"""
    try:
        # Get query parameters
        location = request.args.get('location', '')
        sector = request.args.get('sector', '')
        export_market = request.args.get('export', '')
        search = request.args.get('search', '')
        min_score = int(request.args.get('min_score', 0))
        
        # Build filter query
        filter_query = {}
        
        if location:
            filter_query['Location'] = {'$regex': location, '$options': 'i'}
        if sector:
            filter_query['Sector'] = {'$regex': sector, '$options': 'i'}
        if export_market:
            filter_query['Export_Markets'] = {'$regex': export_market, '$options': 'i'}
        if search:
            filter_query['$or'] = [
                {'Company_Name': {'$regex': search, '$options': 'i'}},
                {'Sector': {'$regex': search, '$options': 'i'}},
                {'Primary_Products': {'$regex': search, '$options': 'i'}}
            ]
        
        # Get companies from database
        companies = list(db_manager.companies_collection.find(filter_query))
        
        # Filter by performance score
        if min_score > 0:
            score_map = {'Strong': 80, 'Good': 60, 'Medium': 40, 'Developing': 20, 'Weak': 0}
            companies = [c for c in companies if score_map.get(c.get('Overall_Performance_Score', 'Weak'), 0) >= min_score]
        
        # Convert ObjectId to string for JSON serialization
        for company in companies:
            if '_id' in company:
                company['_id'] = str(company['_id'])
        
        return jsonify({
            "success": True,
            "companies": companies,
            "total": len(companies)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dashboard/filters', methods=['GET'])
def get_dashboard_filters():
    """Get available filter options for dashboard"""
    try:
        # Get unique values for filters
        companies = list(db_manager.companies_collection.find({}))
        
        locations = set()
        sectors = set()
        export_markets = set()
        
        for company in companies:
            if company.get('Location'):
                locations.add(company['Location'])
            if company.get('Sector'):
                sectors.add(company['Sector'])
            if company.get('Export_Markets'):
                # Split export markets by comma and clean up
                markets = [m.strip() for m in company['Export_Markets'].split(',') if m.strip()]
                export_markets.update(markets)
        
        return jsonify({
            "success": True,
            "filters": {
                "locations": sorted(list(locations)),
                "sectors": sorted(list(sectors)),
                "export_markets": sorted(list(export_markets))
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dashboard/company-analysis', methods=['POST'])
def analyze_company_dashboard():
    """Analyze a specific company using PraisonAI agents"""
    try:
        data = request.json
        company_name = data.get('company_name')
        
        if not company_name:
            return jsonify({"success": False, "error": "Company name required"}), 400
        
        # Get company data
        company = db_manager.companies_collection.find_one({'Company_Name': company_name})
        if not company:
            return jsonify({"success": False, "error": "Company not found"}), 404
        
        analysis_result = {
            "financial": {},
            "growth": {},
            "news": {}
        }
        
        # Financial Analysis using Financial Analyst agent
        try:
            if praison_manager and praison_manager.initialized:
                financial_agent = praison_manager.agents.get('financial_analyst')
                if financial_agent:
                    financial_prompt = f"""
                    Analyze the financial performance of {company_name}:
                    - Total Revenue: {company.get('Total_Revenue', 'N/A')} Cr
                    - Net Profit Margin: {company.get('Net_Profit_Margin', 'N/A')}
                    - Debt-to-Equity Ratio: {company.get('Debt_to_Equity', 'N/A')}
                    - Sector: {company.get('Sector', 'N/A')}
                    
                    Provide insights on financial health, profitability, and risk assessment.
                    """
                    
                    try:
                        financial_response = financial_agent.run(financial_prompt)
                        # Sanitize response to remove emoji characters and handle encoding
                        if financial_response:
                            # Remove emoji characters and other problematic Unicode
                            import re
                            financial_response = re.sub(r'[^\x00-\x7F]+', '', str(financial_response))
                            financial_response = financial_response.encode('ascii', 'ignore').decode('ascii')
                    except UnicodeEncodeError as ue:
                        financial_response = f"Financial analysis completed. Unicode encoding error: {str(ue)}"
                    except Exception as e:
                        financial_response = f"Financial analysis error: {str(e)}"
                    
                    analysis_result["financial"] = {
                        "analysis": financial_response,
                        "metrics": {
                            "revenue": company.get('Total_Revenue'),
                            "net_margin": company.get('Net_Profit_Margin'),
                            "debt_equity": company.get('Debt_to_Equity'),
                            "performance_score": company.get('Overall_Performance_Score')
                        }
                    }
        except Exception as e:
            analysis_result["financial"] = {"error": str(e)}
        
        # Growth Analysis using Growth Strategist agent
        try:
            if praison_manager and praison_manager.initialized:
                growth_agent = praison_manager.agents.get('growth_strategist')
                if growth_agent:
                    growth_prompt = f"""
                    Provide growth recommendations for {company_name}:
                    - Sector: {company.get('Sector', 'N/A')}
                    - Location: {company.get('Location', 'N/A')}
                    - Export Markets: {company.get('Export_Markets', 'N/A')}
                    - Growth Drivers: {company.get('Growth_Drivers', 'N/A')}
                    - Performance Score: {company.get('Overall_Performance_Score', 'N/A')}
                    
                    Suggest specific growth strategies, market opportunities, and expansion plans.
                    """
                    
                    try:
                        growth_response = growth_agent.run(growth_prompt)
                        # Sanitize response to remove emoji characters and handle encoding
                        if growth_response:
                            # Remove emoji characters and other problematic Unicode
                            import re
                            growth_response = re.sub(r'[^\x00-\x7F]+', '', str(growth_response))
                            growth_response = growth_response.encode('ascii', 'ignore').decode('ascii')
                    except UnicodeEncodeError as ue:
                        growth_response = f"Growth analysis completed. Unicode encoding error: {str(ue)}"
                    except Exception as e:
                        growth_response = f"Growth analysis error: {str(e)}"
                    
                    analysis_result["growth"] = {
                        "recommendations": growth_response,
                        "current_drivers": company.get('Growth_Drivers'),
                        "export_markets": company.get('Export_Markets')
                    }
        except Exception as e:
            analysis_result["growth"] = {"error": str(e)}
        
        # News Analysis using News Analyst agent
        try:
            if praison_manager and praison_manager.initialized:
                news_agent = praison_manager.agents.get('news_analyst')
                if news_agent:
                    news_prompt = f"""
                    Analyze recent news and market trends for {company_name}:
                    - Sector: {company.get('Sector', 'N/A')}
                    - Location: {company.get('Location', 'N/A')}
                    
                    Provide insights on industry trends, market sentiment, and relevant news.
                    """
                    
                    try:
                        news_response = news_agent.run(news_prompt)
                        # Sanitize response to remove emoji characters and handle encoding
                        if news_response:
                            # Remove emoji characters and other problematic Unicode
                            import re
                            news_response = re.sub(r'[^\x00-\x7F]+', '', str(news_response))
                            news_response = news_response.encode('ascii', 'ignore').decode('ascii')
                    except UnicodeEncodeError as ue:
                        news_response = f"News analysis completed. Unicode encoding error: {str(ue)}"
                    except Exception as e:
                        news_response = f"News analysis error: {str(e)}"
                    
                    analysis_result["news"] = {
                        "analysis": news_response,
                        "sector": company.get('Sector'),
                        "location": company.get('Location')
                    }
        except Exception as e:
            analysis_result["news"] = {"error": str(e)}
        
        return jsonify({
            "success": True,
            "analysis": analysis_result,
            "company_name": company_name
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dashboard/stock-news', methods=['POST'])
def get_company_stock_news():
    """Get stock/news for a specific company"""
    try:
        data = request.json
        company_name = data.get('company_name')
        news_type = data.get('news_type', 'all')
        
        if not company_name:
            return jsonify({"success": False, "error": "Company name required"}), 400
        
        # Get company data
        company = db_manager.companies_collection.find_one({'Company_Name': company_name})
        if not company:
            return jsonify({"success": False, "error": "Company not found"}), 404
        
        # Search for news related to the company
        search_query = f"{company_name} {company.get('Sector', '')}"
        
        # Use existing news search functionality
        news_results = enhanced_rag_service.enhanced_semantic_search_news(search_query, limit=10)
        
        # Filter news by type if specified
        filtered_news = []
        if news_results.get('articles'):
            for article in news_results['articles']:
                if news_type == 'all':
                    filtered_news.append(article)
                elif news_type == 'stock' and any(keyword in article.get('title', '').lower() for keyword in ['stock', 'share', 'ipo', 'market', 'trading']):
                    filtered_news.append(article)
                elif news_type == 'industry' and company.get('Sector', '').lower() in article.get('title', '').lower():
                    filtered_news.append(article)
        
        # Add sentiment analysis to news
        for article in filtered_news:
            # Simple sentiment analysis based on keywords
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            text = title + ' ' + description
            
            positive_words = ['growth', 'profit', 'success', 'increase', 'positive', 'strong', 'good', 'excellent']
            negative_words = ['loss', 'decline', 'decrease', 'negative', 'weak', 'bad', 'poor', 'crisis']
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                article['sentiment'] = 'positive'
            elif negative_count > positive_count:
                article['sentiment'] = 'negative'
            else:
                article['sentiment'] = 'neutral'
        
        return jsonify({
            "success": True,
            "news": filtered_news,
            "company_name": company_name,
            "news_type": news_type,
            "total": len(filtered_news)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dashboard/add-company', methods=['POST'])
def add_new_company():
    """Add a new company to the database"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['Company_Name', 'Sector', 'Location', 'Primary_Products']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        # Check if company already exists
        existing = db_manager.companies_collection.find_one({'Company_Name': data['Company_Name']})
        if existing:
            return jsonify({"success": False, "error": "Company already exists"}), 400
        
        # Generate keywords
        company_text = f"{data['Company_Name']} {data['Sector']} {data['Primary_Products']} {data['Location']}"
        similarity_service = SimpleTextSimilarity()
        keywords = similarity_service.find_keywords(company_text)
        data['keywords'] = keywords
        
        # Clean up data
        for key, value in data.items():
            if value == '' or value is None:
                data[key] = None
        
        # Insert company
        result = db_manager.companies_collection.insert_one(data)
        
        # Also add to financial collection if financial data provided
        if data.get('Total_Revenue') is not None:
            financial_data = {
                'Company_Name': data['Company_Name'],
                'Total_Revenue': data.get('Total_Revenue'),
                'Gross_Profit_Margin': data.get('Gross_Profit_Margin'),
                'Net_Profit_Margin': data.get('Net_Profit_Margin'),
                'Debt_to_Equity': data.get('Debt_to_Equity'),
                'Operating_Profit': data.get('Operating_Profit'),
                'Sales_Growth': data.get('Sales_Growth')
            }
            db_manager.financial_collection.insert_one(financial_data)
        
        return jsonify({
            "success": True,
            "message": f"Company {data['Company_Name']} added successfully",
            "company_id": str(result.inserted_id)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    print("Starting Enhanced MSME News Aggregator with PraisonAI Integration...")
    print("Available endpoints:")
    print("- POST /api/fetch-news - Fetch news articles")
    print("- POST /api/chat - Enhanced RAG chatbot with AI agents")
    print("- POST /api/dashboard - Generate intelligent charts")
    print("- GET /api/companies - Get MSME companies")
    print("- POST /api/load-data - Load CSV data")
    print("- GET /api/health - Health check")
    print("- GET /api/praison-status - PraisonAI status")
    print("- GET /api/tools-status - Tools status")
    print("\nDebug endpoints:")
    print("- GET /api/debug/help - Debug help and usage guide")
    print("- GET /api/debug/database - Check database state")
    print("- GET /api/debug/test-tools - Test all tools")
    print("- POST /api/debug/company-search - Debug company search")
    print("- POST /api/debug/agents - Debug agent routing")
    print("- POST /api/debug/query-breakdown - Complete query breakdown")
    
    print(f"\nPraisonAI Status:")
    print(f"- Available: {PRAISON_AVAILABLE}")
    print(f"- OpenAI Key: {'Configured' if Config.OPENAI_API_KEY else 'Not configured'}")
    print(f"- Agents Initialized: {praison_manager.initialized}")
    
    if not PRAISON_AVAILABLE:
        print("\nTo enable PraisonAI features:")
        print("1. Install: pip install praisonaiagents")
        print("2. Set OPENAI_API_KEY environment variable")
        print("3. Restart the application")
    
    # Try pinging MongoDB on startup
    ok, err = db_manager.ping()
    if ok:
        print("\nMongoDB connection: OK")
    else:
        print(f"\nMongoDB connection: FAILED -> {err}")
        print("Ensure MongoDB is running and MONGO_URI is correct.")
    
    app.run(debug=True, host='0.0.0.0', port=8000)
