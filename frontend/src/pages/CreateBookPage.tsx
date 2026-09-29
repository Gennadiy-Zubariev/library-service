import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createBook } from "../api/services";

export default function CreateBookPage() {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [cover, setCover] = useState("HARD");
  const [inventory, setInventory] = useState(1);
  const [dailyFee, setDailyFee] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await createBook({ title, author, cover, inventory, daily_fee: dailyFee });
      navigate("/books");
    } catch {
      setError("Failed to create book.");
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "40px auto" }}>
      <h1>Add New Book</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <form onSubmit={handleSubmit}>
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
            placeholder="1.50"
            required
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <button type="submit" style={{ padding: "8px 24px" }}>
          Create Book
        </button>
      </form>
    </div>
  );
}
