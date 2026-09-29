import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "../api/services";
import BookIcon from "../components/BookIcon";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      });
      navigate("/login");
    } catch {
      setError("Registration failed. Email might already be taken.");
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card w-full max-w-md p-8">
        <div className="mb-4 flex justify-center text-primary dark:text-blue-400"><BookIcon size={44} /></div>
        <h1 className="mb-6 text-center font-serif text-3xl font-bold text-primary dark:text-blue-400">Register</h1>
        {error && <p className="mb-4 rounded-control bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="input" />
          </div>
          <div>
            <label className="label">First Name</label>
            <input value={firstName} onChange={(e) => setFirstName(e.target.value)} required className="input" />
          </div>
          <div>
            <label className="label">Last Name</label>
            <input value={lastName} onChange={(e) => setLastName(e.target.value)} required className="input" />
          </div>
          <div>
            <label className="label">Password</label>
            <input type="password" minLength={5} value={password} onChange={(e) => setPassword(e.target.value)} required className="input" />
          </div>
          <button type="submit" className="btn w-full">Register</button>
        </form>
        <p className="mt-5 text-center text-sm text-muted">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-primary hover:underline dark:text-blue-400">Login</Link>
        </p>
      </div>
    </div>
  );
}
