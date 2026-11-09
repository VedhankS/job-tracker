import React, { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import CopilotPanel from './CopilotPanel';

export default function Dashboard() {
  const { logout, authFetch } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [loading, setLoading] = useState(true);

  // AI Copilot state
  const [activeCopilotJobId, setActiveCopilotJobId] = useState(null);

  // Resume Manager state
  const [showResumeModal, setShowResumeModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [resumeText, setResumeText] = useState('');
  const [showManualText, setShowManualText] = useState(false);
  const [resumeStatus, setResumeStatus] = useState({ indexed: false, chunk_count: 0 });
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeMessage, setResumeMessage] = useState('');

  const fetchJobs = async () => {
    try {
      const res = await authFetch('/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchResumeStatus = async () => {
    try {
      const res = await authFetch('/resume/status');
      if (res.ok) {
        const data = await res.json();
        setResumeStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch resume status:', err);
    }
  };

  useEffect(() => {
    fetchJobs();
    fetchResumeStatus();
  }, []);

  const handleAddJob = async (e) => {
    e.preventDefault();
    if (!company.trim() || !role.trim()) return;

    const res = await authFetch('/jobs', {
      method: 'POST',
      body: JSON.stringify({ company: company.trim(), role: role.trim() }),
    });
    if (res.ok) {
      setCompany('');
      setRole('');
      fetchJobs();
    }
  };

  const handleStatusChange = async (id, status) => {
    const res = await authFetch(`/jobs/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
    if (res.ok) fetchJobs();
  };

  const handleDeleteJob = async (id) => {
    const res = await authFetch(`/jobs/${id}`, {
      method: 'DELETE',
    });
    if (res.ok) fetchJobs();
  };

  // Bridge function to save AI results to the database
  const handleSaveAIInsights = async (id, aiResults, jdText) => {
    const rawBullets = aiResults.tailored_bullets || [];
    const formattedBullets = rawBullets.map((b) => (typeof b === 'string' ? b : b.bullet));

    const res = await authFetch(`/jobs/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        match_score: aiResults.match_data?.score ?? null,
        tailored_bullets: formattedBullets,
        prep_questions: aiResults.prep_questions || [],
        skills: aiResults.analysis?.required_skills || [],
        job_description: jdText || '',
      }),
    });

    if (res.ok) {
      const updatedJob = await res.json();
      setJobs((prev) => prev.map((j) => (j.id === id ? updatedJob : j)));
      alert('AI strategy saved successfully');
    } else {
      alert('Failed to save AI data.');
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setResumeMessage('Error: Please select a valid .pdf file.');
        return;
      }
      setSelectedFile(file);
      setResumeMessage('');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setResumeMessage('Error: Please drop a valid .pdf file.');
        return;
      }
      setSelectedFile(file);
      setResumeMessage('');
    }
  };

  const handleUploadPdf = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setResumeLoading(true);
    setResumeMessage('');
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await authFetch('/resume/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.error || 'Failed to upload and index PDF resume');
      }

      setResumeMessage(`Successfully parsed "${selectedFile.name}" and indexed ${data.chunks_indexed} resume sections into vector store.`);
      setSelectedFile(null);
      fetchResumeStatus();
    } catch (err) {
      setResumeMessage(`Error: ${err.message}`);
    } finally {
      setResumeLoading(false);
    }
  };

  const handleIndexManualText = async (e) => {
    e.preventDefault();
    if (!resumeText.trim()) return;

    setResumeLoading(true);
    setResumeMessage('');
    try {
      const res = await authFetch('/resume/index', {
        method: 'POST',
        body: JSON.stringify({ text: resumeText.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || 'Failed to index resume text');
      }

      const data = await res.json();
      setResumeMessage(`Successfully indexed ${data.chunks_indexed} resume sections into vector store.`);
      fetchResumeStatus();
    } catch (err) {
      setResumeMessage(`Error: ${err.message}`);
    } finally {
      setResumeLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#faf7f2] text-stone-800 p-6">
      {/* Header */}
      <header className="max-w-4xl mx-auto flex flex-wrap justify-between items-center gap-4 mb-8 pb-4 border-b border-[#e7dfd3]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-orange-600">
            JobTracker
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Resume Manager Button */}
          <button
            onClick={() => setShowResumeModal(!showResumeModal)}
            className="flex items-center gap-2 px-3 py-1.5 bg-[#f3ede2] hover:bg-[#eae2d4] text-stone-800 border border-[#dcd3c4] rounded text-sm font-medium transition"
          >
            <span>Resume PDF</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                resumeStatus.indexed
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : 'bg-amber-100 text-amber-800 border border-amber-300'
              }`}
            >
              {resumeStatus.indexed ? `${resumeStatus.chunk_count} Chunks` : 'Not Uploaded'}
            </span>
          </button>

          {/* Logout Button kept red */}
          <button
            onClick={logout}
            className="px-3 py-1.5 bg-red-600/80 hover:bg-red-500 text-white rounded text-sm font-medium transition"
          >
            Log Out
          </button>
        </div>
      </header>

      {/* Resume Management Modal / Drawer */}
      {showResumeModal && (
        <div className="max-w-4xl mx-auto mb-8 bg-[#f5efe4] border border-[#dcd2c2] rounded-lg p-5 shadow-sm">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-base font-semibold text-stone-900">
              Resume Vector Store
            </h2>
            <button
              onClick={() => setShowResumeModal(false)}
              className="text-stone-500 hover:text-stone-800 text-sm font-medium"
            >
              Close
            </button>
          </div>

          <p className="text-xs text-stone-600 mb-4 leading-relaxed">
            Upload your resume. Text will be extracted, segmented, indexed into ChromaDB for skill matching.
          </p>

          {/* PDF Drag & Drop / File Input */}
          <form onSubmit={handleUploadPdf} className="space-y-4">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-6 text-center transition cursor-pointer ${
                isDragging
                  ? 'border-orange-500 bg-orange-50/70'
                  : selectedFile
                  ? 'border-emerald-500 bg-emerald-50/60'
                  : 'border-[#d4c8b6] hover:border-orange-400 bg-white/70 hover:bg-white'
              }`}
              onClick={() => document.getElementById('resume-pdf-input')?.click()}
            >
              <input
                id="resume-pdf-input"
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
              />

              <div className="flex flex-col items-center justify-center gap-2">
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-semibold text-stone-900">{selectedFile.name}</p>
                    <p className="text-xs text-stone-500 mt-1">
                      {(selectedFile.size / 1024).toFixed(1)} KB - Click to choose a different file
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-stone-800">
                      Click to browse or drag and drop your <span className="text-orange-700 font-semibold">Resume PDF</span> here
                    </p>
                    <p className="text-xs text-stone-500 mt-1">supports .pdf </p>
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={resumeLoading || !selectedFile}
                  className="bg-orange-600 hover:bg-orange-500 disabled:bg-[#dcd4c6] disabled:text-stone-500 font-medium py-2 px-5 rounded text-sm transition text-white flex items-center gap-2"
                >
                  {resumeLoading ? (
                    <>
                      <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                      </svg>
                      <span>Parsing and Vectorizing PDF...</span>
                    </>
                  ) : (
                    <span>Upload and Index PDF</span>
                  )}
                </button>

                {selectedFile && !resumeLoading && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }}
                    className="text-xs text-stone-500 hover:text-red-600 transition"
                  >
                    Clear selection
                  </button>
                )}
              </div>

              <button
                type="button"
                onClick={() => setShowManualText(!showManualText)}
                className="text-xs text-stone-600 hover:text-orange-700 underline transition"
              >
                {showManualText ? 'Hide manual text option' : 'Or paste resume text manually'}
              </button>
            </div>

            {resumeMessage && (
              <div
                className={`text-xs p-3 rounded border font-medium ${
                  resumeMessage.startsWith('Success')
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                    : 'bg-rose-50 border-rose-300 text-rose-800'
                }`}
              >
                {resumeMessage}
              </div>
            )}
          </form>

          {/* Optional manual text fallback */}
          {showManualText && (
            <form onSubmit={handleIndexManualText} className="mt-4 pt-4 border-t border-[#dcd2c2] space-y-3">
              <label className="block text-xs font-medium text-stone-700">
                Fallback: Paste Resume Text Manually
              </label>
              <textarea
                className="w-full min-h-[100px] p-3 bg-white border border-[#d4c8b6] rounded text-stone-900 text-xs focus:outline-none focus:border-orange-500 placeholder-stone-400"
                placeholder="Paste raw resume text here..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
              />
              <button
                type="submit"
                disabled={resumeLoading || !resumeText.trim()}
                className="bg-[#e4dcce] hover:bg-[#d8cebe] text-stone-800 disabled:opacity-50 text-xs font-medium py-1.5 px-3 rounded transition"
              >
                Index Text Instead
              </button>
            </form>
          )}
        </div>
      )}

      <main className="max-w-4xl mx-auto space-y-8">
        {/* Create Job Form */}
        <div className="bg-[#f5efe4] p-6 rounded-lg border border-[#e2d8c8] shadow-sm">
          <h2 className="text-lg font-semibold mb-4 text-stone-900">Track New Application</h2>
          <form onSubmit={handleAddJob} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Company"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="px-3 py-2 bg-white border border-[#d6cbba] rounded text-stone-900 placeholder-stone-400 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 text-sm"
            />
            <input
              type="text"
              placeholder="Role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="px-3 py-2 bg-white border border-[#d6cbba] rounded text-stone-900 placeholder-stone-400 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 text-sm"
            />
            <button
              type="submit"
              className="bg-orange-600 hover:bg-orange-500 font-medium py-2 rounded transition text-white text-sm"
            >
              Add Job
            </button>
          </form>
        </div>

        {/* Job Listings */}
        <div className="bg-white rounded-lg border border-[#e2d8c8] shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-[#f8f4ec] border-b border-[#e2d8c8] flex justify-between items-center">
            <h2 className="text-lg font-semibold text-stone-900">Your Applications</h2>
            <span className="text-xs bg-[#e8e0d2] text-stone-700 px-2.5 py-1 rounded-full font-medium">
              {jobs.length} Active
            </span>
          </div>

          {loading ? (
            <div className="p-6 text-center text-stone-500 text-sm">Loading applications...</div>
          ) : jobs.length === 0 ? (
            <div className="p-6 text-center text-stone-500 text-sm">
              No applications tracked yet. Add your first job above!
            </div>
          ) : (
            <div className="divide-y divide-[#eee7dc]">
              {jobs.map((job) => (
                <div key={job.id} className="flex flex-col">
                  {/* Job Row */}
                  <div className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition hover:bg-[#faf7f2]">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-stone-900">{job.company}</h3>

                        {job.match_score !== null && job.match_score !== undefined && (
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              job.match_score >= 70
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : job.match_score >= 40
                                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                                : 'bg-rose-100 text-rose-800 border border-rose-300'
                            }`}
                          >
                            Match: {job.match_score}%
                          </span>
                        )}

                        {job.tailored_bullets && job.tailored_bullets.length > 0 && (
                          <span className="text-xs bg-orange-100 text-orange-800 border border-orange-200 px-2 py-0.5 rounded-full font-medium">
                            Strategy Saved
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-stone-600 mt-0.5">{job.role}</p>
                    </div>

                    <div className="flex items-center gap-3">
                      <select
                        value={job.status || 'applied'}
                        onChange={(e) => handleStatusChange(job.id, e.target.value)}
                        className="bg-white border border-[#d6cbba] text-stone-800 rounded px-2.5 py-1 text-sm focus:outline-none focus:border-orange-500"
                      >
                        <option value="applied">Applied</option>
                        <option value="interviewing">Interviewing</option>
                        <option value="offered">Offered</option>
                        <option value="rejected">Rejected</option>
                      </select>

                      <button
                        onClick={() =>
                          setActiveCopilotJobId(activeCopilotJobId === job.id ? null : job.id)
                        }
                        className={`text-sm font-medium px-3 py-1 rounded transition border ${
                          activeCopilotJobId === job.id
                            ? 'bg-orange-600 text-white border-orange-600 shadow-2xs'
                            : 'border-orange-400 text-orange-700 bg-white hover:bg-orange-600 hover:text-white hover:border-orange-600'
                        }`}
                      >
                        AI Overview
                      </button>

                      <button
                        onClick={() => handleDeleteJob(job.id)}
                        className="border border-red-400 text-red-600 bg-white hover:bg-red-600 hover:text-white hover:border-red-600 px-3 py-1 text-sm font-medium rounded transition"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {/* AI Copilot Panel Expansion */}
                  {activeCopilotJobId === job.id && (
                    <div className="px-6 pb-6 bg-[#faf6ee] border-t border-[#e6dcce]">
                      <CopilotPanel
                        job={job}
                        onSaveToTracker={(aiResults, jdText) =>
                          handleSaveAIInsights(job.id, aiResults, jdText)
                        }
                        onJobUpdated={(updatedJob) =>
                          setJobs((prev) =>
                            prev.map((j) => (j.id === updatedJob.id ? updatedJob : j))
                          )
                        }
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
