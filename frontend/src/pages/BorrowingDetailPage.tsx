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

  if (loading) return <div className="page text-muted">Loading...</div>;
  if (error) return <div className="page text-red-600">{error}</div>;
  if (!borrowing) return null;

  return (
    <div className="page">
      <h1 className="mb-6 font-serif text-3xl font-bold text-primary dark:text-blue-400">Borrowing #{borrowing.id}</h1>

      <div className="grid gap-5 md:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-3 font-serif text-xl font-bold">Book Info</h3>
          <dl>
            <div className="flex justify-between border-b border-line py-2.5 last:border-0 dark:border-slate-700">
              <dt className="text-sm text-muted">Title</dt>
              <dd className="font-medium">{borrowing.book.title}</dd>
            </div>
            <div className="flex justify-between border-b border-line py-2.5 last:border-0 dark:border-slate-700">
              <dt className="text-sm text-muted">Author</dt>
              <dd className="font-medium">{borrowing.book.author}</dd>
            </div>
            <div className="flex justify-between border-b border-line py-2.5 last:border-0 dark:border-slate-700">
              <dt className="text-sm text-muted">Cover</dt>
              <dd className="font-medium">{borrowing.book.cover}</dd>
            </div>
            <div className="flex justify-between border-b border-line py-2.5 last:border-0 dark:border-slate-700">
              <dt className="text-sm text-muted">Daily Fee</dt>
              <dd className="font-medium">${borrowing.book.daily_fee}</dd>
            </div>
          </dl>
        </div>

        <div className="card p-6">
          <h3 className="mb-3 font-serif text-xl font-bold">Borrowing Info</h3>
          <dl>
            <div className="flex justify-between border-b border-line py-2.5 last:border-0 dark:border-slate-700">
              <dt className="text-sm text-muted">Borrow Date</dt>
              <dd className="font-medium">{borrowing.borrow_date}</dd>
            </div>
            <div className="flex justify-between border-b border-line py-2.5 last:border-0 dark:border-slate-700">
              <dt className="text-sm text-muted">Expected Return</dt>
              <dd className="font-medium">{borrowing.expected_return_date}</dd>
            </div>
            <div className="flex justify-between border-b border-line py-2.5 last:border-0 dark:border-slate-700">
              <dt className="text-sm text-muted">Actual Return</dt>
              <dd className="font-medium">{borrowing.actual_return_date ? (
                <span className="badge badge-green">● {borrowing.actual_return_date}</span>
              ) : (
                <span className="badge badge-orange">● Not returned yet</span>
              )}</dd>
            </div>
          </dl>
        </div>
      </div>

      {!borrowing.actual_return_date && (
        <div className="mt-5">
          {borrowing.payments.some((p) => p.status === "PENDING") && (
            <p className="mb-4 rounded-control border border-orange-200 bg-orange-50 px-4 py-3 text-sm font-medium text-orange-600 dark:border-orange-900 dark:bg-orange-950">
              ⚠️ You have unpaid payments for this borrowing
            </p>
          )}
          <button onClick={handleReturn} className="btn-green cursor-pointer">Return Book</button>
        </div>
      )}

      {borrowing.payments.length > 0 && (
        <div className="mt-8">
          <h3 className="mb-3 font-serif text-xl font-bold">Payments</h3>
          <div className="card overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-line dark:border-slate-700">
                <tr>
                  <th className="th">Type</th>
                  <th className="th">Amount</th>
                  <th className="th">Status</th>
                  <th className="th">Action</th>
                </tr>
              </thead>
              <tbody>
                {borrowing.payments.map((p) => (
                  <tr key={p.id} className="border-b border-line transition last:border-0 hover:bg-primary-lighter/40 dark:border-slate-700 dark:hover:bg-slate-700/50">
                    <td className="td">{p.type}</td>
                    <td className="td">${p.money_to_pay}</td>
                    <td className="td">
                      <span className={`badge ${p.status === "PAID" ? "badge-green" : "badge-orange"}`}>
                        ● {p.status}
                      </span>
                    </td>
                    <td className="td">
                      {p.status === "PENDING" && (
                        <a href={p.session_url} className="btn !px-3 !py-1.5">
                          Pay Now
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <button onClick={() => navigate("/borrowings")} className="btn-outline mt-6">← Back to Borrowings</button>
    </div>
  );
}
