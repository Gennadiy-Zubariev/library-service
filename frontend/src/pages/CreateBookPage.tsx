import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createBook } from "../api/services";
import { buildBookFormData } from "../utils/bookForm";
import BookIcon from "../components/BookIcon";

export default function CreateBookPage() {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [cover, setCover] = useState("HARD");
  const [inventory, setInventory] = useState(1);
  const [dailyFee, setDailyFee] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await createBook(
        buildBookFormData({ title, author, cover, inventory, dailyFee, image })
      );
      navigate("/books");
    } catch {
      setError("Failed to create book.");
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card w-full max-w-lg p-8">
        <div className="mb-4 flex justify-center text-primary dark:text-blue-400"><BookIcon size={44} /></div>
        <h1 className="mb-6 text-center font-serif text-3xl font-bold text-primary dark:text-blue-400">Add New Book</h1>
        {error && <p className="mb-4 rounded-control bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
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
            <input value={dailyFee} onChange={(e) => setDailyFee(e.target.value)} placeholder="1.50" required className="input" />
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
          <button type="submit" className="btn w-full">Create Book</button>
        </form>
      </div>
    </div>
  );
}
