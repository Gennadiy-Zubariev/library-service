import type { Book } from "../types";
import { coverGradient } from "../utils/bookTheme";

type Props = {
  book: Pick<Book, "id" | "title" | "image">;
  className?: string;
};

// Book image if uploaded, otherwise a gradient with the title.
export default function BookCover({ book, className = "" }: Props) {
  if (book.image) {
    return (
      <img
        src={book.image}
        alt={book.title}
        className={`object-cover ${className}`}
      />
    );
  }
  return (
    <div
      className={`flex items-end p-4 ${className}`}
      style={{ background: coverGradient(book.id) }}
    >
      <span className="font-serif text-xl font-bold leading-tight text-white">
        {book.title}
      </span>
    </div>
  );
}
