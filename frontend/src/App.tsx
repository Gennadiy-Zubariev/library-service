import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import BooksPage from "./pages/BooksPage";
import BorrowingsPage from "./pages/BorrowingsPage";
import CreateBorrowingPage from "./pages/CreateBorrowingPage";
import BorrowingDetailPage from "./pages/BorrowingDetailPage";
import PaymentSuccessPage from "./pages/PaymentSuccessPage";
import PaymentCancelPage from "./pages/PaymentCancelPage";
import ProfilePage from "./pages/ProfilePage";


function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;

  return <>{children}</>;
}

function HomePage() {
  const { user } = useAuth();

  return (
    <div style={{ padding: 20 }}>
      <h1>Welcome, {user?.first_name}!</h1>
      <p>Use the navigation above to browse books and manage your borrowings.</p>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/books" element={<BooksPage />} />
          <Route
            path="/borrowings"
            element={
              <PrivateRoute>
                <BorrowingsPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/borrowings/create"
            element={
              <PrivateRoute>
                <CreateBorrowingPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/borrowings/:id"
            element={
              <PrivateRoute>
                <BorrowingDetailPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <HomePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/payments/success"
            element={
              <PrivateRoute>
                <PaymentSuccessPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/payments/cancel"
            element={
              <PrivateRoute>
                <PaymentCancelPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <ProfilePage />
              </PrivateRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
