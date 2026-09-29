import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login as loginApi } from "../api/services";
import { useAuth } from "../context/AuthContext";
import BookIcon from "../components/BookIcon";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const { data } = await loginApi(email, password);
      login(data.access, data.refresh);
      navigate("/");
    } catch {
      setError("Invalid email or password");
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card w-full max-w-md p-8">
        <div className="mb-4 flex justify-center text-primary dark:text-blue-400"><BookIcon size={44} /></div>
        <h1 className="mb-6 text-center font-serif text-3xl font-bold text-primary dark:text-blue-400">Login</h1>
        {error && <p className="mb-4 rounded-control bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="input" />
          </div>
          <div>
            <label className="label">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="input" />
          </div>
          <button type="submit" className="btn w-full">Login</button>
        </form>
        <p className="mt-5 text-center text-sm text-muted">
          Don't have an account?{" "}
          <Link to="/register" className="font-semibold text-primary hover:underline dark:text-blue-400">Register</Link>
        </p>
      </div>
    </div>
  );
}
