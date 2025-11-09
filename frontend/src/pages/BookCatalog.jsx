import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Search, Filter, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { api } from '@/App';
import { toast } from 'sonner';

export default function BookCatalog({ user, onLogout }) {
  const navigate = useNavigate();
  const [books, setBooks] = useState([]);
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  useEffect(() => {
    fetchBooks();
  }, []);

  useEffect(() => {
    filterBooks();
  }, [searchQuery, categoryFilter, books]);

  const fetchBooks = async () => {
    try {
      const response = await api.get('/books');
      setBooks(response.data);
      setFilteredBooks(response.data);
    } catch (error) {
      toast.error('Failed to fetch books');
    } finally {
      setLoading(false);
    }
  };

  const filterBooks = () => {
    let filtered = books;

    if (categoryFilter !== 'all') {
      filtered = filtered.filter(book => book.category === categoryFilter);
    }

    if (searchQuery) {
      filtered = filtered.filter(book => 
        book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        book.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
        book.isbn.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredBooks(filtered);
  };

  const handleBorrow = async (bookId) => {
    try {
      await api.post('/borrow', { book_id: bookId });
      toast.success('Book borrowed successfully!');
      fetchBooks();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to borrow book');
    }
  };

  const categories = ['all', ...new Set(books.map(book => book.category))];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Button variant="ghost" onClick={() => navigate('/dashboard')} data-testid="back-button">
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Book Catalog</h1>
                <p className="text-sm text-gray-600">{filteredBooks.length} books available</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Search and Filter */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                placeholder="Search by title, author, or ISBN..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                data-testid="search-input"
              />
            </div>
            
            <div className="flex items-center space-x-2">
              <Filter className="text-gray-400 w-5 h-5" />
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger data-testid="category-filter">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category === 'all' ? 'All Categories' : category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>

      {/* Books Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <p className="text-center py-12 text-gray-600">Loading books...</p>
        ) : filteredBooks.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No books found</p>
            <p className="text-gray-500 text-sm mt-2">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredBooks.map((book) => (
              <Card key={book.id} className="hover:shadow-lg transition-shadow" data-testid={`book-card-${book.id}`}>
                <CardHeader className="space-y-2">
                  <div className="aspect-[3/4] bg-gradient-to-br from-purple-100 to-purple-200 rounded-lg flex items-center justify-center mb-3">
                    {book.image_url ? (
                      <img src={book.image_url} alt={book.title} className="w-full h-full object-cover rounded-lg" />
                    ) : (
                      <BookOpen className="w-12 h-12 text-purple-600" />
                    )}
                  </div>
                  <div className="space-y-1">
                    <CardTitle className="text-lg line-clamp-2" data-testid="book-title">{book.title}</CardTitle>
                    <CardDescription className="line-clamp-1" data-testid="book-author">{book.author}</CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="secondary" data-testid="book-category">{book.category}</Badge>
                    <span className="text-sm text-gray-600" data-testid="book-availability">
                      {book.available_copies}/{book.total_copies} available
                    </span>
                  </div>
                  
                  {book.description && (
                    <p className="text-sm text-gray-600 line-clamp-2" data-testid="book-description">{book.description}</p>
                  )}
                  
                  <Button 
                    className="w-full" 
                    disabled={book.available_copies === 0}
                    onClick={() => handleBorrow(book.id)}
                    data-testid={`borrow-button-${book.id}`}
                  >
                    {book.available_copies === 0 ? 'Not Available' : 'Borrow Book'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}