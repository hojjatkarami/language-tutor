import { useState, useEffect } from 'react';
import './App.css';

interface LevelStats {
  total: number;
  practiced: number;
}

interface LessonInfo {
  id: string;
  title: string;
  level: string;
  times_practiced: number;
  quizzes_practiced: number;
  quiz_correct_answers: number;
  active_mistakes_count: number;
  last_practiced: string | null;
}

interface IncorrectQuestion {
  quiz_id: string;
  lesson_id: string;
  lesson_title: string;
  timestamp: string;
  user_answer: string;
  correct_answer: string;
  question_text: string;
  options: Record<string, string>;
}

interface NeedsPracticeLesson {
  id: string;
  title: string;
  level: string;
  active_mistakes_count: number;
  reason: 'mistake' | 'unpracticed';
}

interface ProgressStats {
  current_level: string;
  total_lessons_count: number;
  practiced_lessons_count: number;
  unresolved_mistakes_count: number;
  total_quizzes_practiced: number;
  total_quiz_correct_answers: number;
  accuracy_rate: number;
  levels_breakdown: Record<string, LevelStats>;
  lessons: LessonInfo[];
  incorrect_questions_history: IncorrectQuestion[];
  needs_practice_lessons: NeedsPracticeLesson[];
  saved_phrases: Record<string, Array<{ french: string; english: string; saved_at: string; type?: string }>>;
}

const CONTEXT_TITLES: Record<string, string> = {
  supermarket: "Au supermarché (Migros / Coop)",
  bank: "À la banque (Banque cantonale / Bancomat)",
  post_office: "À l'office de poste (La Poste)",
  municipality: "À la commune (Contrôle des habitants)",
  train: "Prendre le train (CFF / À la gare)",
  nature: "Dans la nature (Randonnée / Lacs / Montagne)",
  general: "Vocabulaire général & Expressions diverses"
};

function App() {
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState('All');

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch stats from local backend API
      const response = await fetch('/api/stats');
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to fetch stats:', err);
      setError(err?.message || 'Failed to connect to the progress API server. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="loading-container" id="loading-spinner">
        <div className="spinner"></div>
        <p>Loading your learning statistics...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="error-container" id="error-screen">
        <div className="error-card">
          <div className="error-icon">⚠️</div>
          <h2>Connection Error</h2>
          <p>{error || 'An unexpected error occurred while loading your profile.'}</p>
          <button className="retry-button" onClick={fetchStats} id="retry-btn">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Filter lessons based on search and level filter
  const filteredLessons = stats.lessons.filter((lesson) => {
    const matchesSearch = lesson.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesLevel = levelFilter === 'All' || lesson.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  // Calculate Accuracy Percentage
  const accuracyPercent = stats.total_quizzes_practiced > 0
    ? Math.round((stats.total_quiz_correct_answers / stats.total_quizzes_practiced) * 100)
    : 0;

  // Format timestamp helper
  const formatDate = (isoString: string | null) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="dashboard-container">
      {/* Header Section */}
      <header>
        <div className="header-title-section">
          <h1>French Progress Analytics</h1>
          <p>Real-time visual insights into your grammar and preposition achievements</p>
        </div>
        <div className="user-badge" id="user-badge">
          <div className="user-avatar">FR</div>
          <div className="user-info-text">
            <h3>French Student</h3>
            <span>LEVEL {stats.current_level}</span>
          </div>
        </div>
      </header>

      {/* KPI Stats Grid */}
      <section className="kpis-grid" aria-label="Key Performance Indicators">
        <div className="kpi-card lessons" id="kpi-lessons">
          <div className="kpi-icon">📚</div>
          <div className="kpi-details">
            <span>Lessons Completed</span>
            <h2>{stats.practiced_lessons_count} <small style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ {stats.total_lessons_count}</small></h2>
          </div>
        </div>

        <div className="kpi-card mistakes" id="kpi-mistakes">
          <div className="kpi-icon">❌</div>
          <div className="kpi-details">
            <span>Active Mistakes</span>
            <h2>{stats.unresolved_mistakes_count}</h2>
          </div>
        </div>

        <div className="kpi-card quizzes" id="kpi-quizzes">
          <div className="kpi-icon">✍️</div>
          <div className="kpi-details">
            <span>Quizzes Practiced</span>
            <h2>{stats.total_quizzes_practiced}</h2>
          </div>
        </div>

        <div className="kpi-card accuracy" id="kpi-accuracy">
          <div className="kpi-icon">🎯</div>
          <div className="kpi-details">
            <span>Quiz Accuracy</span>
            <h2>{accuracyPercent}%</h2>
          </div>
        </div>
      </section>

      {/* Level Completion Section */}
      <section className="glass-panel" id="levels-progress-panel" aria-label="Progress by Level">
        <div className="panel-header">
          <h2>📊 Completion by Level</h2>
        </div>
        <div className="levels-grid">
          {Object.entries(stats.levels_breakdown).map(([level, info]) => {
            const pct = info.total > 0 ? Math.round((info.practiced / info.total) * 100) : 0;
            const strokeDashoffset = 251.2 - (251.2 * pct) / 100;
            const isActive = level === stats.current_level;

            return (
              <div
                key={level}
                className={`level-progress-card ${isActive ? 'active-level' : ''}`}
                id={`level-card-${level.toLowerCase()}`}
              >
                <span className="level-badge">{level}</span>
                <div className="level-progress-ring">
                  <svg width="90" height="90">
                    <circle className="level-progress-ring-bg" cx="45" cy="45" r="40" />
                    <circle
                      className="level-progress-ring-fill"
                      cx="45"
                      cy="45"
                      r="40"
                      style={{ strokeDashoffset, stroke: isActive ? 'var(--accent-primary)' : 'var(--color-info)' }}
                    />
                  </svg>
                  <div className="level-progress-percentage">{pct}%</div>
                </div>
                <div className="level-lessons-count">
                  {info.practiced} / {info.total} Lessons
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Main Split Grid */}
      <div className="main-grid">
        {/* Left Column: Lesson Directory */}
        <section className="glass-panel" id="lessons-directory-panel" aria-label="Lesson Directory">
          <div className="panel-header">
            <h2>📖 Lesson Directory</h2>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Showing {filteredLessons.length} lessons</span>
          </div>

          <div className="controls-bar">
            <input
              type="text"
              placeholder="Search lessons by title..."
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              id="search-lessons-input"
            />
            <select
              className="filter-select"
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              id="filter-level-select"
            >
              <option value="All">All Levels</option>
              <option value="A1">A1 Level</option>
              <option value="A2">A2 Level</option>
              <option value="B1">B1 Level</option>
              <option value="B2">B2 Level</option>
              <option value="Prepositions">Prepositions</option>
            </select>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Lesson Title</th>
                  <th>Times Practiced</th>
                  <th>Quiz Attempts</th>
                  <th>Active Mistakes</th>
                  <th>Last Practiced</th>
                </tr>
              </thead>
              <tbody>
                {filteredLessons.length > 0 ? (
                  filteredLessons.map((lesson) => (
                    <tr key={lesson.id} id={`lesson-row-${lesson.id}`}>
                      <td>
                        <span className={`table-level-badge level-${lesson.level.toLowerCase()}`}>
                          {lesson.level}
                        </span>
                      </td>
                      <td style={{ fontWeight: '600' }}>{lesson.title}</td>
                      <td>
                        <span className={`practice-badge ${lesson.times_practiced > 0 ? 'some' : 'zero'}`}>
                          {lesson.times_practiced}x
                        </span>
                      </td>
                      <td className="quiz-count-badge">{lesson.quizzes_practiced}</td>
                      <td>
                        <span className={`mistake-badge ${lesson.active_mistakes_count > 0 ? 'has' : 'none'}`}>
                          {lesson.active_mistakes_count}
                        </span>
                      </td>
                      <td className="last-practiced-time">{formatDate(lesson.last_practiced)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '3rem' }}>
                      <div className="empty-state">
                        <div className="empty-state-icon">🔍</div>
                        <h3>No Lessons Found</h3>
                        <p>No lessons match your search criteria. Try a different query or level filter.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Right Column: Recommendations & Mistakes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Practice Recommendations */}
          <section className="glass-panel" id="recommendations-panel" aria-label="Practice Recommendations">
            <div className="panel-header">
              <h2>💡 Recommended Next</h2>
            </div>
            <div className="action-items-list">
              {stats.needs_practice_lessons.length > 0 ? (
                stats.needs_practice_lessons.map((item) => (
                  <div
                    key={item.id}
                    className={`action-card ${item.reason === 'mistake' ? 'mistake-reason' : 'unpracticed-reason'}`}
                    id={`recommend-card-${item.id}`}
                  >
                    <div className="action-left">
                      <span className="action-level">{item.level}</span>
                      <span className="action-title">{item.title}</span>
                      <span className="action-reason">
                        {item.reason === 'mistake'
                          ? `Contains ${item.active_mistakes_count} unresolved quiz mistake(s)`
                          : 'Not practiced yet (Current Level target)'}
                      </span>
                    </div>
                    <span className="action-badge">
                      {item.reason === 'mistake' ? 'REVIEW' : 'START'}
                    </span>
                  </div>
                ))
              ) : (
                <div className="empty-state" style={{ padding: '1.5rem' }}>
                  <div className="empty-state-icon">🎉</div>
                  <h3>All Caught Up!</h3>
                  <p>You have practiced all lessons for your level and have no active mistakes. Bravo!</p>
                </div>
              )}
            </div>
          </section>

          {/* Active Mistakes Breakdown */}
          <section className="glass-panel" id="mistakes-reviewer-panel" aria-label="Active Mistakes Reviewer">
            <div className="panel-header">
              <h2>📝 Active Mistakes Reviewer</h2>
              <span className="mistake-badge has" style={{ borderRadius: '4px', fontSize: '0.75rem' }}>
                {stats.unresolved_mistakes_count} Wrong
              </span>
            </div>
            <div className="mistakes-timeline">
              {stats.incorrect_questions_history.length > 0 ? (
                stats.incorrect_questions_history.map((q) => (
                  <div key={q.quiz_id} className="mistake-history-card" id={`mistake-card-${q.quiz_id}`}>
                    <div className="mistake-history-header">
                      <span className="mistake-lesson-title">{q.lesson_title}</span>
                      <span className="mistake-timestamp">{formatDate(q.timestamp)}</span>
                    </div>
                    <div className="mistake-question">{q.question_text}</div>

                    <div className="mistake-options-grid">
                      {Object.entries(q.options).map(([key, val]) => {
                        const isUserAnswer = q.user_answer === key;
                        const isCorrectAnswer = q.correct_answer === key;

                        return (
                          <div
                            key={key}
                            className={`mistake-option ${isUserAnswer ? 'selected' : ''} ${isCorrectAnswer ? 'correct' : ''}`}
                          >
                            <strong>{key}.</strong> {val}
                          </div>
                        );
                      })}
                    </div>

                    <div className="mistake-answers-diff">
                      <div className="answer-comparison user-wrong">
                        ❌ Your Answer: <strong>{q.user_answer}</strong>
                      </div>
                      <div className="answer-comparison correct-right">
                        ✓ Correct: <strong>{q.correct_answer}</strong>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state" style={{ padding: '1.5rem' }}>
                  <div className="empty-state-icon">🌟</div>
                  <h3>No Active Mistakes</h3>
                  <p>You have resolved all quiz mistakes! Take more quizzes to test your skills.</p>
                </div>
              )}
            </div>
          </section>

          {/* Saved Phrases by Context */}
          <section className="glass-panel" id="saved-phrases-panel" aria-label="Saved Phrases by Context">
            <div className="panel-header">
              <h2>💾 Saved Phrases by Context</h2>
            </div>
            <div className="saved-phrases-list" style={{ maxHeight: '400px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {stats.saved_phrases && Object.keys(stats.saved_phrases).some(key => stats.saved_phrases[key]?.length > 0) ? (
                Object.entries(stats.saved_phrases).map(([contextId, phrases]) => {
                  if (!phrases || phrases.length === 0) return null;
                  const title = CONTEXT_TITLES[contextId] || contextId;
                  return (
                    <div key={contextId} className="context-phrases-card" style={{ padding: '1rem', borderLeft: '4px solid var(--accent-primary)', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '4px' }}>
                      <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--accent-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>{title}</span>
                        <span style={{ fontSize: '0.75rem', background: 'rgba(255, 255, 255, 0.1)', padding: '2px 6px', borderRadius: '4px', color: 'var(--text-secondary)' }}>{phrases.length} phrase(s)</span>
                      </h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {phrases.map((phrase, idx) => {
                          const pType = (phrase.type || 'sentence').toLowerCase();
                          let typeColor = '#10b981'; // green for sentence
                          let typeLabel = 'SENTENCE';
                          if (pType === 'word') {
                            typeColor = '#3b82f6'; // blue for word
                            typeLabel = 'VOCAB';
                          } else if (pType === 'block') {
                            typeColor = '#a855f7'; // purple for block
                            typeLabel = 'EXPRESSION';
                          }

                          return (
                            <div key={idx} style={{ paddingBottom: '0.5rem', borderBottom: idx < phrases.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                                <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.95rem' }}>{phrase.french}</div>
                                <span style={{ fontSize: '0.65rem', fontWeight: 'bold', background: typeColor + '20', color: typeColor, border: `1px solid ${typeColor}40`, padding: '1px 6px', borderRadius: '4px', textTransform: 'uppercase', flexShrink: 0 }}>
                                  {typeLabel}
                                </span>
                              </div>
                              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{phrase.english}</div>
                              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'right', marginTop: '4px' }}>Saved: {formatDate(phrase.saved_at)}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="empty-state" style={{ padding: '1.5rem' }}>
                  <div className="empty-state-icon">💡</div>
                  <h3>No Saved Phrases Yet</h3>
                  <p>Start a conversation practice and use 'save' to collect key expressions here.</p>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

export default App;
