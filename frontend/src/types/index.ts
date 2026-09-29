export interface Book {
  id: number;
  title: string;
  author: string;
  cover: "HARD" | "SOFT";
  inventory: number;
  daily_fee: string;
  image: string | null;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
}

export interface Payment {
  id: number;
  status: "PENDING" | "PAID";
  type: "PAYMENT" | "FINE";
  borrowing: number;
  session_url: string;
  session_id: string;
  money_to_pay: string;
}

export interface Borrowing {
  id: number;
  borrow_date: string;
  expected_return_date: string;
  actual_return_date: string | null;
  book: Book;
  user: number;
  payments: Payment[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
