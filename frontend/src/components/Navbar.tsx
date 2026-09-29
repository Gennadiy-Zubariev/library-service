import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      padding: "12px 24px",
      backgroundColor: "#333",
      color: "white",
    }}>
      <div style={{ display: "flex", gap: 16 }}>
        <Link to="/" style={{ color: "white", textDecoration: "none", fontWeight: "bold" }}>
          Library
        </Link>
        <Link to="/books" style={{ color: "white", textDecoration: "none" }}>
          Books
        </Link>
        {user && (
          <>
            <Link to="/borrowings" style={{ color: "white", textDecoration: "none" }}>
              My Borrowings
            </Link>
            <Link to="/profile" style={{ color: "white", textDecoration: "none" }}>
              Profile
            </Link>
          </>
        )}
      </div>
      <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
        {user ? (
          <>
            <span>{user.first_name} {user.last_name}</span>
            {user.is_staff && <span style={{ color: "#ffd700" }}>(Admin)</span>}
            <button onClick={logout} style={{ padding: "4px 12px" }}>
              Logout
            </button>
          </>
        ) : (
          <Link to="/login" style={{ color: "white", textDecoration: "none" }}>
            Login
          </Link>
        )}
      </div>
    </nav>
  );
}
