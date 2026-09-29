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
    <div className="auth-wrap">
      <div className="card w-full max-w-md p-10 text-center">
        {error ? (
          <>
            <div className="text-6xl">❌</div>
            <h1 className="mt-4 font-serif text-3xl font-bold text-red-600">Error</h1>
            <p className="mt-2 text-muted">{error}</p>
          </>
        ) : (
          <>
            <div className="text-6xl">✅</div>
            <h1 className="mt-4 font-serif text-3xl font-bold text-green-600">{message}</h1>
          </>
        )}
        <Link to="/borrowings" className="btn mt-6">← Back to Borrowings</Link>
      </div>
    </div>
  );
}
