import { useState, FormEvent } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/axiosInstance";

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
    <div style={{ maxWidth: 400, margin: "40px auto" }}>
      <h1>My Profile</h1>
      <p style={{ color: "#666", marginBottom: 20 }}>
        Email: {user?.email}
        {user?.is_staff && <span style={{ color: "#ffd700" }}> (Admin)</span>}
      </p>
      {message && <p style={{ color: "green" }}>{message}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label>First Name</label>
          <br />
          <input
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label>Last Name</label>
          <br />
          <input
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <button type="submit" style={{ padding: "8px 24px" }}>
          Save
        </button>
      </form>
    </div>
  );
}
