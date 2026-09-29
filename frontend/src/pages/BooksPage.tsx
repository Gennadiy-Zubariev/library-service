import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { getBooks } from "../api/services";
import { useAuth } from "../context/AuthContext";
import type { Book } from "../types";
import BookCover from "../components/BookCover";

export default function BooksPage() {
  const { user } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = useRef(0);

  useEffect(() => {
    const fetchBooks = async () => {
      setLoading(true);
      try {
        const { data } = await getBooks(page);
        setBooks(data.results);
        // Page size comes from the API (first page length), not a hardcoded number.
        if (page === 1) pageSize.current = data.next ? data.results.length : data.count;
        setTotalPages(Math.max(1, Math.ceil(data.count / (pageSize.current || 1))));
      } catch (err) {
        console.error("Failed to fetch books", err);
      } finally {
        setLoading(false);
      }
    };
    fetchBooks();
  }, [page]);

  if (loading) return <div className="page text-muted">Loading...</div>;

  return (
    <div className="page">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-serif text-3xl font-bold text-primary dark:text-blue-400">Books</h1>
        {user?.is_staff && (
          <Link to="/books/create" className="btn">+ Add Book</Link>
        )}
      </div>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {books.map((book) => (
          <Link
            key={book.id}
            to={`/books/${book.id}`}
            className="card overflow-hidden transition hover:-translate-y-1 hover:shadow-lg"
          >
            <BookCover book={book} className="h-56 w-full" />
            <div className="p-4">
              {book.image && <h2 className="font-serif text-lg font-bold leading-tight">{book.title}</h2>}
              <p className="text-sm text-muted">{book.author}</p>
              <div className="mt-3 flex items-center justify-between">
                <span className="font-bold text-primary dark:text-blue-400">${book.daily_fee}/day</span>
                {book.inventory > 0 ? (
                  <span className="badge badge-green">{book.inventory} available</span>
                ) : (
                  <span className="badge badge-red">Out of stock</span>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-4">
          <button className="btn-outline disabled:opacity-50" onClick={() => setPage((p) => p - 1)} disabled={page === 1}>
            Previous
          </button>
          <span className="text-sm text-muted">Page {page} of {totalPages}</span>
          <button className="btn-outline disabled:opacity-50" onClick={() => setPage((p) => p + 1)} disabled={page === totalPages}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}
