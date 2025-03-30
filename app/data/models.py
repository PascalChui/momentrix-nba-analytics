"""Modèles de données pour Momentrix NBA Analytics.

Ce module définit les structures de données utilisées dans l'application."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Team:
    """Représente une équipe NBA."""
    id: int
    name: str
    code: str
    conference: str
    division: str
    logo_url: Optional[str] = None
    wins: int = 0
    losses: int = 0
    
    @property
    def record(self) -> str:
        """Retourne le bilan victoires-défaites de l'équipe."""
        return f"{self.wins}-{self.losses}"

@dataclass
class Player:
    """Représente un joueur NBA."""
    id: int
    name: str
    team_id: int
    jersey_number: Optional[str] = None
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    birth_date: Optional[datetime] = None
    college: Optional[str] = None
    country: Optional[str] = None

@dataclass
class Game:
    """Représente un match NBA."""
    id: int
    date: datetime
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = "scheduled"  # scheduled, live, finished
    arena: Optional[str] = None
    
    @property
    def is_finished(self) -> bool:
        """Indique si le match est terminé."""
        return self.status == "finished" and self.home_score is not None and self.away_score is not None
    
    @property
    def winner_id(self) -> Optional[int]:
        """Retourne l'ID de l'équipe gagnante ou None si match non terminé ou égalité."""
        if not self.is_finished:
            return None
        if self.home_score > self.away_score:
            return self.home_team_id
        elif self.away_score > self.home_score:
            return self.away_team_id
        return None  # En cas d'égalité (rare en NBA mais possible)

@dataclass
class GameQuarter:
    """Représente les statistiques d'un quart-temps."""
    id: int
    game_id: int
    quarter: int  # 1-4 pour les quart-temps réguliers, 5+ pour prolongations
    home_score: int
    away_score: int
    
    @property
    def home_differential(self) -> int:
        """Différentiel de points pour l'équipe à domicile."""
        return self.home_score - self.away_score
    
    @property
    def away_differential(self) -> int:
        """Différentiel de points pour l'équipe visiteuse."""
        return self.away_score - self.home_score

@dataclass
class Badge:
    """Représente un badge attribué à une équipe."""
    id: int
    team_id: int
    badge_code: str
    attribution_date: datetime
    justification: str
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        """Indique si le badge est expiré (plus de 15 jours sans confirmation)."""
        expiration_days = 15  # Badges expirent après 15 jours sans confirmation
        delta = datetime.now() - self.attribution_date
        return delta.days > expiration_days and not self.is_active

@dataclass 
class Prediction:
    """Représente une prédiction pour un match."""
    id: int
    game_id: int
    home_win_probability: float
    predicted_home_score: Optional[int] = None
    predicted_away_score: Optional[int] = None
    creation_date: datetime = datetime.now()
    confidence_level: float = 0.0
    key_factors: Optional[str] = None
    
    @property
    def is_accurate(self) -> Optional[bool]:
        """Vérifie si la prédiction était correcte, basé sur le résultat réel."""
        from .database import get_db_connection
        db = get_db_connection()
        game = db.get_game(self.game_id)
        
        if not game or not game.is_finished:
            return None
            
        actual_home_win = game.home_score > game.away_score
        predicted_home_win = self.home_win_probability > 0.5
        
        return actual_home_win == predicted_home_win

@dataclass
class QuarterProfile:
    """Profil de performance d'un quart-temps pour une équipe."""
    team_id: int
    quarter: int  # 1-4
    avg_points_for: float
    avg_points_against: float
    std_points_for: float
    std_points_against: float
    win_percentage: float
    last_update: datetime = datetime.now()
    
    @property
    def avg_differential(self) -> float:
        """Différentiel moyen de points pour ce quart-temps."""
        return self.avg_points_for - self.avg_points_against
