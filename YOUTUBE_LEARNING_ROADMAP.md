# 🎬 YouTube Learning Roadmap
## Docker & Production Deployment — Video-First Study Plan
### For: Distributed Multi-Agent Agentic RAG Project Interview Prep

> **Study Strategy:**
> 1. Watch the videos in the order listed (fundamentals first, advanced later)
> 2. After each phase, go back to the **Interview Mastersheet** and re-read that section
> 3. The mastersheet will make 10x more sense after watching the video
> 4. Tick off phases as you complete them

---

## ⏱️ TOTAL ESTIMATED TIME
| Phase | Topic | Time |
|---|---|---|
| Phase 1 | How Docker Works (Conceptual Foundation) | ~2 hrs |
| Phase 2 | Docker Full Course (Hands-On) | ~3–4 hrs |
| Phase 3 | Multi-Stage Builds | ~1 hr |
| Phase 4 | Docker Compose Deep Dive | ~1.5 hrs |
| Phase 5 | Nginx — Reverse Proxy & Web Server | ~2 hrs |
| Phase 6 | CI/CD with GitHub Actions + Docker | ~2 hrs |
| Phase 7 | Kubernetes Fundamentals | ~4 hrs |
| Phase 8 | AWS Cloud Deployment (ECS, ECR, S3, RDS) | ~2.5 hrs |
| Phase 9 | Monitoring & Observability (Prometheus + Grafana) | ~1.5 hrs |
| Phase 10 | FastAPI Production & SSE Streaming | ~1.5 hrs |
| **TOTAL** | | **~22 hrs** |

> You don't need to watch all at once. Spread over 1–2 weeks. Focus on Phases 1–6 first — those are most interview-relevant for your project.

---

---

# PHASE 1 — HOW DOCKER WORKS (The "Why" Before the "How")
> **Goal:** Understand WHY Docker exists before touching a single command. This makes everything else click.
> **Mastersheet connection:** Part 1 — Docker Fundamentals

---

### 🎥 Video 1 — Start Here (100% Must Watch)
**"Docker in 100 Seconds"** — Fireship
🔗 https://www.youtube.com/watch?v=Gjnup-PuquQ
- ⏱️ 2 minutes
- Perfect first video. You'll understand containers vs VMs instantly.
- Fireship's style: fast, visual, excellent analogies

---

### 🎥 Video 2 — Container vs VM (Conceptual Clarity)
**"Containerization Explained"** — IBM Technology
🔗 https://www.youtube.com/watch?v=0qotVMX-J5s
- ⏱️ 8 minutes
- Explains WHY containers are different from VMs at the OS level
- Covers: namespaces, cgroups, union filesystem — the actual Linux tech under Docker
- **Key concept:** Docker doesn't virtualize hardware — it isolates processes using the Linux kernel

---

### 🎥 Video 3 — Full Docker Architecture
**"Docker Crash Course for Absolute Beginners"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=fqMOX6JJhGo
- ⏱️ 1 hr 20 min
- Nana is the gold standard for DevOps education
- Covers: Docker architecture, images vs containers, layers, registries, volumes
- **Best for:** Building the complete mental model you need before the full course

---

**After Phase 1 — Read in Mastersheet:**
- Part 1: "Docker Architecture (The Big Picture)"
- Part 1: "Docker Image Layers"
- Q1, Q2, Q9 in Part 12

---

---

# PHASE 2 — DOCKER FULL COURSE (Hands-On Commands)
> **Goal:** Learn all essential Docker commands, Dockerfile writing, and build mechanics.
> **Mastersheet connection:** Part 1 (commands) + Part 2 (Your Dockerfile line-by-line)

---

### 🎥 Video 4 — The Complete Docker Hands-On Course
**"Docker Tutorial for Beginners [FULL COURSE in 3 Hours]"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=3c-iLYHCgeo
- ⏱️ 3 hours
- This is THE most recommended Docker course on YouTube
- Covers:
  - `docker build`, `docker run`, `docker ps`, `docker logs`, `docker exec`
  - Dockerfile: FROM, RUN, COPY, CMD, EXPOSE, ENV, WORKDIR
  - Named volumes vs bind mounts
  - Docker networking basics
  - Push/pull from Docker Hub
- **Action:** Pause at each command and try it yourself

---

### 🎥 Video 5 — Docker Best Practices (Dockerfile Optimization)
**"Docker Best Practices and Anti-Patterns"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=8vXoMqWgbQQ
- ⏱️ 1 hour
- This is EXACTLY what interviewers ask about
- Covers:
  - Layer caching strategy (why copy requirements.txt before source code)
  - Using `.dockerignore`
  - Why `--no-cache-dir` for pip
  - Why `npm ci` not `npm install`
  - Using slim/alpine base images
  - Non-root users
- **Direct connection:** Your Dockerfile decisions in the mastersheet are explained here

---

### 🎥 Video 6 — NetworkChuck Docker (Fun Alternative Perspective)
**"you need to learn Docker RIGHT NOW!! (it's not that hard)"** — NetworkChuck
🔗 https://www.youtube.com/watch?v=eGz9DS-aIeY
- ⏱️ 26 minutes
- Very engaging and fun style if Nana's videos feel too structured
- Good for: reinforcing concepts with a different perspective
- Watch AFTER Video 4 as a refresher

---

**After Phase 2 — Read in Mastersheet:**
- Part 2: "Your Dockerfile Line-by-Line" (every single line will now make sense)
- Q3, Q4, Q5, Q6, Q7, Q8, Q10
- The "Essential Docker Commands" section

---

---

# PHASE 3 — MULTI-STAGE BUILDS (Your Key Resume Differentiator)
> **Goal:** Thoroughly understand the multi-stage pattern used in YOUR Dockerfile.
> **Mastersheet connection:** Part 3 — Multi-Stage Builds

---

### 🎥 Video 7 — Multi-Stage Builds Explained
**"Docker Multi-Stage Builds | Smaller Images, Better Security"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=70nV_3LhRnA
- ⏱️ 30–40 minutes
- Covers exactly the pattern in your Dockerfile:
  - `AS builder` stage for frontend compile
  - `COPY --from=builder` to carry artifacts
  - Why node_modules doesn't appear in the final image
  - Before/after image size comparison

---

### 🎥 Video 8 — Python + Node Multi-Stage Practical Example
**"Optimize your Docker builds with multi-stage builds"** — Fireship
🔗 https://www.youtube.com/watch?v=rRv-QCE5MrU
- ⏱️ 7 minutes
- Very quick, visual breakdown
- Shows the exact same pattern: Node build stage → Python/slim final stage
- Watch this right before an interview as a quick refresher

---

**After Phase 3 — Read in Mastersheet:**
- Part 3: "Multi-Stage Builds Deep Dive"
- Q11, Q12, Q13
- Q43 (your killer project-specific answer)

---

---

# PHASE 4 — DOCKER COMPOSE (Orchestrating Your Stack)
> **Goal:** Understand every line of your `docker-compose.yml` file deeply.
> **Mastersheet connection:** Part 4 — Docker Compose & Orchestration

---

### 🎥 Video 9 — Docker Compose Complete Tutorial
**"Docker Compose will BLOW your MIND!! (a tutorial)"** — NetworkChuck
🔗 https://www.youtube.com/watch?v=DM65_JyGxCo
- ⏱️ 40 minutes
- Fun, engaging intro to Docker Compose
- Covers: services, ports, volumes, networks, env_file
- Very beginner-friendly — great starting point

---

### 🎥 Video 10 — Docker Compose Deep Dive (Nana)
**"Docker Compose Tutorial"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=HGwCTH23-5M
- ⏱️ 50 minutes
- More technical than NetworkChuck's version
- Covers:
  - `depends_on` and its limitations
  - `condition: service_healthy` — exactly what your compose uses
  - Health checks
  - Restart policies (`unless-stopped`, `always`, `on-failure`)
  - Named volumes for database persistence
  - `env_file` vs `environment:` blocks
- **This video directly explains your `docker-compose.yml` decisions**

---

### 🎥 Video 11 — Docker Volumes Explained (Must Watch)
**"Docker Volumes explained in 6 minutes"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=p2PH_YPCsis
- ⏱️ 6 minutes
- Short but critical — explains named volumes vs bind mounts
- Connects directly to: why `chroma_data` is a named volume but `feedback.db` is a bind mount

---

**After Phase 4 — Read in Mastersheet:**
- Part 4: Full section on Docker Compose
- Q14, Q15, Q16, Q17, Q18, Q19
- Q45 (healthcheck start_period killer answer)
- Q46 (two Dockerfiles — different targets)

---

---

# PHASE 5 — NGINX (Reverse Proxy, Static Files, SPA Routing)
> **Goal:** Understand what Nginx does in your architecture and why every config line exists.
> **Mastersheet connection:** Part 5 — Nginx as Reverse Proxy

---

### 🎥 Video 12 — Nginx Explained (What Is It?)
**"NGINX Tutorial for Beginners"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=7VAI73roXaY
- ⏱️ 30 minutes
- Covers: web server vs reverse proxy vs load balancer
- Explains `location` blocks, `proxy_pass`, `root`, `try_files`
- **Directly explains your `nginx.conf`**

---

### 🎥 Video 13 — Nginx as Reverse Proxy (Hands-On)
**"NGINX Proxy Manager - How-To Installation and Configuration"** — Wolfgang's Channel
🔗 https://www.youtube.com/watch?v=sFaB0LKGX2E  
- ⏱️ 30 minutes
- Real-world reverse proxy setup
- See how proxy_pass, headers, and timeouts work in practice

---

### 🎥 Video 14 — Nginx for React SPA (Critical for Your Architecture)
**"How to Deploy a React App with Nginx"** — Traversy Media
🔗 https://www.youtube.com/watch?v=n1yaS3J3kEA
- ⏱️ 30 minutes
- Explains exactly WHY `try_files $uri $uri/ /index.html` is needed
- Shows React Router + Nginx working together
- Directly explains Q21 in your mastersheet

---

### 🎥 Video 15 — Nginx Config Deep Dive (Gzip, Headers, Timeouts)
**"NGINX Crash Course"** — Traversy Media
🔗 https://www.youtube.com/watch?v=7VAI73roXaY
- ⏱️ 45 minutes
- Goes deep on: gzip, proxy headers (X-Real-IP, X-Forwarded-For), timeouts
- Explains why `proxy_read_timeout 300` is needed for LLM streaming apps

---

**After Phase 5 — Read in Mastersheet:**
- Part 5: Full Nginx section
- Q20, Q21, Q22, Q23, Q24
- Q47 (your killer answer about how Nginx proxies API requests)

---

---

# PHASE 6 — CI/CD WITH GITHUB ACTIONS + DOCKER
> **Goal:** Understand the automated build-test-deploy pipeline that production teams use.
> **Mastersheet connection:** Part 7 — CI/CD Pipelines

---

### 🎥 Video 16 — GitHub Actions Explained
**"GitHub Actions Tutorial - Basic Concepts and CI/CD Pipeline with Docker"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=R8_veQiYBjI
- ⏱️ 32 minutes
- This is THE video for your interview
- Covers:
  - What is CI/CD? (Continuous Integration / Continuous Deployment)
  - GitHub Actions: workflows, jobs, steps, runners
  - Building Docker images in CI
  - Pushing to Docker Hub from GitHub Actions
  - Using GitHub Secrets for credentials (DOCKER_HUB_TOKEN)
  - Deploying to a server after CI passes

---

### 🎥 Video 17 — Complete CI/CD Pipeline from Scratch
**"Complete CI/CD with GitHub Actions"** — Fireship
🔗 https://www.youtube.com/watch?v=eB0nUzAI7M8
- ⏱️ 11 minutes
- Fast overview of a complete pipeline
- Shows the YAML workflow file structure clearly
- Great for: understanding the "shape" of a GitHub Actions workflow file

---

### 🎥 Video 18 — Blue-Green Deployments Explained
**"Blue Green Deployment"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=J_OxRl2BqHo
- ⏱️ 8 minutes
- Explains zero-downtime deployment strategy
- Directly maps to Q in the mastersheet: "Your Groq API key is expiring, how do you update without downtime?"

---

**After Phase 6 — Read in Mastersheet:**
- Part 7: Full CI/CD section
- The "Image Tagging Strategy" table
- The "Blue-Green Deployment" section
- The scenario Q: "You pushed a buggy image to production. Recovery process?"

---

---

# PHASE 7 — KUBERNETES (K8s) FUNDAMENTALS
> **Goal:** Understand what Kubernetes is, why it exists, and how it compares to Docker Compose.
> **Note:** You don't need to be K8s expert — but you need to speak to Deployments, Services, Secrets, Health Probes.
> **Mastersheet connection:** Part 11 — Cloud & Deployment Platforms, Q39, Q40, Q41, Q42

---

### 🎥 Video 19 — Kubernetes in 100 Seconds
**"Kubernetes Explained in 100 Seconds"** — Fireship
🔗 https://www.youtube.com/watch?v=PziYflu8cB8
- ⏱️ 2 minutes
- Start here for the big picture
- Understand: what problem K8s solves vs Docker Compose

---

### 🎥 Video 20 — Kubernetes Full Course (The Gold Standard)
**"Kubernetes Tutorial for Beginners [FULL COURSE in 4 Hours]"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=X48VuDVv0do
- ⏱️ 4 hours
- The most recommended K8s course on YouTube (3M+ views)
- Covers:
  - Pods, Deployments, Services, Ingress
  - ConfigMaps and Secrets (the K8s equivalent of your `.env`)
  - Persistent Volumes (equivalent of your named volumes)
  - Health probes: `livenessProbe`, `readinessProbe` — equivalent to your Docker health checks
  - Namespaces
  - kubectl commands
  - YAML config files
- **For interviews:** Focus especially on: Deployments, Services, Secrets, Probes, Resource Limits
- **Skip (for now):** StatefulSets, Helm, advanced sections

---

### 🎥 Video 21 — Docker Compose vs Kubernetes
**"Docker Swarm vs Kubernetes"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=NHPiJc3YXQk
- ⏱️ 8 minutes
- Directly answers Q39 in your mastersheet: "When would you choose Kubernetes over Docker Compose?"

---

**After Phase 7 — Read in Mastersheet:**
- Part 11: "Kubernetes Quick Reference" section
- Q39, Q40, Q41, Q42
- The K8s YAML equivalent of your docker-compose.yml

---

---

# PHASE 8 — AWS CLOUD DEPLOYMENT (ECS, ECR, S3, RDS)
> **Goal:** Understand the AWS services that replace your Docker Compose when deploying to the cloud.
> **Mastersheet connection:** Part 11 — AWS Services Map, Q49 (AWS migration answer)

---

### 🎥 Video 22 — AWS for Beginners (Big Picture)
**"AWS Certified Cloud Practitioner Certification Course (CLF-C02)"** — freeCodeCamp
🔗 https://www.youtube.com/watch?v=NhDYbskXRgc
- ⏱️ 14 hours (DON'T watch all — use timestamp chapters)
- **Watch chapters on:**
  - EC2 (virtual machines — 30 min)
  - S3 (file storage — 20 min)
  - RDS (managed database — 20 min)
  - VPC & Security Groups (networking — 30 min)
  - IAM (permissions — 20 min)
- Skip: billing, compliance, Support plans (not interview relevant)

---

### 🎥 Video 23 — AWS ECS + ECR (Deploy Docker to AWS)
**"AWS ECS Tutorial | Deploy Docker containers to Elastic Container Service"**
Search on YouTube: "AWS ECS Fargate tutorial for beginners" (pick a 2023/2024 video)
Recommended channels to look for: Stephane Maarek, Be a Better Dev, Cloud With Raj
- ⏱️ 45–60 minutes
- Learn:
  - What is ECR (private Docker registry on AWS)?
  - What is ECS Task Definition (like docker-compose service config)?
  - What is ECS Service (the thing that keeps your container running)?
  - What is Fargate (serverless containers — no EC2 management)?
  - How CloudWatch Logs replaces `docker logs`
- **Key understanding:** ECS Task Definition ≈ docker-compose.yml service block

---

### 🎥 Video 24 — AWS S3 for File Storage
**"Amazon S3 Tutorial for Beginners"** — AWS Official
🔗 https://www.youtube.com/watch?v=mDRoyPFJvlU (or search "AWS S3 tutorial beginner")
- ⏱️ 20 minutes
- Understand: why you'd replace your local `uploads/` folder with S3 in production
- Key for Q49 in your mastersheet: "replace local uploads/ with S3"

---

### 🎥 Video 25 — AWS RDS for Databases
Search YouTube: "AWS RDS tutorial for beginners"
- ⏱️ 20–30 minutes
- Understand: why you'd replace SQLite (feedback.db) with RDS PostgreSQL for scale
- Key for Q49: "replace SQLite with RDS for concurrent-write safety"

---

**After Phase 8 — Read in Mastersheet:**
- Part 11: Full "AWS Services Map" table
- Q49: "What would you change for a production AWS deployment?" — you should now be able to give a rich answer
- The "Vocabulary Cheat Sheet" at the end (ECR, ECS, Fargate, etc.)

---

---

# PHASE 9 — MONITORING & OBSERVABILITY (Prometheus + Grafana)
> **Goal:** Understand how production systems are monitored — logs, metrics, and traces.
> **Mastersheet connection:** Part 8 — Monitoring, Logging & Observability

---

### 🎥 Video 26 — Monitoring Concepts (Start Here)
**"Prometheus vs. Grafana | What's the difference?"** — IBM Technology
🔗 https://www.youtube.com/watch?v=h4Sl21AKiDg (or search "Prometheus Grafana explained simply")
- ⏱️ 10 minutes
- Understand the relationship:
  - Prometheus = data collector (scrapes metrics)
  - Grafana = visualization layer (builds dashboards from Prometheus data)

---

### 🎥 Video 27 — Full Prometheus + Grafana Setup
**"Prometheus and Grafana Tutorial — Monitor Your Servers and Containers"** — TechWorld with Nana
🔗 https://www.youtube.com/watch?v=QNbCBv9duhQ
- ⏱️ 1 hour
- Covers:
  - How Prometheus scrapes `/metrics` endpoints
  - Setting up cAdvisor to get Docker container metrics
  - Building Grafana dashboards
  - Alert rules (CPU >80%, memory >90%)
- **Key connection:** Q50 in mastersheet: "What monitoring would you add to this application?"

---

### 🎥 Video 28 — Logging with Docker (Practical)
**"Docker Logging: Everything You Need to Know"** — Docker Official / TechWorld
Search: "Docker logging best practices tutorial"
- ⏱️ 20–30 minutes
- Covers `docker logs`, log drivers (json-file, fluentd, awslogs)
- Understand: why `PYTHONUNBUFFERED=1` matters for real-time logs (Q28 in mastersheet)

---

### 🎥 Video 29 — Distributed Tracing (LangSmith for Your App)
**"What is Distributed Tracing?"** — ByteByteGo
🔗 https://www.youtube.com/watch?v=EW67M9clOxs (or search "distributed tracing explained ByteByteGo")
- ⏱️ 10 minutes
- This directly maps to LangSmith in your project
- Understand: trace spans, how to see which agent node (Planner/Retriever/Generator) is slow

---

**After Phase 9 — Read in Mastersheet:**
- Part 8: Full Monitoring section
- Q35, Q36, Q37, Q38 (debugging questions)
- Q50 (your monitoring answer for the RAG app)

---

---

# PHASE 10 — FASTAPI PRODUCTION + SSE STREAMING
> **Goal:** Understand why FastAPI is production-grade and how SSE streaming works.
> **Mastersheet connection:** Part 9 — Scalability, Q25–Q30

---

### 🎥 Video 30 — FastAPI Full Course
**"FastAPI Course for Beginners"** — freeCodeCamp
🔗 https://www.youtube.com/watch?v=tLKKmouUams
- ⏱️ 1 hour
- Great for: async/await, route handlers, Pydantic, CORS middleware
- Key concepts: understand async def vs def in FastAPI — why it matters for SSE

---

### 🎥 Video 31 — ASGI vs WSGI (The Core Architecture Difference)
**"What is ASGI? (Async Python Web)"** — Search YouTube for "ASGI WSGI difference explained"
Or watch: "Python ASGI Explained" — Arjan Codes channel
- ⏱️ 15 minutes
- Explains WHY FastAPI (ASGI) supports streaming when Flask/Django (WSGI) doesn't
- Directly answers Q26 in mastersheet

---

### 🎥 Video 32 — Server-Sent Events (SSE) Explained
**"WebSockets vs Server-Sent Events vs Long Polling"** — Hussein Nasser
🔗 https://www.youtube.com/watch?v=J0lHudBTRn0 (or search "SSE vs WebSocket Hussein Nasser")
- ⏱️ 20–30 minutes
- Explains the difference between SSE, WebSockets, and Long Polling
- WHY SSE is better for LLM token streaming (unidirectional, HTTP-based, proxy-friendly)
- Directly answers Q27 in mastersheet

---

### 🎥 Video 33 — Uvicorn Workers + Gunicorn Production Setup
Search YouTube: "FastAPI production uvicorn gunicorn workers deployment"
Recommended: "Deploy FastAPI with Gunicorn and Uvicorn" — any clear tutorial
- ⏱️ 20 minutes
- Understand: why `--workers 4` matters, the formula (2×CPU+1)
- Understand: worker = separate Python process (GIL workaround)
- Directly answers Q25 in mastersheet

---

**After Phase 10 — Read in Mastersheet:**
- Part 9: Full Scalability section
- Q25 (uvicorn workers), Q26 (ASGI vs WSGI), Q27 (SSE), Q28 (PYTHONUNBUFFERED), Q29

---

---

# 🗺️ RECOMMENDED STUDY SCHEDULE

## Week 1 — Foundations (Phases 1–4)
| Day | What to Watch | Time |
|---|---|---|
| Day 1 | Videos 1, 2, 3 (Docker concepts + architecture) | 2 hrs |
| Day 2 | Video 4 (Docker 3-hour full course — Part 1: first 1.5 hrs) | 1.5 hrs |
| Day 3 | Video 4 (Part 2: remaining 1.5 hrs) + Video 5 (best practices) | 2.5 hrs |
| Day 4 | Videos 7, 8 (Multi-Stage Builds) | 1 hr |
| Day 5 | Videos 9, 10 (Docker Compose) + Video 11 (Volumes) | 1.5 hrs |
| Day 6-7 | Re-read Mastersheet Parts 1–4 | 2 hrs |

## Week 2 — Production Skills (Phases 5–8)
| Day | What to Watch | Time |
|---|---|---|
| Day 8 | Videos 12, 13 (Nginx) | 1 hr |
| Day 9 | Videos 14, 15 (Nginx for SPA + deep dive) | 1.5 hrs |
| Day 10 | Videos 16, 17, 18 (CI/CD + Blue-Green) | 2 hrs |
| Day 11 | Videos 19, 20 (K8s — first 2 hrs of Nana's course) | 2 hrs |
| Day 12 | Videos 20 cont. + 21 (K8s complete + Compose vs K8s) | 2 hrs |
| Day 13 | Videos 22 chapters + 23 (AWS ECS intro) | 2 hrs |
| Day 14 | Re-read Mastersheet Parts 5–11 | 2 hrs |

## Final 2–3 Days Before Interview
| Day | Activity |
|---|---|
| Day 15 | Videos 26, 27 (Prometheus + Grafana — 1.5 hrs) |
| Day 16 | Videos 30, 31, 32 (FastAPI + ASGI + SSE — 1 hr) |
| Day 17 | Read entire Mastersheet Part 12 (all Q&As) out loud |

---

---

# 📌 CHANNEL BOOKMARKS — WHO TO FOLLOW

| Channel | Why Follow | Best For |
|---|---|---|
| **TechWorld with Nana** | Best DevOps educator on YouTube. Clear, visual, deep | Docker, Kubernetes, CI/CD, Monitoring |
| **NetworkChuck** | Engaging, fun, practical. Great for motivation | Docker, Networking, Linux |
| **Fireship** | 100-second intros + quick conceptual overviews | Any topic — quick mental model |
| **Traversy Media** | Full crash courses, very practical | Nginx, React, Node.js, real-world projects |
| **freeCodeCamp** | Long-form, comprehensive, free | Full courses — Docker, AWS, FastAPI |
| **ByteByteGo** | System design concepts, beautiful animations | Distributed systems, tracing, scaling |
| **Hussein Nasser** | Deep networking and backend engineering | SSE, WebSockets, HTTP, ASGI, proxies |
| **Arjan Codes** | Clean Python engineering | FastAPI, async, async Python patterns |
| **IBM Technology** | Official IBM education, clear concept videos | Cloud, containers, Kubernetes concepts |

---

---

# 🔗 ALL LINKS — QUICK REFERENCE LIST

| # | Video | Link |
|---|---|---|
| 1 | Docker in 100 Seconds — Fireship | https://www.youtube.com/watch?v=Gjnup-PuquQ |
| 2 | Containerization Explained — IBM Technology | https://www.youtube.com/watch?v=0qotVMX-J5s |
| 3 | Docker Crash Course — TechWorld with Nana | https://www.youtube.com/watch?v=fqMOX6JJhGo |
| 4 | Docker Full Course 3 hrs — TechWorld with Nana | https://www.youtube.com/watch?v=3c-iLYHCgeo |
| 5 | Docker Best Practices — TechWorld with Nana | https://www.youtube.com/watch?v=8vXoMqWgbQQ |
| 6 | Docker you need to learn — NetworkChuck | https://www.youtube.com/watch?v=eGz9DS-aIeY |
| 7 | Multi-Stage Builds — TechWorld with Nana | https://www.youtube.com/watch?v=70nV_3LhRnA |
| 8 | Optimize Docker Builds — Fireship | https://www.youtube.com/watch?v=rRv-QCE5MrU |
| 9 | Docker Compose Mind Blown — NetworkChuck | https://www.youtube.com/watch?v=DM65_JyGxCo |
| 10 | Docker Compose Tutorial — TechWorld with Nana | https://www.youtube.com/watch?v=HGwCTH23-5M |
| 11 | Docker Volumes in 6 min — TechWorld with Nana | https://www.youtube.com/watch?v=p2PH_YPCsis |
| 12 | NGINX Tutorial — TechWorld with Nana | https://www.youtube.com/watch?v=7VAI73roXaY |
| 13 | Nginx Proxy Manager Setup — Wolfgang's Channel | https://www.youtube.com/watch?v=sFaB0LKGX2E |
| 14 | Deploy React App with Nginx — Traversy Media | https://www.youtube.com/watch?v=n1yaS3J3kEA |
| 16 | GitHub Actions CI/CD + Docker — TechWorld with Nana | https://www.youtube.com/watch?v=R8_veQiYBjI |
| 17 | Complete CI/CD — Fireship | https://www.youtube.com/watch?v=eB0nUzAI7M8 |
| 18 | Blue Green Deployment — TechWorld with Nana | https://www.youtube.com/watch?v=J_OxRl2BqHo |
| 19 | Kubernetes in 100 Seconds — Fireship | https://www.youtube.com/watch?v=PziYflu8cB8 |
| 20 | Kubernetes Full Course 4 hrs — TechWorld with Nana | https://www.youtube.com/watch?v=X48VuDVv0do |
| 21 | Docker Swarm vs Kubernetes — TechWorld with Nana | https://www.youtube.com/watch?v=NHPiJc3YXQk |
| 22 | AWS Cloud Practitioner Full — freeCodeCamp | https://www.youtube.com/watch?v=NhDYbskXRgc |
| 27 | Prometheus + Grafana — TechWorld with Nana | https://www.youtube.com/watch?v=QNbCBv9duhQ |
| 29 | Distributed Tracing — ByteByteGo | https://www.youtube.com/watch?v=EW67M9clOxs |
| 30 | FastAPI Course — freeCodeCamp | https://www.youtube.com/watch?v=tLKKmouUams |
| 32 | SSE vs WebSocket — Hussein Nasser | https://www.youtube.com/watch?v=J0lHudBTRn0 |

---

---

# 🎯 PRE-INTERVIEW RAPID REVIEW (Watch These the Night Before)
If you have only 3 hours before an interview:

1. **Video 3** — Docker Architecture (Nana Crash Course) — 1h 20min
2. **Video 7** — Multi-Stage Builds — 35min
3. **Video 11** — Docker Volumes — 6min
4. Read: Mastersheet Q43–Q50 (project-specific answers) — 20min
5. Read: Mastersheet "Quick Reference: Your Tech Stack Answers" table — 10min

That's it. Those 5 things will let you answer 90% of Docker questions thrown at you.

---

*Study Roadmap version 1.0 — April 2026*
*Paired with: DOCKER_PRODUCTION_INTERVIEW_MASTERSHEET.md*
