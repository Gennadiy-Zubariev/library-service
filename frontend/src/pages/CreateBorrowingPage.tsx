import { useEffect, useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { getBooks, createBorrowing } from "../api/services";
import type { Book } from "../types";

export default function CreateBorrowingPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBook, setSelectedBook] = useState("");
  const [returnDate, setReturnDate] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        const { data } = await getBooks();
        setBooks(data.results.filter((b) => b.inventory > 0));
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

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>;

  return (
    <div style={{ maxWidth: 500, margin: "40px auto" }}>
      <h1>New Borrowing</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label>Book</label>
          <br />
          <select
            value={selectedBook}
            onChange={(e) => setSelectedBook(e.target.value)}
            required
            style={{ width: "100%", padding: 8 }}
          >
            <option value="">Select a book</option>
            {books.map((book) => (
              <option key={book.id} value={book.id}>
                {book.title} — {book.author} (${book.daily_fee}/day, {book.inventory} available)
              </option>
            ))}
          </select>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label>Expected Return Date</label>
          <br />
          <input
            type="date"
            value={returnDate}
            onChange={(e) => setReturnDate(e.target.value)}
            min={minDate}
            required
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <button type="submit" style={{ padding: "8px 24px" }}>
          Borrow
        </button>
      </form>
    </div>
  );
}
