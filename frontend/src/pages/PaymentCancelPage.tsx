import { Link } from "react-router-dom";

export default function PaymentCancelPage() {
  return (
    <div style={{ padding: 20, maxWidth: 500, margin: "80px auto", textAlign: "center" }}>
      <h1>⏸️ Payment Paused</h1>
      <p>You can complete the payment later. The session is available for 24 hours.</p>
      <Link to="/borrowings" style={{ marginTop: 20, display: "inline-block" }}>
        ← Back to Borrowings
      </Link>
    </div>
  );
}
