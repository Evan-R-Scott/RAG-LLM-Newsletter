## Quick Start

1. Install Docker/Docker Compose
2. Clone this repo
3. Optionally run: `docker-compose pull` for latest images but not necessary
4. Run: `docker-compose up` to start app
5. Go to localhost:8000 on browser once container startup is complete

## What It Does

On container startup, articles from 15+ tech newsletters via their RSS feeds (anywhere from 500-2000 articles) are pulled and stored. When you query the chatbot at localhost:8000, it will find articles similar to what you asked about via RAG (if available) and provide summaries on those articles. The goal for this is just to let me learn about anything new in tech that I'm interested in (research papers/startups/inventions/etc) quicker and avoid scrolling through a ton of articles I find uninteresting. :D

## Newsletter RSS Feeds Used:

### General Tech & CS News

- MIT Technology Review
- The Verge
- Ars Technica
- Wired

### Startup and Business Tech

- VentureBeat
- Tech Crunch

### AI/ML Focused

- AI News
- Import AI

### Company Research Blogs

- Google AI Blog
- Meta Engineering Blog
- Microsoft AI Blog

### Academic Research

- Distill
- arXiv AI Papers
- arXiv Machine Learning Papers
- arXiv Computer Science Papers

## Things I want to add

- Short-term memory for deeper dives into specific articles
- Fine-tuning the local model with previous articles for better summarization
- Approximate Nearest Neighbor [ANN] since newsletters tend to have genre specialties
