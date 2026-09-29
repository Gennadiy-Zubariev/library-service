import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import api from "../api/axiosInstance";

export default function PaymentSuccessPage() {
  const [searchParams] = useSearchParams();
  const [message, setMessage] = useState("Verifying payment...");
  const [error, setError] = useState("");

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    if (!sessionId) {
      setError("No session ID provided");
      return;
    }

    const verifyPayment = async () => {
      try {
        const { data } = await api.get(
          `/payments/success/?session_id=${sessionId}`
        );
        setMessage(data.message);
      } catch {
        setError("Failed to verify payment");
      }
    };
    verifyPayment();
  }, [searchParams]);

  return (
    <div style={{ padding: 20, maxWidth: 500, margin: "80px auto", textAlign: "center" }}>
      {error ? (
        <div>
          <h1 style={{ color: "red" }}>Error</h1>
          <p>{error}</p>
        </div>
      ) : (
        <div>
          <h1 style={{ color: "green" }}>✅ {message}</h1>
        </div>
      )}
      <Link to="/borrowings" style={{ marginTop: 20, display: "inline-block" }}>
        ← Back to Borrowings
      </Link>
    </div>
  );
}
