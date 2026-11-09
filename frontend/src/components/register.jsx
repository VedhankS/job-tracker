import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const cleanEmail = email.trim().toLowerCase();

    try {
      const res = await fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: cleanEmail, password }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        setError(data.error || 'Registration failed');
        return;
      }

      navigate('/login');
    } catch (err) {
      setError(err.message || 'An error occurred during registration');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#faf7f2] p-4 text-stone-800">
      <div className="max-w-md w-full p-8 bg-white rounded-xl shadow-sm border border-[#e2d8c8]">
        <h1 className="text-2xl font-bold text-center text-orange-600 mb-1">JobTracker</h1>
        <p className="text-center text-xs text-stone-500 mb-6">Create a new account</p>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded text-xs mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label className="block text-xs font-medium text-stone-700 mb-1">Email</label>
            <input
              type="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck="false"
              placeholder="user@example.com"
              className="w-full p-2.5 bg-white border border-[#d6cbba] rounded text-stone-900 placeholder-stone-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm"
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
              className="w-full p-2.5 bg-white border border-[#d6cbba] rounded text-stone-900 placeholder-stone-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white font-medium p-2.5 rounded hover:bg-blue-500 transition text-sm shadow-2xs"
          >
            Register
          </button>
        </form>

        <p className="text-center text-sm text-stone-600 mt-5">
          Already have an account?{' '}
          <Link to="/login" className="text-orange-600 hover:text-orange-700 hover:underline font-medium">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
