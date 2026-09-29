import { useEffect, useState, type FormEvent } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getBook, updateBook, deleteBook } from "../api/services";
import { useAuth } from "../context/AuthContext";
import type { Book } from "../types";
import BookCover from "../components/BookCover";
import { buildBookFormData } from "../utils/bookForm";

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
  const [image, setImage] = useState<File | null>(null);

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
      const { data } = await updateBook(
        Number(id),
        buildBookFormData({ title, author, cover, inventory, dailyFee, image })
      );
      setBook(data);
      setImage(null);
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

  if (loading) return <div className="page text-muted">Loading...</div>;
  if (error) return <div className="page text-red-600">{error}</div>;
  if (!book) return null;

  return (
    <div className="page max-w-xl">
      <div className="card overflow-hidden">
        <BookCover book={book} className="h-64 w-full" />
        <div className="p-8">
        <h1 className="mb-6 font-serif text-3xl font-bold text-primary dark:text-blue-400">{book.title}</h1>

        {!editing ? (
          <div>
            <dl>
              <div className="flex justify-between border-b border-line py-3 last:border-0 dark:border-slate-700">
                <dt className="text-sm text-muted">Author</dt>
                <dd className="font-medium">{book.author}</dd>
              </div>
              <div className="flex justify-between border-b border-line py-3 last:border-0 dark:border-slate-700">
                <dt className="text-sm text-muted">Cover</dt>
                <dd className="font-medium">{book.cover}</dd>
              </div>
              <div className="flex justify-between border-b border-line py-3 last:border-0 dark:border-slate-700">
                <dt className="text-sm text-muted">Available</dt>
                <dd className="font-medium">{book.inventory > 0 ? (
                    <span className="badge badge-green">{book.inventory} available</span>
                  ) : (
                    <span className="badge badge-red">Out of stock</span>
                  )}</dd>
              </div>
              <div className="flex justify-between border-b border-line py-3 last:border-0 dark:border-slate-700">
                <dt className="text-sm text-muted">Daily Fee</dt>
                <dd className="font-medium">${book.daily_fee}</dd>
              </div>
            </dl>

            <div className="mt-6 flex flex-wrap gap-3">
              {book.inventory > 0 && (
                <button onClick={() => navigate(`/borrowings/create?book=${book.id}`)} className="btn">
                  Borrow this book
                </button>
              )}
              {user?.is_staff && (
                <>
                  <button onClick={() => setEditing(true)} className="btn-outline">Edit</button>
                  <button onClick={handleDelete} className="btn-danger">Delete</button>
                </>
              )}
            </div>
          </div>
        ) : (
          <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required className="input" />
          </div>
          <div>
            <label className="label">Author</label>
            <input value={author} onChange={(e) => setAuthor(e.target.value)} required className="input" />
          </div>
          <div>
            <label className="label">Cover</label>
            <select value={cover} onChange={(e) => setCover(e.target.value)} className="input">
              <option value="HARD">Hard</option>
              <option value="SOFT">Soft</option>
            </select>
          </div>
          <div>
            <label className="label">Inventory</label>
            <input type="number" value={inventory} onChange={(e) => setInventory(Number(e.target.value))} min={0} required className="input" />
          </div>
          <div>
            <label className="label">Daily Fee ($)</label>
            <input value={dailyFee} onChange={(e) => setDailyFee(e.target.value)}  required className="input" />
          </div>
            <div>
            <label className="label">Image</label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setImage(e.target.files?.[0] ?? null)}
              className="input file:mr-3 file:cursor-pointer file:rounded-md file:border-0 file:bg-primary-lighter file:px-3 file:py-1 file:text-sm file:font-semibold file:text-primary"
            />
          </div>
            <div className="flex gap-3">
              <button type="submit" className="btn">Save</button>
              <button type="button" onClick={() => setEditing(false)} className="btn-outline">Cancel</button>
            </div>
          </form>
        )}
        </div>
      </div>

      <button onClick={() => navigate("/books")} className="btn-outline mt-5">← Back to Books</button>
    </div>
  );
}
