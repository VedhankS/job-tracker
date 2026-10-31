import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';

export default function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [error, setError] = useState('');
  const { authFetch, logout } = useAuth();

  // Fetch jobs when the component loads
  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      const res = await authFetch('/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (err) {
      setError('Failed to load jobs');
    }
  };

  const handleAddJob = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await authFetch('/jobs', {
        method: 'POST',
        body: JSON.stringify({ company, role }),
      });
      if (res.ok) {
        setCompany('');
        setRole('');
        loadJobs(); // Refresh the list
      } else {
        setError('Failed to add job');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      const res = await authFetch(`/jobs/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setJobs(jobs.filter(job => job.id !== id));
      }
    } catch (err) {
      setError('Failed to delete job');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">My Job Tracker</h1>
          <button
            onClick={logout}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition"
          >
            Logout
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Add Job Form */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Add a New Application</h2>
          <form onSubmit={handleAddJob} className="flex gap-4">
            <input
              type="text"
              placeholder="Company Name"
              className="flex-1 p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              required
            />
            <input
              type="text"
              placeholder="Role / Title"
              className="flex-1 p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              required
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition font-medium"
            >
              Add Job
            </button>
          </form>
        </div>

        {/* Jobs List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {jobs.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No jobs tracked yet. Add one above!</div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {jobs.map((job) => (
                <li key={job.id} className="p-6 flex justify-between items-center hover:bg-gray-50">
                  <div>
                    <h3 className="text-lg font-bold text-gray-800">{job.company}</h3>
                    <p className="text-gray-600">{job.role}</p>
                    <span className="inline-block mt-2 px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full uppercase tracking-wide">
                      {job.status || 'applied'}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDelete(job.id)}
                    className="text-red-500 hover:text-red-700 font-medium"
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

      </div>
    </div>
  );
}
