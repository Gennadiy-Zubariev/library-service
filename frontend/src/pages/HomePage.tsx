import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getBooks, getStats } from "../api/services";
import BookCover from "../components/BookCover";
import type { Book } from "../types";

const MAX_BOOKS = 14;
const CARD_W = 150;
const GAP = 24;

type Stats = Awaited<ReturnType<typeof getStats>>["data"];

export default function HomePage() {
  const { user } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const first = await getBooks(1);
        let results = first.data.results;
        if (first.data.next) results = [...results, ...(await getBooks(2)).data.results];
        setBooks(results.slice(0, MAX_BOOKS));
      } catch {
        /* carousel stays hidden */
      }
    })();
    getStats().then(({ data }) => setStats(data)).catch(() => {});
  }, []);

  const radius = Math.max(260, Math.round((books.length * (CARD_W + GAP)) / (2 * Math.PI)));
  const step = books.length ? 360 / books.length : 0;
  const cards = [
    { label: "Books Available", value: stats?.books_available },
    { label: "Active Readers", value: stats?.active_readers },
    { label: "Borrowings Total", value: stats?.borrowings_total },
  ];

  return (
    <div>
      <section className="overflow-hidden px-4 pb-20 pt-14 text-center">
        <h1 className="font-serif text-4xl font-extrabold text-primary sm:text-[52px] dark:text-blue-400">
          Your Digital Library
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-muted dark:text-slate-400">
          Welcome{user?.first_name ? `, ${user.first_name}` : ""}! Browse the collection,
          borrow your next read and manage payments in one place.
        </p>
        <div className="relative z-10 mt-6 flex flex-wrap justify-center gap-3">
          <Link to="/books" className="btn">Browse Books</Link>
          <Link to="/borrowings" className="btn-outline">My Borrowings</Link>
        </div>

        {books.length > 0 && (
          <div className="group mx-auto mt-16 h-[230px] w-[150px] [perspective:1800px]">
            <div className="relative h-full w-full [transform-style:preserve-3d] [animation:spin3d_25s_linear_infinite] group-hover:[animation-play-state:paused]">
              {books.map((b, i) => (
                <Link
                  key={b.id}
                  to={`/books/${b.id}`}
                  className="absolute inset-0 overflow-hidden rounded-xl shadow-lg"
                  style={{ transform: `rotateY(${i * step}deg) translateZ(${radius}px)` }}
                >
                  <BookCover book={b} className="h-full w-full" />
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="mx-auto grid max-w-4xl gap-4 px-4 py-10 sm:grid-cols-3">
        {cards.map((s) => (
          <div key={s.label} className="card p-6 text-center transition hover:-translate-y-1 hover:shadow-lg">
            <div className="font-serif text-3xl font-extrabold text-primary dark:text-blue-400">
              {s.value ?? "–"}
            </div>
            <div className="mt-1 text-sm text-muted">{s.label}</div>
          </div>
        ))}
      </section>
    </div>
  );
}
