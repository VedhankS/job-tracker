import React, { useState, useEffect } from 'react'
import { useAuth } from './AuthContext';
export default function Dashboard() {
  const { logout, authFetch } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [company, setCompany] = useState([]);
  const [role, setRole] = useState('');
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleAddJob = async (e) => {
    e.preventDefault();
    if (!company || !role) return;

    const res = await authFetch('/jobs', {
      method: 'POST',
      body: JSON.stringigy({ company, role }),
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
    const res = await authFetch(`/jobs/${id}`,{
      method: 'DELETE',
    });
    if (res.ok) fetchJobs();
  };
  return (
    <div className = "min-h-screen bg-slate-900 text-slate-100 p-6">
      <header className ="max-w-4xl mx-auto flex justify-between items-center mb-8 pb-4 border-b border-slate-800">
        <h1 className = "text-2xl font-bold text-cyan-400">JobTracker Dashboard</h1>
        <button
          onClick={logout}
          className="px-3 py-1.5 bg-red-600/80 hover:bg-red-500rounded text-sm font-medium transition">
            Log Out
        </button>
      </header>
      <main className ="max-w-4xl mx-auto space-y-8">
        {/*Create Job Form */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-sm">
          <h2 className="text-lg font-semibold mb-4 text-slate-200">Track New Application</h2>
          <form onSubmit={handleAddJob} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Company (e.g. Stripe)"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="px-3 py-2 bg-slate-950 border border-slate-700 rounded focus:outline-none focus:border-cyan-500"
            />
            <input
              type="text"
              placeholder="Role (e.g. Backend Engineer)"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="px-3 py-2 bg-slate-950 border border-slate-700 rounded focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              className="bg-cyan-600 hover:bg-cyan-500 font-medium py-2 rounded transition"
            >
              Add Job
            </button>
           </form>
          </div>

         {/* Job Listings */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
             <h2 className="text-lg font-semibold">Your Applications</h2>
            <span className="text-xs bg-slate-700 text-slate-300 px-2.5 py-1 rounded-full">
              {jobs.length} Active
              </span>
          </div>

          {loading ? (
            <div className="p-6 text-center text-slate-400">Loading applications...</div>
          ) : jobs.length === 0 ? (
             <div className="p-6 text-center text-slate-400">
                      No applications tracked yet. Add your first job above!
            </div>
           ) : (
             <div className="divide-y divide-slate-700">
                      {jobs.map((job) => (
                <div key={job.id} className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-white">{job.company}</h3>
                    <p className="text-sm text-slate-400">{job.role}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <select
                      value={job.status || 'applied'}
                      onChange={(e) => handleStatusChange(job.id, e.target.value)}
                      className="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-sm focus:outline-none focus:border-cyan-500"
                    >
                      <option value="applied">Applied</option>
                      <option value="interviewing">Interviewing</option>
                      <option value="offered">Offered</option>
                      <option value="rejected">Rejected</option>
                    </select>

                    <button
                      onClick={() => handleDeleteJob(job.id)}
                      className="text-red-400 hover:text-red-300 text-sm font-medium p-1 transition"
                    >
                      Delete
                    </button>
                  </div>
                </div>
               ))}
             </div>
          )}
        </div>
      </main>
    </div>
  );
}
