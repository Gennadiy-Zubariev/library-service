import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getBooks, createBorrowing } from "../api/services";
import type { Book } from "../types";
import BookIcon from "../components/BookIcon";

export default function CreateBorrowingPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [searchParams] = useSearchParams();
  const [selectedBook, setSelectedBook] = useState(searchParams.get("book") ?? "");
  const [returnDate, setReturnDate] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        // The API is paginated: load every page so any book can be selected.
        const all: Book[] = [];
        let page = 1;
        while (true) {
          const { data } = await getBooks(page);
          all.push(...data.results);
          if (!data.next) break;
          page += 1;
        }
        setBooks(all.filter((b) => b.inventory > 0));
      } catch (err) {
        console.error("Failed to fetch books", err);
      } finally {
        setLoading(false);
      }
    };
    fetchBooks();
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await createBorrowing({
        book: Number(selectedBook),
        expected_return_date: returnDate,
      });
      navigate("/borrowings");
    } catch (err: any) {
      const detail = err.response?.data;
      if (typeof detail === "object") {
        const messages = Object.values(detail).flat().join(" ");
        setError(messages);
      } else {
        setError("Failed to create borrowing.");
      }
    }
  };

  // Minimum return date is tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split("T")[0];

  if (loading) return <div className="page text-muted">Loading...</div>;

  return (
    <div className="auth-wrap">
      <div className="card w-full max-w-lg p-8">
        <div className="mb-4 flex justify-center text-primary dark:text-blue-400"><BookIcon size={44} /></div>
        <h1 className="mb-6 text-center font-serif text-3xl font-bold text-primary dark:text-blue-400">New Borrowing</h1>
        {error && <p className="mb-4 rounded-control bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Book</label>
            <select value={selectedBook} onChange={(e) => setSelectedBook(e.target.value)} required className="input">
              <option value="">Select a book</option>
              {books.map((book) => (
                <option key={book.id} value={book.id}>
                  {book.title} — {book.author} (${book.daily_fee}/day, {book.inventory} available)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Expected Return Date</label>
            <input type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)} min={minDate} required className="input" />
          </div>
          <button type="submit" className="btn w-full">Borrow</button>
        </form>
      </div>
    </div>
  );
}
