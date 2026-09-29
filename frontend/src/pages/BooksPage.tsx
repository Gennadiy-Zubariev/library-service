import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBooks } from "../api/services";
import { useAuth } from "../context/AuthContext";
import type { Book } from "../types";

export default function BooksPage() {
  const { user } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchBooks = async () => {
      setLoading(true);
      try {
        const { data } = await getBooks(page);
        setBooks(data.results);
        setTotalPages(Math.ceil(data.count / 10));
      } catch (err) {
        console.error("Failed to fetch books", err);
      } finally {
        setLoading(false);
      }
    };
    fetchBooks();
  }, [page]);

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>;

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Books</h1>
        {user?.is_staff && (
          <Link to="/books/create">
            <button style={{ padding: "8px 16px" }}>+ Add Book</button>
          </Link>
        )}
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #333", textAlign: "left" }}>
            <th style={{ padding: 8 }}>Title</th>
            <th style={{ padding: 8 }}>Author</th>
            <th style={{ padding: 8 }}>Cover</th>
            <th style={{ padding: 8 }}>Available</th>
            <th style={{ padding: 8 }}>Daily Fee</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book) => (
            <tr key={book.id} style={{ borderBottom: "1px solid #ddd" }}>
              <td style={{ padding: 8 }}>
                <Link to={`/books/${book.id}`}>{book.title}</Link>
              </td>
              <td style={{ padding: 8 }}>{book.author}</td>
              <td style={{ padding: 8 }}>{book.cover}</td>
              <td style={{ padding: 8 }}>{book.inventory}</td>
              <td style={{ padding: 8 }}>${book.daily_fee}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
          <button onClick={() => setPage((p) => p - 1)} disabled={page === 1}>
            Previous
          </button>
          <span>Page {page} of {totalPages}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={page === totalPages}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}
