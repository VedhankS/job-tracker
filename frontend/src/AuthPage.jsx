import React, { useState } from 'react';
import { useAuth } from './AuthContext';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, API_BASE } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const endpoint = isLogin ? '/login' : 'register';
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || data.error || 'Authenticaion Failed')
      }
      if (isLogin) {
        login(data.access_token);
      } else {
        const loginRes = await fetch(`${API_BASE}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const loginData = await loginRes.json();
        login(loginData.access_token);
      }
    } catch (err) {
      setError(err.message);
    }
  };
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white px-4">
      <div className='w-full max-w-md bg-slate-800 p-8 rounded-xl shadow-lg border border-slate-700'>
        <h2 className="text-2xl font-bold mb-6 text-center text-cyan-400">
          {isLogin ? 'Log In to JobTracker' : 'Create an Account'}
        </h2>
        {error && (
          <div className="mb-4 p-3 bf-red-500/20 border border-red-500 text-red-200 text-sm rounded">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="black text-sm font-medium mb-1 text-slate-300">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded text-white focus:outline-none focus:border=cyan-500"
            />
          </div>
          <div>
            <label className="blocl text-sm font-medium mb-1 text-slate-300">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full py-2 px-4 bg-slate-950 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button type="submit"
            className='w-full py-2 px4 bg-cyan-600 hover:bf-cyan-500 font-semibold rounded transition'>
            {isLogin ? 'Log In' : 'Register'}
          </button>
        </form>
        <div className='mt-6 text-center text-sm text-slate-400'>
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <button
            onClick={() => { setIsLogin(!isLogin); setError(''); }}
            className="text-cyan-400 hover:underline"
          >
            {isLogin ? 'Register' : 'Login'}
          </button>
        </div>
      </div>
    </div>
  );
}
