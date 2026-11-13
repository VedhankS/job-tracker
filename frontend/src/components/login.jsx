
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../AuthContext";

const AUTH_API_URL = "https://job-tracker-r0ko.onrender.com";

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();
  const cleanEmail = email.trim().toLowerCase();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const res = await fetch(`${AUTH_API_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: cleanEmail, password }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        setError(data.error || 'Login failed: Invalid email or password');
        return;
      }

      if (!data.access_token) {
        setError('Login failed: Authentication token was not returned');
        return;
      }

      login(data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'An error occurred during login');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#faf7f2] p-4 text-stone-800">
      <div className="max-w-md w-full p-8 bg-white rounded-xl shadow-sm border border-[#e2d8c8]">
        <h1 className="text-2xl font-bold text-center text-orange-600 mb-1">JobTracker</h1>
        <p className="text-center text-xs text-stone-500 mb-6">Sign in to your account</p>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded text-xs mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-stone-700 mb-1">Email</label>
            <input
              type="email"
              placeholder="user@example.com"
              className="w-full p-2.5 bg-white border border-[#d6cbba] rounded text-stone-900 placeholder-stone-400 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-700 mb-1">Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              className="w-full p-2.5 bg-white border border-[#d6cbba] rounded text-stone-900 placeholder-stone-400 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-orange-600 text-white font-medium p-2.5 rounded hover:bg-orange-500 transition text-sm shadow-2xs"
          >
            Sign In
          </button>
        </form>

        <p className="text-center text-sm text-stone-600 mt-5">
          Don't have an account?{' '}
          <Link to="/register" className="text-orange-600 hover:text-orange-700 hover:underline font-medium">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
