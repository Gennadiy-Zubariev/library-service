import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import BookIcon from "./BookIcon";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-control px-3.5 py-2 text-sm font-medium transition hover:bg-primary-lighter hover:text-primary dark:hover:bg-slate-700 dark:hover:text-blue-300 ${
    isActive ? "bg-primary-lighter text-primary dark:bg-slate-700 dark:text-blue-300" : "text-muted"
  }`;

export default function Navbar() {
  const { user, logout } = useAuth();
  const initials = user
    ? `${user.first_name?.[0] ?? ""}${user.last_name?.[0] ?? ""}`.toUpperCase() ||
      user.email[0].toUpperCase()
    : "";

  return (
    <nav className="sticky top-0 z-50 flex flex-wrap items-center justify-between gap-2 border-b border-line bg-white/80 px-4 py-3 backdrop-blur-md sm:px-6 dark:border-slate-700 dark:bg-slate-900/80">
      <div className="flex flex-wrap items-center gap-1 sm:gap-2">
        <Link to="/" className="mr-3 flex items-center gap-2 font-serif text-2xl font-bold text-primary dark:text-blue-400">
          <BookIcon size={26} />
          Library
        </Link>
        <NavLink to="/books" className={linkClass}>Books</NavLink>
        {user && (
          <>
            <NavLink to="/borrowings" className={linkClass}>My Borrowings</NavLink>
            <NavLink to="/profile" className={linkClass}>Profile</NavLink>
          </>
        )}
      </div>
      <div className="flex items-center gap-3">
        {user ? (
          <>
            <span className="hidden text-sm font-medium sm:inline">
              {user.first_name} {user.last_name}
            </span>
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-900 to-blue-500 text-sm font-bold text-white">
              {initials}
            </span>
            {user.is_staff && (
              <span className="rounded-full bg-primary-lighter px-2.5 py-0.5 text-xs font-bold text-primary">Admin</span>
            )}
            <button onClick={logout} className="btn-outline !py-1.5">Logout</button>
          </>
        ) : (
          <Link to="/login" className="btn">Login</Link>
        )}
      </div>
    </nav>
  );
}
