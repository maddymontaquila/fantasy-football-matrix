from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv
from espn_api.football import League
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Fantasy Football Matrix API", version="1.0.0")

# Add CORS middleware for matrix portal access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TeamInMatchup(BaseModel):
    team_id: int
    team_abbrev: str  # 4-char abbreviation for matrix display
    team_name: str
    current_score: float
    projected_score: float

class MatchupData(BaseModel):
    matchup_index: int  # 0-based index for matrix cycling (0-5 for 12-team league)
    home_team: TeamInMatchup
    away_team: TeamInMatchup
    home_win_probability: float  # 0.0 to 1.0
    away_win_probability: float  # 0.0 to 1.0
    is_complete: bool
    
class MatrixData(BaseModel):
    matchups: List[MatchupData]
    week: int
    league_name: str
    total_matchups: int

@app.get("/")
async def root():
    return {"message": "Fantasy Football Matrix API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def get_league() -> League:
    """
    Create ESPN league instance with environment configuration
    """
    league_id = int(os.getenv("ESPN_LEAGUE_ID"))
    year = int(os.getenv("ESPN_YEAR", "2025"))
    swid = os.getenv("ESPN_SWID")
    espn_s2 = os.getenv("ESPN_S2")
    
    if swid and espn_s2:
        return League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)
    else:
        return League(league_id=league_id, year=year)



def calculate_win_probability(home_score: float, away_score: float, 
                            home_proj: float, away_proj: float) -> tuple[float, float]:
    """
    Calculate win probability based on current scores and projections
    Simple algorithm: factor in both current lead and projection advantage
    """
    if home_proj + away_proj == 0:
        return 0.5, 0.5
    
    # Current score advantage (30% weight)
    score_diff = home_score - away_score
    
    # Projection advantage (70% weight) 
    proj_diff = home_proj - away_proj
    
    # Combined advantage
    total_advantage = (score_diff * 0.3) + (proj_diff * 0.7)
    
    # Convert to probability using sigmoid-like function
    # Normalize by total projected points for scaling
    total_proj = home_proj + away_proj
    if total_proj > 0:
        normalized_advantage = total_advantage / (total_proj * 0.1)  # Scale factor
        home_prob = 1 / (1 + pow(2.71828, -normalized_advantage))
    else:
        home_prob = 0.5
    
    away_prob = 1.0 - home_prob
    
    return round(home_prob, 3), round(away_prob, 3)

@app.get("/league/data", response_model=MatrixData)
async def get_league_data() -> MatrixData:
    """
    Internal function to fetch league data from ESPN API
    """
    try:
        league = get_league()
        current_week = league.current_week
        box_scores = league.box_scores(week=current_week)

        matchups_data = []
        for i, box in enumerate(box_scores):
            home_team = box.home_team
            away_team = box.away_team

            # Get current scores and projections from box score
            home_score = round(box.home_score, 1)
            away_score = round(box.away_score, 1)
            home_proj = round(box.home_projected, 1)
            away_proj = round(box.away_projected, 1)

            # Calculate win probabilities
            home_win_prob, away_win_prob = calculate_win_probability(
                home_score, away_score, home_proj, away_proj
            )

            matchup_data = MatchupData(
                matchup_index=i,
                home_team=TeamInMatchup(
                    team_id=home_team.team_id,
                    team_abbrev=home_team.team_abbrev,
                    team_name=home_team.team_name,
                    current_score=home_score,
                    projected_score=home_proj
                ),
                away_team=TeamInMatchup(
                    team_id=away_team.team_id,
                    team_abbrev=away_team.team_abbrev,
                    team_name=away_team.team_name,
                    current_score=away_score,
                    projected_score=away_proj
                ),
                home_win_probability=home_win_prob,
                away_win_probability=away_win_prob,
                is_complete=box.is_playoff  # Using is_playoff as proxy since box doesn't have is_complete
            )
            matchups_data.append(matchup_data)

        return MatrixData(
            matchups=matchups_data,
            week=current_week,
            league_name=league.settings.name,
            total_matchups=len(matchups_data)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching league data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)