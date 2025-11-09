import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, LogOut, Library, Clock, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/App';
import { toast } from 'sonner';
import { format } from 'date-fns';

export default function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [borrowedBooks, setBorrowedBooks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBorrowedBooks();
  }, []);

  const fetchBorrowedBooks = async () => {
    try {
      const response = await api.get('/transactions/borrowed');
      setBorrowedBooks(response.data);
    } catch (error) {
      toast.error('Failed to fetch borrowed books');
    } finally {
      setLoading(false);
    }
  };

  const handleReturn = async (transactionId) => {
    try {
      const response = await api.post('/return', { transaction_id: transactionId });
      toast.success(`Book returned! ${response.data.fine > 0 ? `Fine: $${response.data.fine}` : ''}`);
      fetchBorrowedBooks();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to return book');
    }
  };

  const getDaysRemaining = (dueDate) => {
    const due = new Date(dueDate);
    const today = new Date();
    const diff = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
    return diff;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">LibraryHub</h1>
                <p className="text-sm text-gray-600">{user.name}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button 
                variant="outline" 
                onClick={() => navigate('/books')}
                data-testid="browse-books-button"
              >
                <Library className="w-4 h-4 mr-2" />
                Browse Books
              </Button>
              {user.role === 'librarian' && (
                <Button 
                  variant="outline" 
                  onClick={() => navigate('/librarian')}
                  data-testid="librarian-dashboard-button"
                >
                  Librarian Dashboard
                </Button>
              )}
              <Button variant="outline" onClick={onLogout} data-testid="logout-button">
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2" data-testid="dashboard-title">Welcome back, {user.name}!</h2>
          <p className="text-gray-600">Student ID: {user.student_id}</p>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card data-testid="borrowed-count-card">
            <CardHeader className="pb-3">
              <CardDescription>Currently Borrowed</CardDescription>
              <CardTitle className="text-3xl">{borrowedBooks.length}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">Max: 3 books</p>
            </CardContent>
          </Card>

          <Card data-testid="available-slots-card">
            <CardHeader className="pb-3">
              <CardDescription>Available Slots</CardDescription>
              <CardTitle className="text-3xl">{3 - borrowedBooks.length}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">You can borrow more</p>
            </CardContent>
          </Card>

          <Card data-testid="overdue-card">
            <CardHeader className="pb-3">
              <CardDescription>Overdue Books</CardDescription>
              <CardTitle className="text-3xl">
                {borrowedBooks.filter(b => getDaysRemaining(b.due_date) < 0).length}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">Return immediately</p>
            </CardContent>
          </Card>
        </div>

        {/* Borrowed Books */}
        <Card>
          <CardHeader>
            <CardTitle>My Borrowed Books</CardTitle>
            <CardDescription>Manage your currently borrowed books</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center py-8 text-gray-600">Loading...</p>
            ) : borrowedBooks.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No borrowed books</p>
                <Button onClick={() => navigate('/books')} data-testid="browse-catalog-button">
                  Browse Catalog
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {borrowedBooks.map((transaction) => {
                  const daysRemaining = getDaysRemaining(transaction.due_date);
                  const isOverdue = daysRemaining < 0;
                  
                  return (
                    <div key={transaction.id} className="flex items-center justify-between p-4 border rounded-lg" data-testid={`borrowed-book-${transaction.id}`}>
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg" data-testid="book-title">{transaction.book_title}</h3>
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                          <span className="flex items-center">
                            <Clock className="w-4 h-4 mr-1" />
                            Borrowed: {format(new Date(transaction.borrow_date), 'MMM dd, yyyy')}
                          </span>
                          <span className="flex items-center">
                            Due: {format(new Date(transaction.due_date), 'MMM dd, yyyy')}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        {isOverdue ? (
                          <Badge variant="destructive" className="flex items-center" data-testid="overdue-badge">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Overdue by {Math.abs(daysRemaining)} days
                          </Badge>
                        ) : daysRemaining <= 2 ? (
                          <Badge variant="warning" className="bg-yellow-100 text-yellow-800" data-testid="due-soon-badge">
                            Due in {daysRemaining} {daysRemaining === 1 ? 'day' : 'days'}
                          </Badge>
                        ) : (
                          <Badge variant="secondary" data-testid="days-remaining-badge">
                            {daysRemaining} days left
                          </Badge>
                        )}
                        
                        <Button 
                          onClick={() => handleReturn(transaction.id)}
                          data-testid={`return-book-button-${transaction.id}`}
                        >
                          Return Book
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}