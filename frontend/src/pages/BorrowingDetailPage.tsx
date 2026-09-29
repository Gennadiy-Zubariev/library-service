import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getBorrowing, returnBorrowing } from "../api/services";
import type { Borrowing } from "../types";

export default function BorrowingDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [borrowing, setBorrowing] = useState<Borrowing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchBorrowing = async () => {
      try {
        const { data } = await getBorrowing(Number(id));
        setBorrowing(data);
      } catch {
        setError("Borrowing not found");
      } finally {
        setLoading(false);
      }
    };
    fetchBorrowing();
  }, [id]);

  const handleReturn = async () => {
    try {
      const { data } = await returnBorrowing(Number(id));
      setBorrowing(data);
    } catch (err: any) {
      const detail = err.response?.data;
      if (Array.isArray(detail)) {
        setError(detail.join(" "));
      } else if (typeof detail === "object") {
        setError(Object.values(detail).flat().join(" "));
      } else {
        setError("Failed to return book.");
      }
    }
  };

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>;
  if (error) return <div style={{ padding: 20, color: "red" }}>{error}</div>;
  if (!borrowing) return null;

  return (
    <div style={{ padding: 20, maxWidth: 600 }}>
      <h1>Borrowing #{borrowing.id}</h1>

      <div style={{ marginBottom: 20 }}>
        <h3>Book Info</h3>
        <p>Title: {borrowing.book.title}</p>
        <p>Author: {borrowing.book.author}</p>
        <p>Cover: {borrowing.book.cover}</p>
        <p>Daily Fee: ${borrowing.book.daily_fee}</p>
      </div>

      <div style={{ marginBottom: 20 }}>
        <h3>Borrowing Info</h3>
        <p>Borrow Date: {borrowing.borrow_date}</p>
        <p>Expected Return: {borrowing.expected_return_date}</p>
        <p>
          Actual Return:{" "}
          {borrowing.actual_return_date ? (
            <span style={{ color: "green" }}>{borrowing.actual_return_date}</span>
          ) : (
            <span style={{ color: "orange" }}>Not returned yet</span>
          )}
        </p>
      </div>

        {!borrowing.actual_return_date && (
          <div>
            {borrowing.payments.some((p) => p.status === "PENDING") && (
              <p style={{ color: "orange", marginBottom: 8 }}>
                ⚠️ You have unpaid payments for this borrowing
              </p>
            )}
            <button
              onClick={handleReturn}
              style={{
                padding: "8px 24px",
                backgroundColor: "#4CAF50",
                color: "white",
                border: "none",
                cursor: "pointer",
                marginBottom: 20,
              }}
            >
              Return Book
            </button>
          </div>
        )}

      {borrowing.payments.length > 0 && (
        <div>
          <h3>Payments</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #333", textAlign: "left" }}>
                <th style={{ padding: 8 }}>Type</th>
                <th style={{ padding: 8 }}>Amount</th>
                <th style={{ padding: 8 }}>Status</th>
                <th style={{ padding: 8 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {borrowing.payments.map((p) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #ddd" }}>
                  <td style={{ padding: 8 }}>{p.type}</td>
                  <td style={{ padding: 8 }}>${p.money_to_pay}</td>
                  <td style={{ padding: 8 }}>
                    <span style={{ color: p.status === "PAID" ? "green" : "orange" }}>
                      {p.status}
                    </span>
                  </td>
                  <td style={{ padding: 8 }}>
                    {p.status === "PENDING" &&
                      <a
                        href={p.session_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "blue" }}
                      >
                        Pay Now
                      </a>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button
        onClick={() => navigate("/borrowings")}
        style={{ marginTop: 16, padding: "8px 16px" }}
      >
        ← Back to Borrowings
      </button>
    </div>
  );
}
