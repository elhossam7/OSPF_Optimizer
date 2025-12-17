"""
Interface Web pour visualiser et contrôler l'optimisation OSPF
API REST + Dashboard simple
"""

from flask import Flask, jsonify, request, render_template_string
import threading
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ospf_optimizer import OSPFOptimizer, OptimizationStrategy

app = Flask(__name__)

# Instance globale de l'optimiseur
optimizer = None
optimization_thread = None

# Template HTML pour le dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>OSPF Optimizer Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { 
            text-align: center; 
            margin-bottom: 30px;
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0,212,255,0.5);
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.2em;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 10px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-running { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
        .status-stopped { background: #ff4444; }
        .status-simulation { background: #ffaa00; }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .metric-value { font-weight: bold; color: #00d4ff; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
            transition: all 0.3s;
        }
        .btn-primary { background: #00d4ff; color: #1a1a2e; }
        .btn-primary:hover { background: #00a8cc; transform: translateY(-2px); }
        .btn-danger { background: #ff4444; color: white; }
        .btn-danger:hover { background: #cc3333; }
        .btn-success { background: #00ff88; color: #1a1a2e; }
        .link-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .link-table th, .link-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .link-table th { color: #00d4ff; }
        .progress-bar {
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s;
        }
        .progress-low { background: #00ff88; }
        .progress-medium { background: #ffaa00; }
        .progress-high { background: #ff6600; }
        .progress-critical { background: #ff4444; }
        .controls { text-align: center; margin: 20px 0; }
        .log-container {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .log-entry { padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .log-info { color: #00d4ff; }
        .log-warning { color: #ffaa00; }
        .log-error { color: #ff4444; }
        .refresh-info { text-align: center; color: #888; font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 OSPF Optimizer Dashboard</h1>
        
        <div class="controls">
            <button class="btn btn-primary" onclick="optimizeOnce()">⚡ Optimiser Maintenant</button>
            <button class="btn btn-success" onclick="startContinuous()">▶ Démarrer Continu</button>
            <button class="btn btn-danger" onclick="stopOptimizer()">⏹ Arrêter</button>
            <button class="btn btn-primary" onclick="refreshData()">🔄 Rafraîchir</button>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📊 État du Système</h2>
                <div id="status-content">
                    <div class="metric">
                        <span>État</span>
                        <span class="metric-value" id="status-state">Chargement...</span>
                    </div>
                    <div class="metric">
                        <span>Mode</span>
                        <span class="metric-value" id="status-mode">-</span>
                    </div>
                    <div class="metric">
                        <span>Routeurs configurés</span>
                        <span class="metric-value" id="status-routers">-</span>
                    </div>
                    <div class="metric">
                        <span>Liens surveillés</span>
                        <span class="metric-value" id="status-links">-</span>
                    </div>
                    <div class="metric">
                        <span>Optimisations effectuées</span>
                        <span class="metric-value" id="status-count">-</span>
                    </div>
                    <div class="metric">
                        <span>Dernière optimisation</span>
                        <span class="metric-value" id="status-last">-</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Dernière Optimisation</h2>
                <div id="last-optimization">
                    <p style="color: #888;">Aucune optimisation effectuée</p>
                </div>
            </div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h2>🔗 État des Liens</h2>
            <table class="link-table">
                <thead>
                    <tr>
                        <th>Lien</th>
                        <th>Utilisation BW</th>
                        <th>Latence</th>
                        <th>Perte</th>
                        <th>Coût Actuel</th>
                        <th>Coût Recommandé</th>
                    </tr>
                </thead>
                <tbody id="links-table-body">
                    <tr><td colspan="6" style="text-align:center; color:#888;">Cliquez sur "Optimiser" pour voir les données</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h2>📝 Logs</h2>
            <div class="log-container" id="logs">
                <div class="log-entry log-info">Dashboard initialisé</div>
            </div>
        </div>
        
        <p class="refresh-info">Auto-refresh toutes les 10 secondes</p>
    </div>
    
    <script>
        function addLog(message, type = 'info') {
            const logs = document.getElementById('logs');
            const entry = document.createElement('div');
            entry.className = `log-entry log-${type}`;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            logs.insertBefore(entry, logs.firstChild);
            if (logs.children.length > 50) logs.removeChild(logs.lastChild);
        }
        
        function getProgressClass(value) {
            if (value < 30) return 'progress-low';
            if (value < 60) return 'progress-medium';
            if (value < 80) return 'progress-high';
            return 'progress-critical';
        }
        
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('status-state').innerHTML = 
                    `<span class="status-indicator ${data.running ? 'status-running' : 'status-stopped'}"></span>
                     ${data.running ? 'En cours' : 'Arrêté'}`;
                document.getElementById('status-mode').textContent = 
                    data.simulation_mode ? '🔬 Simulation' : '🔧 Production';
                document.getElementById('status-routers').textContent = 
                    data.configured_routers ? data.configured_routers.length : 0;
                document.getElementById('status-links').textContent = data.monitored_links || 0;
                document.getElementById('status-count').textContent = data.optimization_count || 0;
                document.getElementById('status-last').textContent = 
                    data.last_optimization ? new Date(data.last_optimization).toLocaleString() : 'Jamais';
                    
            } catch (error) {
                addLog('Erreur de connexion au serveur', 'error');
            }
        }
        
        async function optimizeOnce() {
            addLog('Lancement de l\\'optimisation...', 'info');
            try {
                const response = await fetch('/api/optimize', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    addLog(`Optimisation terminée: ${data.changes_applied} changements`, 'info');
                    updateLinksTable(data.summary);
                    updateLastOptimization(data);
                } else {
                    addLog(`Erreur: ${data.error}`, 'error');
                }
                refreshData();
            } catch (error) {
                addLog('Erreur lors de l\\'optimisation', 'error');
            }
        }
        
        function updateLinksTable(summary) {
            if (!summary || !summary.all_results) return;
            
            const tbody = document.getElementById('links-table-body');
            tbody.innerHTML = '';
            
            summary.all_results.forEach(result => {
                const bw = result.metrics.bandwidth_utilization;
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${result.link}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill ${getProgressClass(bw)}" style="width: ${bw}%"></div>
                        </div>
                        <small>${bw.toFixed(1)}%</small>
                    </td>
                    <td>${result.metrics.latency_ms.toFixed(1)} ms</td>
                    <td>${result.metrics.packet_loss_percent.toFixed(2)}%</td>
                    <td>${result.current}</td>
                    <td style="color: ${result.will_update ? '#00ff88' : 'inherit'}">${result.calculated} ${result.will_update ? '⚡' : ''}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function updateLastOptimization(data) {
            const container = document.getElementById('last-optimization');
            container.innerHTML = `
                <div class="metric">
                    <span>Durée</span>
                    <span class="metric-value">${data.duration_seconds.toFixed(2)}s</span>
                </div>
                <div class="metric">
                    <span>Changements appliqués</span>
                    <span class="metric-value">${data.changes_applied}</span>
                </div>
                <div class="metric">
                    <span>Liens analysés</span>
                    <span class="metric-value">${data.summary.total_links}</span>
                </div>
            `;
        }
        
        async function startContinuous() {
            addLog('Démarrage du mode continu...', 'info');
            try {
                await fetch('/api/start', { method: 'POST' });
                refreshData();
            } catch (error) {
                addLog('Erreur', 'error');
            }
        }
        
        async function stopOptimizer() {
            addLog('Arrêt de l\\'optimiseur...', 'warning');
            try {
                await fetch('/api/stop', { method: 'POST' });
                refreshData();
            } catch (error) {
                addLog('Erreur', 'error');
            }
        }
        
        // Auto-refresh
        setInterval(refreshData, 10000);
        refreshData();
    </script>
</body>
</html>
"""


def init_optimizer(config_path: str = None, simulation: bool = True):
    """Initialise l'optimiseur global"""
    global optimizer
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'routers.yaml')
    optimizer = OSPFOptimizer(config_path, simulation_mode=simulation)
    return optimizer


@app.route('/')
def dashboard():
    """Page principale du dashboard"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/status')
def get_status():
    """Retourne l'état de l'optimiseur"""
    if optimizer is None:
        return jsonify({'error': 'Optimizer not initialized'}), 500
    return jsonify(optimizer.get_status())


@app.route('/api/optimize', methods=['POST'])
def optimize():
    """Lance une optimisation"""
    if optimizer is None:
        return jsonify({'error': 'Optimizer not initialized'}), 500
    
    strategy = request.args.get('strategy', 'composite')
    dry_run = request.args.get('dry_run', 'false').lower() == 'true'
    
    strategy_map = {
        'composite': OptimizationStrategy.COMPOSITE,
        'bandwidth': OptimizationStrategy.BANDWIDTH_BASED,
        'latency': OptimizationStrategy.LATENCY_BASED
    }
    
    result = optimizer.optimize_once(strategy_map.get(strategy, OptimizationStrategy.COMPOSITE), dry_run)
    return jsonify(result)


@app.route('/api/start', methods=['POST'])
def start_continuous():
    """Démarre l'optimisation continue en arrière-plan"""
    global optimization_thread
    
    if optimizer is None:
        return jsonify({'error': 'Optimizer not initialized'}), 500
    
    if optimizer.running:
        return jsonify({'message': 'Already running'})
    
    interval = int(request.args.get('interval', 60))
    
    def run():
        optimizer.run_continuous(interval=interval, dry_run=False)
    
    optimization_thread = threading.Thread(target=run, daemon=True)
    optimization_thread.start()
    
    return jsonify({'message': 'Started', 'interval': interval})


@app.route('/api/stop', methods=['POST'])
def stop_optimizer():
    """Arrête l'optimisation"""
    if optimizer:
        optimizer.stop()
    return jsonify({'message': 'Stopped'})


@app.route('/api/config')
def get_config():
    """Retourne la configuration actuelle"""
    if optimizer is None:
        return jsonify({'error': 'Optimizer not initialized'}), 500
    return jsonify(optimizer.config)


def run_web_server(host: str = '0.0.0.0', port: int = 5000, 
                   config_path: str = None, simulation: bool = True):
    """
    Lance le serveur web
    
    Args:
        host: Adresse d'écoute
        port: Port d'écoute
        config_path: Chemin vers la configuration
        simulation: Mode simulation
    """
    init_optimizer(config_path, simulation)
    print(f"\n🌐 Dashboard disponible sur http://localhost:{port}\n")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='OSPF Optimizer Web Interface')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Port du serveur')
    parser.add_argument('--config', '-c', default=None, help='Fichier de configuration')
    parser.add_argument('--simulation', '-s', action='store_true', help='Mode simulation')
    
    args = parser.parse_args()
    
    run_web_server(port=args.port, config_path=args.config, simulation=args.simulation)
