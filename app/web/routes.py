"""Routes principales pour l'application web Momentrix NBA Analytics.

Ce module définit les endpoints principaux de l'interface web.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from datetime import datetime

from app.data.database import get_db_connection
from app.api.client import get_api_client
from app.analysis.badges import BadgeManager

# Création du blueprint pour les routes principales
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Page d'accueil / Dashboard principal."""
    db = get_db_connection()
    api_client = get_api_client()
    
    # Récupérer les matchs récents (5 derniers)
    recent_games = db.get_recent_games(limit=5)
    
    # Récupérer les matchs à venir (3 prochains)
    upcoming_games = db.get_upcoming_games(limit=3)
    
    # Récupérer les équipes avec les meilleures performances
    top_teams = db.get_top_performing_teams(limit=4)
    
    # Récupérer les badges récemment attribués
    recent_badges = db.get_recent_badges(limit=8)
    
    # Préparer les données pour le graphique de performance par quart-temps
    quarter_performance_data = {
        'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
        'home_team_data': [25.3, 24.8, 27.1, 26.4],  # Données d'exemple
        'away_team_data': [23.7, 25.2, 24.6, 25.1]   # Données d'exemple
    }
    
    # Préparer les données pour l'analyse des quart-temps
    quarter_analysis = {
        'strongest_q4': [
            {'team': 'Boston Celtics', 'differential': 4.8},
            {'team': 'Phoenix Suns', 'differential': 3.9}
        ]
    }
    
    return render_template('dashboard/index.html',
                          recent_games=recent_games,
                          upcoming_games=upcoming_games,
                          top_teams=top_teams,
                          recent_badges=recent_badges,
                          quarter_performance_data=quarter_performance_data,
                          quarter_analysis=quarter_analysis,
                          last_update=datetime.now().strftime('%Y-%m-%d'))

@main_bp.route('/teams')
def teams():
    """Page listant toutes les équipes."""
    db = get_db_connection()
    api_client = get_api_client()
    
    # Récupérer les filtres
    conference = request.args.get('conference', 'all')
    division = request.args.get('division', 'all')
    sort_by = request.args.get('sort', 'wins')
    
    # Récupérer les équipes avec filtres
    teams = db.get_teams(conference=conference if conference != 'all' else None,
                        division=division if division != 'all' else None)
    
    # Trier les équipes
    if sort_by == 'wins':
        teams.sort(key=lambda x: x.wins, reverse=True)
    elif sort_by == 'losses':
        teams.sort(key=lambda x: x.losses)
    elif sort_by == 'name':
        teams.sort(key=lambda x: x.name)
    
    # Récupérer les badges pour chaque équipe
    team_badges = {}
    badge_manager = BadgeManager(db)
    
    for team in teams:
        team_badges[team.id] = db.get_team_badges(team.id, active_only=True)
    
    return render_template('teams/index.html',
                          teams=teams,
                          team_badges=team_badges,
                          conference=conference,
                          division=division,
                          sort_by=sort_by)

@main_bp.route('/teams/<int:team_id>')
def team_detail(team_id):
    """Page de détail d'une équipe spécifique."""
    db = get_db_connection()
    api_client = get_api_client()
    
    # Récupérer les informations de l'équipe
    team = db.get_team(team_id)
    if not team:
        flash("Équipe non trouvée.", "danger")
        return redirect(url_for('main.teams'))
    
    # Récupérer les badges de l'équipe
    badges = db.get_team_badges(team_id)
    
    # Récupérer le profil de performance par quart-temps
    from app.analysis.quarters import QuarterAnalysis
    quarter_analyzer = QuarterAnalysis(db, api_client)
    quarter_profile = quarter_analyzer.get_team_quarter_profile(team_id)
    
    # Récupérer l'analyse de momentum
    momentum_analysis = quarter_analyzer.analyze_momentum_patterns(team_id)
    
    # Récupérer les matchs récents
    recent_games = db.get_team_recent_games(team_id, limit=10)
    
    # Récupérer le roster des joueurs
    players = db.get_team_players(team_id)
    
    return render_template('teams/detail.html',
                          team=team,
                          badges=badges,
                          quarter_profile=quarter_profile,
                          momentum_analysis=momentum_analysis,
                          recent_games=recent_games,
                          players=players)

@main_bp.route('/players')
def players():
    """Page listant tous les joueurs."""
    db = get_db_connection()
    
    # Récupérer les filtres
    team_id = request.args.get('team_id', type=int)
    position = request.args.get('position')
    sort_by = request.args.get('sort', 'name')
    
    # Récupérer les joueurs avec filtres
    players = db.get_players(team_id=team_id, position=position)
    
    # Trier les joueurs
    if sort_by == 'name':
        players.sort(key=lambda x: x.name)
    
    # Récupérer toutes les équipes pour le filtre
    teams = db.get_teams()
    
    return render_template('players/index.html',
                          players=players,
                          teams=teams,
                          selected_team=team_id,
                          selected_position=position,
                          sort_by=sort_by)

@main_bp.route('/players/<int:player_id>')
def player_detail(player_id):
    """Page de détail d'un joueur spécifique."""
    db = get_db_connection()
    
    # Récupérer les informations du joueur
    player = db.get_player(player_id)
    if not player:
        flash("Joueur non trouvé.", "danger")
        return redirect(url_for('main.players'))
    
    # Récupérer l'équipe du joueur
    team = db.get_team(player.team_id)
    
    # Récupérer les statistiques récentes du joueur
    # Cette fonctionnalité sera développée ultérieurement
    
    return render_template('players/detail.html',
                          player=player,
                          team=team)

@main_bp.route('/predictions')
def predictions():
    """Page des prédictions de matchs."""
    db = get_db_connection()
    
    # Récupérer les matchs à venir
    upcoming_games = db.get_upcoming_games(limit=10)
    
    # Récupérer les prédictions existantes pour ces matchs
    predictions = {}
    for game in upcoming_games:
        prediction = db.get_prediction(game.id)
        if prediction:
            predictions[game.id] = prediction
    
    # Récupérer l'historique des prédictions passées
    past_predictions = db.get_past_predictions(limit=10)
    
    # Calculer le taux de réussite
    correct_predictions = sum(1 for p in past_predictions if p.is_accurate)
    success_rate = (correct_predictions / len(past_predictions)) * 100 if past_predictions else 0
    
    return render_template('predictions/index.html',
                          upcoming_games=upcoming_games,
                          predictions=predictions,
                          past_predictions=past_predictions,
                          success_rate=success_rate)

@main_bp.route('/analytics')
def analytics():
    """Page d'analyses comparatives."""
    db = get_db_connection()
    
    # Récupérer toutes les équipes pour les sélecteurs
    teams = db.get_teams()
    
    return render_template('analytics/index.html',
                          teams=teams)

@main_bp.route('/analytics/compare', methods=['POST'])
def compare_teams():
    """Endpoint API pour la comparaison d'équipes."""
    db = get_db_connection()
    api_client = get_api_client()
    
    data = request.get_json()
    if not data or 'team1_id' not in data or 'team2_id' not in data:
        return jsonify({"error": "Paramètres manquants"}), 400
    
    team1_id = data['team1_id']
    team2_id = data['team2_id']
    
    # Récupérer les informations des équipes
    team1 = db.get_team(team1_id)
    team2 = db.get_team(team2_id)
    
    if not team1 or not team2:
        return jsonify({"error": "Équipe non trouvée"}), 404
    
    # Effectuer l'analyse comparative
    from app.analysis.quarters import QuarterAnalysis
    quarter_analyzer = QuarterAnalysis(db, api_client)
    comparison = quarter_analyzer.compare_quarter_performance(team1_id, team2_id)
    
    return jsonify(comparison)

@main_bp.route('/badges')
def badges():
    """Page des badges de performance."""
    db = get_db_connection()
    badge_manager = BadgeManager(db)
    
    # Récupérer les filtres
    category = request.args.get('category', 'all')
    persistence = request.args.get('persistence', 'all')
    
    # Récupérer toutes les définitions de badges
    all_badges = badge_manager.get_all_badges()
    
    # Filtrer les badges selon les critères
    if category != 'all':
        all_badges = {code: info for code, info in all_badges.items() 
                     if info['category'] == category}
    
    if persistence != 'all':
        all_badges = {code: info for code, info in all_badges.items() 
                     if info['persistence'] == persistence}
    
    # Récupérer les équipes avec des badges
    teams_with_badges = db.get_teams_with_badges()
    
    return render_template('badges/index.html',
                          all_badges=all_badges,
                          teams_with_badges=teams_with_badges,
                          selected_category=category,
                          selected_persistence=persistence)

@main_bp.route('/export')
def export():
    """Page d'exportation des données."""
    return render_template('export/index.html')

@main_bp.route('/settings')
def settings():
    """Page de configuration de l'application."""
    return render_template('settings/index.html')

@main_bp.route('/about')
def about():
    """Page d'information sur l'application."""
    return render_template('about/index.html')

@main_bp.app_template_filter('date')
def date_filter(value, format='%d/%m/%Y'):
    """Filtre pour formater les dates dans les templates."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(value, datetime):
        return value.strftime(format)
    return value
