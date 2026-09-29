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

  if (loading) return <div className="page text-muted">Loading...</div>;

  return (
    <div className="page">
      <h1 className="mb-6 font-serif text-3xl font-bold text-primary dark:text-blue-400">My Borrowings</h1>

      <div className="mb-5 flex flex-wrap items-center gap-3">
        <select value={isActive} onChange={(e) => setIsActive(e.target.value)} className="input !w-auto">
          <option value="">All</option>
          <option value="true">Active only</option>
        </select>

        {user?.is_staff && (
          <input
            type="number"
            placeholder="Filter by User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="input !w-auto"
          />
        )}

        <Link to="/borrowings/create" className="btn ml-auto">+ New Borrowing</Link>
      </div>

      {borrowings.length === 0 ? (
        <p className="text-muted">No borrowings found.</p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-line dark:border-slate-700">
              <tr>
                <th className="th">ID</th>
                <th className="th">Book</th>
                <th className="th">Borrow Date</th>
                <th className="th">Expected Return</th>
                <th className="th">Status</th>
                <th className="th">Actions</th>
              </tr>
            </thead>
            <tbody>
              {borrowings.map((b) => (
                <tr key={b.id} className="border-b border-line transition last:border-0 hover:bg-primary-lighter/40 dark:border-slate-700 dark:hover:bg-slate-700/50">
                  <td className="td">{b.id}</td>
                  <td className="td font-medium">{b.book.title}</td>
                  <td className="td">{b.borrow_date}</td>
                  <td className="td">{b.expected_return_date}</td>
                  <td className="td">
                    {b.actual_return_date ? (
                      <span className="badge badge-green">● Returned {b.actual_return_date}</span>
                    ) : (
                      <span className="badge badge-orange">● Active</span>
                    )}
                  </td>
                  <td className="td">
                    <Link to={`/borrowings/${b.id}`} className="font-semibold text-primary hover:underline dark:text-blue-400">Details</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
