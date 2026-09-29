import { useState, type FormEvent } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/axiosInstance";
import BookIcon from "../components/BookIcon";

export default function ProfilePage() {
  const { user } = useAuth();
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      await api.patch("/users/me/", {
        first_name: firstName,
        last_name: lastName,
      });
      setMessage("Profile updated successfully!");
    } catch {
      setError("Failed to update profile.");
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card w-full max-w-md p-8">
        <div className="mb-4 flex justify-center text-primary dark:text-blue-400"><BookIcon size={44} /></div>
        <h1 className="mb-2 text-center font-serif text-3xl font-bold text-primary dark:text-blue-400">My Profile</h1>
        <p className="mb-6 text-center text-sm text-muted">
          {user?.email}
          {user?.is_staff && <span className="ml-2 rounded-full bg-primary-lighter px-2.5 py-0.5 text-xs font-bold text-primary">Admin</span>}
        </p>
        {message && <p className="mb-4 rounded-control bg-green-50 px-3 py-2 text-sm text-green-600">{message}</p>}
        {error && <p className="mb-4 rounded-control bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">First Name</label>
            <input value={firstName} onChange={(e) => setFirstName(e.target.value)} className="input" />
          </div>
          <div>
            <label className="label">Last Name</label>
            <input value={lastName} onChange={(e) => setLastName(e.target.value)} className="input" />
          </div>
          <button type="submit" className="btn w-full">Save</button>
        </form>
      </div>
    </div>
  );
}
