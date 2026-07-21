from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, people, sites, sprints, sync, tech_map

app = FastAPI(title="Jira Dashboard MBC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sites.router)
app.include_router(sprints.router)
app.include_router(people.router)
app.include_router(sync.router)
app.include_router(tech_map.router)
