import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, ArrowLeft, Plus, Trash2, Users, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { api } from '@/App';
import { toast } from 'sonner';
import { format } from 'date-fns';

export default function LibrarianDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [books, setBooks] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({ total_books: 0, total_users: 0, active_borrows: 0 });
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newBook, setNewBook] = useState({
    title: '',
    author: '',
    category: 'Fiction',
    isbn: '',
    description: '',
    total_copies: 1
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [booksRes, transactionsRes, statsRes] = await Promise.all([
        api.get('/books'),
        api.get('/transactions'),
        api.get('/stats')
      ]);
      setBooks(booksRes.data);
      setTransactions(transactionsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddBook = async (e) => {
    e.preventDefault();
    try {
      await api.post('/books', newBook);
      toast.success('Book added successfully!');
      setDialogOpen(false);
      setNewBook({
        title: '',
        author: '',
        category: 'Fiction',
        isbn: '',
        description: '',
        total_copies: 1
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add book');
    }
  };

  const handleDeleteBook = async (bookId) => {
    if (!window.confirm('Are you sure you want to delete this book?')) return;
    
    try {
      await api.delete(`/books/${bookId}`);
      toast.success('Book deleted successfully!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete book');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Button variant="ghost" onClick={() => navigate('/dashboard')} data-testid="back-to-dashboard-button">
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Librarian Dashboard</h1>
                <p className="text-sm text-gray-600">Manage books and transactions</p>
              </div>
            </div>
            
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button data-testid="add-book-button">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Book
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Add New Book</DialogTitle>
                  <DialogDescription>Fill in the details to add a new book to the library</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleAddBook} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="title">Title *</Label>
                      <Input
                        id="title"
                        data-testid="book-title-input"
                        value={newBook.title}
                        onChange={(e) => setNewBook({ ...newBook, title: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="author">Author *</Label>
                      <Input
                        id="author"
                        data-testid="book-author-input"
                        value={newBook.author}
                        onChange={(e) => setNewBook({ ...newBook, author: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="category">Category *</Label>
                      <Select value={newBook.category} onValueChange={(value) => setNewBook({ ...newBook, category: value })}>
                        <SelectTrigger data-testid="book-category-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Fiction">Fiction</SelectItem>
                          <SelectItem value="Non-Fiction">Non-Fiction</SelectItem>
                          <SelectItem value="Science">Science</SelectItem>
                          <SelectItem value="Technology">Technology</SelectItem>
                          <SelectItem value="History">History</SelectItem>
                          <SelectItem value="Reference">Reference</SelectItem>
                          <SelectItem value="Academic">Academic</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="isbn">ISBN *</Label>
                      <Input
                        id="isbn"
                        data-testid="book-isbn-input"
                        value={newBook.isbn}
                        onChange={(e) => setNewBook({ ...newBook, isbn: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      data-testid="book-description-input"
                      value={newBook.description}
                      onChange={(e) => setNewBook({ ...newBook, description: e.target.value })}
                      rows={3}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="total_copies">Total Copies *</Label>
                    <Input
                      id="total_copies"
                      data-testid="book-copies-input"
                      type="number"
                      min="1"
                      value={newBook.total_copies}
                      onChange={(e) => setNewBook({ ...newBook, total_copies: parseInt(e.target.value) })}
                      required
                    />
                  </div>
                  
                  <Button type="submit" className="w-full" data-testid="submit-book-button">
                    Add Book
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card data-testid="total-books-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardDescription>Total Books</CardDescription>
                <BookOpen className="w-5 h-5 text-purple-600" />
              </div>
              <CardTitle className="text-3xl">{stats.total_books}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">In collection</p>
            </CardContent>
          </Card>

          <Card data-testid="total-users-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardDescription>Total Students</CardDescription>
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <CardTitle className="text-3xl">{stats.total_users}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">Registered users</p>
            </CardContent>
          </Card>

          <Card data-testid="active-borrows-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardDescription>Active Borrows</CardDescription>
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <CardTitle className="text-3xl">{stats.active_borrows}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">Currently borrowed</p>
            </CardContent>
          </Card>
        </div>

        {/* Books Management */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Book Inventory</CardTitle>
            <CardDescription>Manage your library collection</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center py-8 text-gray-600">Loading...</p>
            ) : books.length === 0 ? (
              <p className="text-center py-8 text-gray-600">No books in inventory</p>
            ) : (
              <div className="space-y-3">
                {books.map((book) => (
                  <div key={book.id} className="flex items-center justify-between p-4 border rounded-lg hover:shadow-sm transition-shadow" data-testid={`book-item-${book.id}`}>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg" data-testid="book-title">{book.title}</h3>
                      <p className="text-sm text-gray-600">{book.author}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <Badge variant="secondary">{book.category}</Badge>
                        <span className="text-sm text-gray-600">ISBN: {book.isbn}</span>
                        <span className="text-sm text-gray-600" data-testid="book-copies">
                          Available: {book.available_copies}/{book.total_copies}
                        </span>
                      </div>
                    </div>
                    
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => handleDeleteBook(book.id)}
                      data-testid={`delete-book-button-${book.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>All borrowing and return activities</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center py-8 text-gray-600">Loading...</p>
            ) : transactions.length === 0 ? (
              <p className="text-center py-8 text-gray-600">No transactions yet</p>
            ) : (
              <div className="space-y-3">
                {transactions.slice(0, 10).map((txn) => (
                  <div key={txn.id} className="flex items-center justify-between p-4 border rounded-lg" data-testid={`transaction-${txn.id}`}>
                    <div className="flex-1">
                      <h3 className="font-semibold" data-testid="transaction-book-title">{txn.book_title}</h3>
                      <p className="text-sm text-gray-600">Student: {txn.user_name}</p>
                      <p className="text-sm text-gray-600">
                        Borrowed: {format(new Date(txn.borrow_date), 'MMM dd, yyyy')}
                        {txn.return_date && ` | Returned: ${format(new Date(txn.return_date), 'MMM dd, yyyy')}`}
                      </p>
                    </div>
                    
                    <Badge 
                      variant={txn.status === 'borrowed' ? 'default' : txn.status === 'overdue' ? 'destructive' : 'secondary'}
                      data-testid="transaction-status"
                    >
                      {txn.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}