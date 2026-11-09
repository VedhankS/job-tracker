import React, { useState } from 'react';
import { useAuth } from '../AuthContext';

export default function CopilotPanel({ job, onSaveToTracker, onJobUpdated }) {
  const { authFetch } = useAuth();
  const [jdText, setJdText] = useState(job?.job_description || '');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  // Check if job already has persisted AI data
  const hasSavedStrategy =
    job && (job.match_score !== null && job.match_score !== undefined || (job.tailored_bullets && job.tailored_bullets.length > 0));

  const runCopilot = async () => {
    if (!jdText.trim()) return;
    setLoading(true);
    setError('');
    setIsSaved(false);

    try {
      // Primary: Use the integrated backend endpoint that orchestrates AI & DB persistence
      const res = await authFetch(`/jobs/${job.id}/copilot`, {
        method: 'POST',
        body: JSON.stringify({ text: jdText.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `AI analysis failed with status ${res.status}`);
      }

      const data = await res.json();
      setResults(data.copilot_results);
      setIsSaved(true);
      if (onJobUpdated) {
        onJobUpdated(data.job);
      }
    } catch (err) {
      // Fallback: If inter-service proxy had an issue, attempt through Nginx gateway /ai route
      try {
        const fallbackRes = await fetch('/ai/agent/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: jdText.trim() }),
        });
        if (!fallbackRes.ok) throw new Error('AI Service unreachable');
        const fallbackData = await fallbackRes.json();
        setResults(fallbackData.copilot_results);
      } catch (fallbackErr) {
        setError(
          err.message.includes('Failed to connect') || err.message.includes('unreachable')
            ? 'Cannot reach AI service or Ollama. Ensure Ollama is running locally (`ollama run llama3.2`).'
            : err.message
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleManualSave = async () => {
    if (!results) return;
    if (onSaveToTracker) {
      await onSaveToTracker(results, jdText);
      setIsSaved(true);
    }
  };

  // Helper to filter out conversational filler, assessment criteria, notes, and number prefixes
  const sanitizeQuestions = (questions) => {
    if (!Array.isArray(questions)) return [];

    const hasFiller = questions.some(
      (q) =>
        typeof q === 'string' &&
        (q.toLowerCase().startsWith('here are') ||
          q.toLowerCase().includes('assessment criteria') ||
          q.trim().startsWith('*') ||
          q.trim().startsWith('-'))
    );

    if (!hasFiller) {
      return questions
        .filter((q) => typeof q === 'string' && q.trim().length > 5)
        .map((q) =>
          q.replace(/^(?:\d+[\.\)]\s*\*?\*?Question\s*[:.-]?\s*\*?\*?|\d+[\.\)]|\*\*Question\s*[:.-]?\s*\*?\*?)\s*/i, '').trim()
        );
    }

    const clean = [];
    let currentQ = '';
    let inCriteria = false;

    for (const raw of questions) {
      if (typeof raw !== 'string') continue;
      const str = raw.trim();
      const lower = str.toLowerCase();

      if (lower.startsWith('here are') || lower.startsWith('note:')) continue;
      if (lower.includes('assessment criteria')) {
        inCriteria = true;
        continue;
      }
      if (str.startsWith('*') || str.startsWith('-')) {
        continue;
      }

      if (/^(?:\d+[\.\)]|\*\*Question|\d+\.\s*\*?\*?Question)/i.test(str)) {
        inCriteria = false;
        if (currentQ) clean.push(currentQ.trim());
        currentQ = str.replace(
          /^(?:\d+[\.\)]\s*\*?\*?Question\s*[:.-]?\s*\*?\*?|\d+[\.\)]|\*\*Question\s*[:.-]?\s*\*?\*?)\s*/i,
          ''
        );
      } else if (!inCriteria && currentQ) {
        currentQ += ' ' + str;
      }
    }
    if (currentQ) clean.push(currentQ.trim());
    return clean;
  };

  // Determine what to display: current run results, or previously saved insights
  const displayScore = results?.match_data?.score ?? job?.match_score;
  const displaySkills = results?.analysis?.required_skills ?? job?.skills;
  const displayBullets = results?.tailored_bullets ?? job?.tailored_bullets;
  const displayQuestions = sanitizeQuestions(results?.prep_questions ?? job?.prep_questions);
  const hasDataToDisplay = results !== null || hasSavedStrategy;

  return (
    <div className="bg-[#f7f2ea] p-5 rounded-lg border border-[#e2d8c8] mt-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-stone-900 font-semibold text-sm">
          AI Application Strategy
        </h3>
        {hasSavedStrategy && !results && (
          <span className="text-xs bg-emerald-100 text-emerald-800 border border-emerald-300 px-2.5 py-0.5 rounded-full font-medium">
            Saved Strategy Available
          </span>
        )}
      </div>

      <div>
        <label className="block text-xs font-medium text-stone-700 mb-1">
          Job Description
        </label>
        <textarea
          className="w-full min-h-[110px] p-3 bg-white border border-[#d6cbba] rounded text-stone-900 text-sm focus:outline-none focus:border-orange-500 placeholder-stone-400"
          placeholder="Paste the job description here to analyze requirements, calculate resume match, tailor bullets, and generate interview prep..."
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={runCopilot}
          disabled={loading || !jdText.trim()}
          className="bg-orange-600 hover:bg-orange-500 disabled:bg-[#dcd4c6] disabled:text-stone-500 font-medium py-2 px-4 rounded text-sm transition text-white flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Analyzing and Matching with Resume...</span>
            </>
          ) : (
            <span>{hasSavedStrategy ? 'Re-generate Strategy' : 'Generate AI Strategy'}</span>
          )}
        </button>

        {isSaved && (
          <span className="text-xs text-emerald-700 font-medium flex items-center gap-1">
            Strategy saved to job profile
          </span>
        )}
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-300 text-rose-800 p-3 rounded text-sm font-medium">
          <strong>Error:</strong> {error}
        </div>
      )}

      {hasDataToDisplay && (
        <div className="mt-4 text-stone-800 text-sm space-y-4 pt-4 border-t border-[#e2d8c8]">
          {/* Match Score & Skills */}
          <div className="bg-white p-4 rounded-md border border-[#e2d8c8] shadow-2xs">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-stone-900">Resume Match Score:</span>
              <span
                className={`font-bold px-3 py-1 rounded text-sm ${
                  (displayScore ?? 0) >= 70
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : (displayScore ?? 0) >= 40
                    ? 'bg-amber-100 text-amber-800 border border-amber-300'
                    : 'bg-rose-100 text-rose-800 border border-rose-300'
                }`}
              >
                {displayScore ?? 0} / 100
              </span>
            </div>

            {displaySkills && displaySkills.length > 0 && (
              <div className="mt-2 text-xs">
                <span className="text-stone-700 font-semibold">Required Skills: </span>
                <span className="text-stone-600">{displaySkills.join(', ')}</span>
              </div>
            )}
          </div>

          {/* Tailored Bullets */}
          {displayBullets && displayBullets.length > 0 && (
            <div className="bg-white p-4 rounded-md border border-[#e2d8c8] shadow-2xs">
              <h4 className="font-semibold text-stone-900 mb-2 text-xs uppercase tracking-wider">
                Tailored Resume Bullets
              </h4>
              <ul className="list-disc pl-5 space-y-2 text-stone-700">
                {displayBullets.map((b, i) => {
                  const bulletText = typeof b === 'string' ? b : b.bullet;
                  const sourceId = typeof b === 'object' && b?.source_chunk_id ? b.source_chunk_id : null;
                  return (
                    <li key={i}>
                      <span>{bulletText}</span>
                      {sourceId && (
                        <span className="block text-xs text-stone-400 mt-0.5 font-mono">
                          Source citation: {sourceId}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Interview Prep Questions */}
          {displayQuestions && displayQuestions.length > 0 && (
            <div className="bg-white p-4 rounded-md border border-[#e2d8c8] shadow-2xs">
              <h4 className="font-semibold text-stone-900 mb-2 text-xs uppercase tracking-wider">
                Technical Interview Prep
              </h4>
              <ul className="list-decimal pl-5 space-y-2 text-stone-700">
                {displayQuestions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}

          {results && !isSaved && (
            <button
              onClick={handleManualSave}
              className="w-full bg-stone-900 hover:bg-stone-800 font-medium py-2 rounded text-sm transition text-white mt-2"
            >
              Save Strategy to Application
            </button>
          )}
        </div>
      )}
    </div>
  );
}
