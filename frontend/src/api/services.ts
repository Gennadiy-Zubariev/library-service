import api from "./axiosInstance";
import type {
  Book,
  User,
  Borrowing,
  Payment,
  TokenPair,
  PaginatedResponse,
} from "../types";

// Auth
export const login = (email: string, password: string) =>
  api.post<TokenPair>("/users/token/", { email, password });

export const register = (data: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}) => api.post<User>("/users/register/", data);

export const getMe = () => api.get<User>("/users/me/");

// Books
export const getBooks = (page = 1) =>
  api.get<PaginatedResponse<Book>>(`/books/?page=${page}`);

export const getBook = (id: number) => api.get<Book>(`/books/${id}/`);

// Borrowings
export const getBorrowings = (params?: {
  is_active?: string;
  user_id?: number;
  page?: number;
}) => api.get<PaginatedResponse<Borrowing>>("/borrowings/", { params });

export const getBorrowing = (id: number) =>
  api.get<Borrowing>(`/borrowings/${id}/`);

export const createBorrowing = (data: {
  book: number;
  expected_return_date: string;
}) => api.post<Borrowing>("/borrowings/", data);

export const returnBorrowing = (id: number) =>
  api.post<Borrowing>(`/borrowings/${id}/return/`);

// Payments
export const getPayments = (page = 1) =>
  api.get<PaginatedResponse<Payment>>(`/payments/?page=${page}`);
