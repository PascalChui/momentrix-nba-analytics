"""Client API pour l'interaction avec l'API NBA.

Ce module fournit une interface unifiée pour les requêtes vers l'API NBA,
avec gestion du cache et des erreurs.
"""

import requests
import json
import time
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from flask import current_app, g
from app.data.database import get_db_connection

class NBAApiClient:
    """Client pour l'API NBA avec gestion du cache."""
    
    def __init__(self, api_key: str, api_host: str, cache_timeout: int = 86400):
        """Initialise le client API.
        
        Args:
            api_key: Clé API pour l'authentification
            api_host: Hôte de l'API (e.g., api-nba-v1.p.rapidapi.com)
            cache_timeout: Durée de validité du cache en secondes (défaut: 24h)
        """
        self.api_key = api_key
        self.api_host = api_host
        self.base_url = f"https://{api_host}"
        self.cache_timeout = cache_timeout
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": api_host
        }
    
    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Génère une clé de cache unique pour la requête.
        
        Args:
            endpoint: Point d'entrée de l'API
            params: Paramètres de la requête
            
        Returns:
            Clé de cache unique
        """
        # Trier les paramètres pour assurer la cohérence des clés
        sorted_params = json.dumps(params, sort_keys=True)
        # Utiliser un hash pour éviter les clés trop longues
        cache_key = hashlib.md5(f"{endpoint}:{sorted_params}".encode()).hexdigest()
        return cache_key
    
    def _get_from_cache(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Tente de récupérer une réponse mise en cache.
        
        Args:
            endpoint: Point d'entrée de l'API
            params: Paramètres de la requête
            
        Returns:
            Données en cache ou None si non trouvées/expirées
        """
        db = get_db_connection()
        conn = db._get_connection()
        try:
            cursor = conn.cursor()
            params_str = json.dumps(params, sort_keys=True)
            query = """
                SELECT response, timestamp
                FROM api_cache
                WHERE endpoint = ? AND parameters = ? AND expiry > datetime('now')
                ORDER BY timestamp DESC
                LIMIT 1
            """
            cursor.execute(query, (endpoint, params_str))
            result = cursor.fetchone()
            
            if result:
                return json.loads(result['response'])
            return None
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération du cache: {e}")
            return None
        finally:
            conn.close()
    
    def _save_to_cache(self, endpoint: str, params: Dict[str, Any], response: Dict[str, Any]) -> bool:
        """Sauvegarde une réponse API dans le cache.
        
        Args:
            endpoint: Point d'entrée de l'API
            params: Paramètres de la requête
            response: Réponse de l'API à mettre en cache
            
        Returns:
            True si sauvegarde réussie, False sinon
        """
        db = get_db_connection()
        conn = db._get_connection()
        try:
            cursor = conn.cursor()
            params_str = json.dumps(params, sort_keys=True)
            response_str = json.dumps(response)
            expiry = datetime.now() + timedelta(seconds=self.cache_timeout)
            
            query = """
                INSERT INTO api_cache (endpoint, parameters, response, timestamp, expiry)
                VALUES (?, ?, ?, datetime('now'), ?)
            """
            cursor.execute(query, (endpoint, params_str, response_str, expiry.isoformat()))
            conn.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la sauvegarde du cache: {e}")
            return False
        finally:
            conn.close()
    
    def request(self, endpoint: str, params: Dict[str, Any] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """Effectue une requête vers l'API NBA avec gestion du cache.
        
        Args:
            endpoint: Point d'entrée de l'API (e.g., "teams", "games", "statistics")
            params: Paramètres de la requête
            force_refresh: Force la récupération depuis l'API même si présent en cache
            
        Returns:
            Données de réponse de l'API
            
        Raises:
            Exception: En cas d'erreur dans la requête API
        """
        if params is None:
            params = {}
        
        # Vérifier le cache sauf si force_refresh est activé
        if not force_refresh:
            cached_response = self._get_from_cache(endpoint, params)
            if cached_response:
                current_app.logger.debug(f"Utilisation des données en cache pour {endpoint}")
                return cached_response
        
        # Construire l'URL complète
        url = f"{self.base_url}/{endpoint}"
        
        try:
            # Effectuer la requête API
            current_app.logger.info(f"Requête API vers {endpoint} avec paramètres {params}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Lever une exception en cas d'erreur HTTP
            
            # Analyser la réponse JSON
            data = response.json()
            
            # Mettre en cache la réponse
            self._save_to_cache(endpoint, params, data)
            
            return data
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erreur lors de la requête API vers {endpoint}: {e}")
            # En cas d'erreur, tenter de récupérer du cache même si expiré comme solution de secours
            cached_response = self._get_from_cache(endpoint, params)
            if cached_response:
                current_app.logger.warning(f"Utilisation des données en cache expirées pour {endpoint} suite à une erreur")
                return cached_response
            raise Exception(f"Erreur lors de la requête API et aucune donnée en cache: {e}")
    
    def get_teams(self) -> Dict[str, Any]:
        """Récupère la liste des équipes NBA.
        
        Returns:
            Données des équipes NBA
        """
        return self.request("teams")
    
    def get_team(self, team_id: int) -> Dict[str, Any]:
        """Récupère les informations d'une équipe spécifique.
        
        Args:
            team_id: Identifiant de l'équipe
            
        Returns:
            Données de l'équipe
        """
        return self.request(f"teams/{team_id}")
    
    def get_games(self, date: Optional[str] = None, team_id: Optional[int] = None) -> Dict[str, Any]:
        """Récupère les matchs selon différents critères.
        
        Args:
            date: Date des matchs au format "YYYY-MM-DD" (optionnel)
            team_id: Identifiant de l'équipe (optionnel)
            
        Returns:
            Données des matchs
        """
        params = {}
        if date:
            params["date"] = date
        if team_id:
            params["team"] = team_id
            
        return self.request("games", params)
    
    def get_game_details(self, game_id: int) -> Dict[str, Any]:
        """Récupère les détails d'un match spécifique.
        
        Args:
            game_id: Identifiant du match
            
        Returns:
            Détails du match
        """
        return self.request(f"games/{game_id}")
    
    def get_game_statistics(self, game_id: int) -> Dict[str, Any]:
        """Récupère les statistiques d'un match spécifique.
        
        Args:
            game_id: Identifiant du match
            
        Returns:
            Statistiques du match
        """
        return self.request(f"statistics/games/{game_id}")
    
    def get_players(self, team_id: Optional[int] = None) -> Dict[str, Any]:
        """Récupère la liste des joueurs.
        
        Args:
            team_id: Filtrer par équipe (optionnel)
            
        Returns:
            Liste des joueurs
        """
        params = {}
        if team_id:
            params["team"] = team_id
            
        return self.request("players", params)
    
    def get_player(self, player_id: int) -> Dict[str, Any]:
        """Récupère les informations d'un joueur spécifique.
        
        Args:
            player_id: Identifiant du joueur
            
        Returns:
            Données du joueur
        """
        return self.request(f"players/{player_id}")
    
    def get_standings(self, conference: Optional[str] = None) -> Dict[str, Any]:
        """Récupère les classements actuels.
        
        Args:
            conference: Filtrer par conférence ("east"/"west") (optionnel)
            
        Returns:
            Données des classements
        """
        params = {}
        if conference:
            params["conference"] = conference
            
        return self.request("standings", params)


def get_api_client() -> NBAApiClient:
    """Récupère ou crée une instance du client API.
    
    Returns:
        Instance du client API
    """
    if 'api_client' not in g:
        g.api_client = NBAApiClient(
            api_key=current_app.config['RAPIDAPI_KEY'],
            api_host=current_app.config['RAPIDAPI_HOST'],
            cache_timeout=current_app.config['CACHE_TIMEOUT']
        )
    return g.api_client
