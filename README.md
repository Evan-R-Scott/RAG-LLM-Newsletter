## Quick Start

1. Install Docker/Docker Compose
2. Clone this repo
3. Run: `docker-compose pull` for latest images
4. Run: `docker-compose up` to start app
5. Go to localhost:8000 on browser once container startup is complete

## What It Does

On container startup, articles from 15+ tech newsletters via their RSS feeds (anywhere from 500-2000 articles) are pulled and stored. When you query the chatbot at localhost:8000, it will find articles similar to what you asked about (if available) and provide summaries on those articles. The goal for this is just to let me learn about anything new in tech that I'm interested in (research papers/startups/inventions/etc) quicker and avoid scrolling through a ton of articles I find uninteresting. :D

## Newsletter RSS Feeds Used:

### General Tech & CS News

- MIT Technology Review (emerging tech across CS domains)
- The Verge (consumer tech)
- Ars Technica (deep technical coverage)
- Wired (tech culture, security, policy)

### Startup and Business Tech

- VentureBeat (enterprise tech, startup analysis)
- Tech Crunch (startup news, funding, products)

### AI/ML Focused

- AI News (AI industry developments)
- Import AI (AI policy & research summarization)

### Company Research Blogs

- Google AI Blog
- Meta Engineering Blog
- Microsoft AI Blog

### Academic Research

- Distill (visual AI research explanations)
- arXiv AI Papers (AI research)
- arXiv Machine Learning Papers (ML research)
- arXiv Computer Science Papers (all CS fields)
