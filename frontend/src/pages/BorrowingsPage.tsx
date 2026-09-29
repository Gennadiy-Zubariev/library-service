import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBorrowings } from "../api/services";
import { useAuth } from "../context/AuthContext";
import type { Borrowing } from "../types";

export default function BorrowingsPage() {
  const { user } = useAuth();
  const [borrowings, setBorrowings] = useState<Borrowing[]>([]);
  const [loading, setLoading] = useState(true);
  const [isActive, setIsActive] = useState("");
  const [userId, setUserId] = useState("");

  useEffect(() => {
    const fetchBorrowings = async () => {
      setLoading(true);
      try {
        const params: Record<string, string> = {};
        if (isActive) params.is_active = isActive;
        if (userId && user?.is_staff) params.user_id = userId;

        const { data } = await getBorrowings(params);
        setBorrowings(data.results);
      } catch (err) {
        console.error("Failed to fetch borrowings", err);
      } finally {
        setLoading(false);
      }
    };
    fetchBorrowings();
  }, [isActive, userId, user?.is_staff]);

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>;

  return (
    <div style={{ padding: 20 }}>
      <h1>My Borrowings</h1>

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <select
          value={isActive}
          onChange={(e) => setIsActive(e.target.value)}
          style={{ padding: 8 }}
        >
          <option value="">All</option>
          <option value="true">Active only</option>
        </select>

        {user?.is_staff && (
          <input
            type="number"
            placeholder="Filter by User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            style={{ padding: 8 }}
          />
        )}

        <Link to="/borrowings/create">
          <button style={{ padding: "8px 16px" }}>+ New Borrowing</button>
        </Link>
      </div>

      {borrowings.length === 0 ? (
        <p>No borrowings found.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #333", textAlign: "left" }}>
              <th style={{ padding: 8 }}>ID</th>
              <th style={{ padding: 8 }}>Book</th>
              <th style={{ padding: 8 }}>Borrow Date</th>
              <th style={{ padding: 8 }}>Expected Return</th>
              <th style={{ padding: 8 }}>Status</th>
              <th style={{ padding: 8 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {borrowings.map((b) => (
              <tr key={b.id} style={{ borderBottom: "1px solid #ddd" }}>
                <td style={{ padding: 8 }}>{b.id}</td>
                <td style={{ padding: 8 }}>{b.book.title}</td>
                <td style={{ padding: 8 }}>{b.borrow_date}</td>
                <td style={{ padding: 8 }}>{b.expected_return_date}</td>
                <td style={{ padding: 8 }}>
                  {b.actual_return_date ? (
                    <span style={{ color: "green" }}>Returned {b.actual_return_date}</span>
                  ) : (
                    <span style={{ color: "orange" }}>Active</span>
                  )}
                </td>
                <td style={{ padding: 8 }}>
                  <Link to={`/borrowings/${b.id}`}>Details</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
