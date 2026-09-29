import { Link } from "react-router-dom";

export default function PaymentCancelPage() {
  return (
    <div className="auth-wrap">
      <div className="card w-full max-w-md p-10 text-center">
        <div className="text-6xl">⏸️</div>
        <h1 className="mt-4 font-serif text-3xl font-bold text-orange-600">Payment Paused</h1>
        <p className="mt-2 text-muted">
          You can complete the payment later. The session is available for 24 hours.
        </p>
        <Link to="/borrowings" className="btn mt-6">← Back to Borrowings</Link>
      </div>
    </div>
  );
}
