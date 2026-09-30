import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Clock3,
  History,
  Trash2,
  Route,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';

const STORAGE_KEY = 'supplychainer.routeHistory.v1';

export const ROUTE_HISTORY_KEY = STORAGE_KEY;

/* =========================================
   LOAD HISTORY
   ========================================= */
export function loadRouteHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);

    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.error('Failed to load route history:', error);
    return [];
  }
}

/* =========================================
   SAVE HISTORY
   ========================================= */
export function saveRouteHistory(entry) {
  try {
    const current = loadRouteHistory();

    const next = [
      entry,
      ...current.filter(item => item.id !== entry.id),
    ].slice(0, 25);

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(next)
    );

    window.dispatchEvent(
      new CustomEvent('route-history-updated')
    );

    return next;
  } catch (error) {
    console.error('Failed to save route history:', error);

    return loadRouteHistory();
  }
}

/* =========================================
   CLEAR HISTORY
   ========================================= */
export function clearRouteHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);

    window.dispatchEvent(
      new CustomEvent('route-history-updated')
    );
  } catch (error) {
    console.error('Failed to clear route history:', error);
  }
}

/* =========================================
   DATE FORMATTER
   ========================================= */
const formatDate = (value) => {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value));
  } catch {
    return value;
  }
};

/* =========================================
   ROUTE HISTORY COMPONENT
   ========================================= */
export default function RouteHistory({
  onNavigate,
  onRestore,
}) {
  const [history, setHistory] = useState([]);

  /* -----------------------------------------
     Refresh history from localStorage
     ----------------------------------------- */
  const refresh = () => {
    setHistory(loadRouteHistory());
  };

  /* -----------------------------------------
     Listen for history changes
     ----------------------------------------- */
  useEffect(() => {
    refresh();

    const handleHistoryUpdate = () => {
      refresh();
    };

    window.addEventListener(
      'route-history-updated',
      handleHistoryUpdate
    );

    window.addEventListener(
      'storage',
      handleHistoryUpdate
    );

    return () => {
      window.removeEventListener(
        'route-history-updated',
        handleHistoryUpdate
      );

      window.removeEventListener(
        'storage',
        handleHistoryUpdate
      );
    };
  }, []);

  /* -----------------------------------------
     Delete one history entry
     ----------------------------------------- */
  const removeEntry = (id) => {
    const next = history.filter(
      item => item.id !== id
    );

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(next)
    );

    setHistory(next);

    window.dispatchEvent(
      new CustomEvent('route-history-updated')
    );
  };

  /* -----------------------------------------
     Clear all history
     ----------------------------------------- */
  const handleClear = () => {
    if (!history.length) {
      return;
    }

    clearRouteHistory();
    setHistory([]);
  };

  return (
    <div
      className="dashboard-container"
      style={{
        gridTemplateColumns: '1fr',
      }}
    >
      <div
        className="panel"
        style={{
          minHeight: '100%',
        }}
      >

        {/* =====================================
            HEADER
            ===================================== */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.5rem',
            gap: '1rem',
          }}
        >

          <div>
            <h2
              className="panel-title"
              style={{
                marginBottom: '0.35rem',
              }}
            >
              <History size={15} />
              Route History
            </h2>

            <p
              style={{
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                margin: 0,
              }}
            >
              Previous route decisions are retained
              locally so your operational workspace
              is not lost when navigating between views.
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              gap: '0.75rem',
            }}
          >

            {/* BACK */}
            <button
              className="dispatch-btn"
              onClick={() =>
                onNavigate('recommend')
              }
            >
              <ArrowLeft size={14} />
              Back to Route Recommender
            </button>

            {/* CLEAR */}
            <button
              className="dispatch-btn"
              onClick={handleClear}
              disabled={!history.length}
              style={{
                background: history.length
                  ? '#7f1d1d'
                  : undefined,
              }}
            >
              <Trash2 size={14} />
              Clear History
            </button>

          </div>
        </div>

        {/* =====================================
            EMPTY STATE
            ===================================== */}
        {!history.length ? (

          <div
            style={{
              textAlign: 'center',
              padding: '5rem 1rem',
              color: 'var(--text-muted)',
            }}
          >

            <Route
              size={48}
              style={{
                opacity: 0.12,
                marginBottom: '1rem',
              }}
            />

            <p
              style={{
                fontWeight: 700,
                color: 'white',
              }}
            >
              No route decisions yet
            </p>

            <p
              style={{
                fontSize: '0.8rem',
              }}
            >
              Generate a route from the Route
              Recommender and it will appear here
              automatically.
            </p>

          </div>

        ) : (

          /* =====================================
             HISTORY LIST
             ===================================== */
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >

            {history.map((entry) => {

              const fastest =
                entry.recommendations?.find(
                  recommendation =>
                    recommendation.persona === 'FASTEST'
                ) ||
                entry.recommendations?.[0];

              const displayedCost =
                fastest?.display_total_cost ??
                fastest?.total_cost;

              const displayedCurrency =
                fastest?.display_currency ??
                entry.currency ??
                'USD';

              const currencySymbol =
                fastest?.currency_symbol ?? '';

              return (
                <div
                  key={entry.id}
                  className="decision-card"
                  style={{
                    display: 'grid',
                    gridTemplateColumns:
                      '1fr auto',
                    gap: '1rem',
                    alignItems: 'center',
                  }}
                >

                  {/* ==============================
                      ROUTE INFORMATION
                      ============================== */}
                  <div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.6rem',
                        marginBottom: '0.45rem',
                        flexWrap: 'wrap',
                      }}
                    >

                      <Route
                        size={15}
                        color="#3b82f6"
                      />

                      <strong
                        style={{
                          color: 'white',
                        }}
                      >
                        {entry.origin_display ||
                          entry.source}
                      </strong>

                      <span
                        style={{
                          color: '#64748b',
                        }}
                      >
                        →
                      </span>

                      <strong
                        style={{
                          color: 'white',
                        }}
                      >
                        {entry.destination_display ||
                          entry.destination}
                      </strong>

                    </div>

                    {/* ==============================
                        ROUTE METADATA
                        ============================== */}
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.8rem',
                        color: '#94a3b8',
                        fontSize: '0.7rem',
                      }}
                    >

                      <span>
                        <Clock3
                          size={11}
                          style={{
                            verticalAlign:
                              'middle',
                          }}
                        />{' '}
                        {formatDate(
                          entry.created_at
                        )}
                      </span>

                      <span>
                        Mode:{' '}
                        {entry.transportMode
                          ?.toUpperCase() ||
                          'ANY'}
                      </span>

                      <span>
                        Policy:{' '}
                        {entry.routingPolicy ||
                          'STRICT'}
                      </span>

                      {entry.cargoType && (
                        <span>
                          Cargo:{' '}
                          {entry.cargoType}
                        </span>
                      )}

                      {entry.priority && (
                        <span>
                          Priority:{' '}
                          {entry.priority}
                        </span>
                      )}

                      {entry.active_scenario && (
                        <span
                          style={{
                            color: '#f59e0b',
                          }}
                        >
                          <AlertTriangle
                            size={11}
                            style={{
                              verticalAlign:
                                'middle',
                            }}
                          />{' '}
                          {entry.active_scenario}
                        </span>
                      )}

                    </div>

                    {/* ==============================
                        FASTEST ROUTE SUMMARY
                        ============================== */}
                    {fastest && (

                      <div
                        style={{
                          marginTop: '0.65rem',
                          fontSize: '0.75rem',
                          display: 'flex',
                          flexWrap: 'wrap',
                          gap: '0.25rem',
                        }}
                      >

                        <span
                          style={{
                            color: '#64748b',
                          }}
                        >
                          FASTEST
                        </span>

                        <strong>
                          {fastest.adjusted_eta}h
                        </strong>

                        <span
                          style={{
                            color: '#64748b',
                            marginLeft: '1rem',
                          }}
                        >
                          COST
                        </span>

                        <strong
                          style={{
                            color: '#10b981',
                          }}
                        >
                          {currencySymbol}
                          {typeof displayedCost ===
                          'number'
                            ? displayedCost.toLocaleString()
                            : displayedCost}{' '}
                          {displayedCurrency}
                        </strong>

                        <span
                          style={{
                            color: '#64748b',
                            marginLeft: '1rem',
                          }}
                        >
                          RISK
                        </span>

                        <strong>
                          {Math.round(
                            (fastest.threat_level ||
                              0) * 100
                          )}
                          %
                        </strong>

                      </div>

                    )}

                  </div>

                  {/* ==============================
                      ACTIONS
                      ============================== */}
                  <div
                    style={{
                      display: 'flex',
                      gap: '0.5rem',
                    }}
                  >

                    {/* RESTORE */}
                    <button
                      className="dispatch-btn"
                      onClick={() =>
                        onRestore(entry)
                      }
                    >
                      <RotateCcw size={13} />
                      Restore
                    </button>

                    {/* DELETE */}
                    <button
                      className="dispatch-btn"
                      aria-label="Delete route history entry"
                      title="Delete route"
                      onClick={() =>
                        removeEntry(entry.id)
                      }
                      style={{
                        padding: '0.65rem',
                      }}
                    >
                      <Trash2 size={13} />
                    </button>

                  </div>

                </div>
              );
            })}

          </div>
        )}

      </div>
    </div>
  );
}