import { useEffect, useState, FormEvent } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getBook, updateBook, deleteBook } from "../api/services";
import { useAuth } from "../context/AuthContext";
import type { Book } from "../types";

export default function BookDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [book, setBook] = useState<Book | null>(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [cover, setCover] = useState("HARD");
  const [inventory, setInventory] = useState(0);
  const [dailyFee, setDailyFee] = useState("");

  useEffect(() => {
    const fetchBook = async () => {
      try {
        const { data } = await getBook(Number(id));
        setBook(data);
        setTitle(data.title);
        setAuthor(data.author);
        setCover(data.cover);
        setInventory(data.inventory);
        setDailyFee(data.daily_fee);
      } catch {
        setError("Book not found");
      } finally {
        setLoading(false);
      }
    };
    fetchBook();
  }, [id]);

  const handleUpdate = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const { data } = await updateBook(Number(id), {
        title,
        author,
        cover: cover as "HARD" | "SOFT",
        inventory,
        daily_fee: dailyFee,
      });
      setBook(data);
      setEditing(false);
    } catch {
      setError("Failed to update book");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this book?")) return;
    try {
      await deleteBook(Number(id));
      navigate("/books");
    } catch {
      setError("Failed to delete book");
    }
  };

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>;
  if (error) return <div style={{ padding: 20, color: "red" }}>{error}</div>;
  if (!book) return null;

  return (
    <div style={{ padding: 20, maxWidth: 500 }}>
      <h1>{book.title}</h1>

      {!editing ? (
        <div>
          <p>Author: {book.author}</p>
          <p>Cover: {book.cover}</p>
          <p>Available: {book.inventory}</p>
          <p>Daily Fee: ${book.daily_fee}</p>

          {user?.is_staff && (
            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button
                onClick={() => setEditing(true)}
                style={{ padding: "8px 16px" }}
              >
                Edit
              </button>
              <button
                onClick={handleDelete}
                style={{
                  padding: "8px 16px",
                  backgroundColor: "red",
                  color: "white",
                  border: "none",
                }}
              >
                Delete
              </button>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={handleUpdate}>
          <div style={{ marginBottom: 12 }}>
            <label>Title</label>
            <br />
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label>Author</label>
            <br />
            <input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              required
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label>Cover</label>
            <br />
            <select
              value={cover}
              onChange={(e) => setCover(e.target.value)}
              style={{ width: "100%", padding: 8 }}
            >
              <option value="HARD">Hard</option>
              <option value="SOFT">Soft</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label>Inventory</label>
            <br />
            <input
              type="number"
              value={inventory}
              onChange={(e) => setInventory(Number(e.target.value))}
              min={0}
              required
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label>Daily Fee ($)</label>
            <br />
            <input
              value={dailyFee}
              onChange={(e) => setDailyFee(e.target.value)}
              required
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="submit" style={{ padding: "8px 16px" }}>
              Save
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              style={{ padding: "8px 16px" }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <button
        onClick={() => navigate("/books")}
        style={{ marginTop: 16, padding: "8px 16px" }}
      >
        ← Back to Books
      </button>
    </div>
  );
}
