 import React, { useState, useEffect } from 'react';
import BenchmarkCharts from './BenchmarkCharts.jsx';
import RouteRecommender from './RouteRecommender.jsx';
import SupplierIntelligence from './SupplierIntelligence.jsx';
import RouteHistory from './RouteHistory.jsx';

export default function App() {
  const [network, setNetwork] = useState({ nodes: [], edges: [] });
  const [status, setStatus] = useState(null);
  const [currentView, setCurrentView] = useState('recommend');
  const [selectedHistory, setSelectedHistory] = useState(null);

  useEffect(() => {
    fetch('/api/network')
      .then(r => r.json())
      .then(data => setNetwork(data))
      .catch(e => console.error(e));

    const protocol =
      window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    const wsUrl = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const state = JSON.parse(event.data);
      setStatus(state);
    };

    return () => ws.close();
  }, []);

  const restoreHistoryEntry = (entry) => {
    setSelectedHistory(entry);
    setCurrentView('recommend');
  };

  return (
    <>
      {/* =========================================
          ROUTE RECOMMENDER
          Kept mounted so its React state survives
          navigation to other views.
          ========================================= */}
      <div
        style={{
          display: currentView === 'recommend' ? 'block' : 'none',
          height: '100%',
        }}
      >
        <RouteRecommender
          onNavigate={setCurrentView}
          restoreEntry={selectedHistory}
          onRestoreConsumed={() => setSelectedHistory(null)}
        />
      </div>

      {/* =========================================
          SUPPLIER INTELLIGENCE
          ========================================= */}
      <div
        style={{
          display: currentView === 'suppliers' ? 'block' : 'none',
          height: '100%',
        }}
      >
        <SupplierIntelligence
          onNavigate={setCurrentView}
        />
      </div>

      {/* =========================================
          BENCHMARK
          ========================================= */}
      <div
        style={{
          display: currentView === 'benchmark' ? 'block' : 'none',
          height: '100%',
        }}
      >
        <BenchmarkCharts
          onBack={() => setCurrentView('recommend')}
        />
      </div>

      {/* =========================================
          ROUTE HISTORY
          ========================================= */}
      <div
        style={{
          display: currentView === 'history' ? 'block' : 'none',
          height: '100%',
        }}
      >
        <RouteHistory
          onNavigate={setCurrentView}
          onRestore={restoreHistoryEntry}
        />
      </div>

      {/* =========================================
          SYSTEM CONSOLE
          ========================================= */}
      <div
        style={{
          display: currentView === 'system' ? 'block' : 'none',
          height: '100%',
        }}
      >
        <div className="dashboard-container">

          {/* Keep your existing System Console
              markup here exactly as it currently is. */}

          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">
                SYSTEM CONSOLE
              </h2>
            </div>

            <div className="panel-content">
              <div className="status-grid">

                <div className="status-card">
                  <div className="status-label">
                    NETWORK
                  </div>

                  <div className="status-value">
                    {network?.nodes?.length || 0} NODES
                  </div>
                </div>

                <div className="status-card">
                  <div className="status-label">
                    CONNECTION
                  </div>

                  <div className="status-value">
                    {status ? 'ONLINE' : 'CONNECTING'}
                  </div>
                </div>

              </div>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}