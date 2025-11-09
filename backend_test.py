import requests
import sys
import json
from datetime import datetime

class LibraryAPITester:
    def __init__(self, base_url="https://allocationpro.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.librarian_token = None
        self.user_id = None
        self.librarian_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "status": "PASSED" if success else "FAILED",
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test student registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        student_data = {
            "student_id": f"STU{timestamp}",
            "name": f"Test Student {timestamp}",
            "email": f"student{timestamp}@test.edu",
            "password": "TestPass123!",
            "role": "student"
        }
        
        success, response = self.run_test(
            "Student Registration",
            "POST",
            "auth/register",
            200,
            data=student_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_librarian_registration(self):
        """Test librarian registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        librarian_data = {
            "student_id": f"LIB{timestamp}",
            "name": f"Test Librarian {timestamp}",
            "email": f"librarian{timestamp}@test.edu",
            "password": "LibPass123!",
            "role": "librarian"
        }
        
        success, response = self.run_test(
            "Librarian Registration",
            "POST",
            "auth/register",
            200,
            data=librarian_data
        )
        
        if success and 'token' in response:
            self.librarian_token = response['token']
            self.librarian_id = response['user']['id']
            return True
        return False

    def test_login(self):
        """Test login functionality"""
        # This assumes we have a registered user from registration test
        if not self.token:
            self.log_test("Login Test", False, "No registered user to test login")
            return False
            
        # Test with invalid credentials
        invalid_login = {
            "email": "invalid@test.edu",
            "password": "wrongpass"
        }
        
        success, _ = self.run_test(
            "Login with Invalid Credentials",
            "POST",
            "auth/login",
            401,
            data=invalid_login
        )
        
        return success

    def test_get_books(self):
        """Test getting books catalog"""
        success, response = self.run_test(
            "Get Books Catalog",
            "GET",
            "books",
            200
        )
        
        if success:
            books_count = len(response) if isinstance(response, list) else 0
            print(f"   📚 Found {books_count} books in catalog")
            return books_count > 0
        return False

    def test_book_search_and_filter(self):
        """Test book search and category filtering"""
        # Test category filter
        success, response = self.run_test(
            "Filter Books by Category",
            "GET",
            "books?category=Fiction",
            200
        )
        
        if success:
            fiction_books = len(response) if isinstance(response, list) else 0
            print(f"   📖 Found {fiction_books} Fiction books")
        
        # Test search functionality
        success2, response2 = self.run_test(
            "Search Books by Title",
            "GET",
            "books?search=the",
            200
        )
        
        return success and success2

    def test_borrow_book(self):
        """Test book borrowing functionality"""
        if not self.token:
            self.log_test("Borrow Book", False, "No authentication token")
            return False
        
        # First get available books
        success, books = self.run_test(
            "Get Books for Borrowing",
            "GET",
            "books",
            200
        )
        
        if not success or not books:
            self.log_test("Borrow Book", False, "No books available")
            return False
        
        # Find a book with available copies
        available_book = None
        for book in books:
            if book.get('available_copies', 0) > 0:
                available_book = book
                break
        
        if not available_book:
            self.log_test("Borrow Book", False, "No books with available copies")
            return False
        
        # Test borrowing
        borrow_data = {"book_id": available_book['id']}
        headers = {"Authorization": f"Bearer {self.token}"}
        
        success, response = self.run_test(
            "Borrow Available Book",
            "POST",
            "borrow",
            200,
            data=borrow_data,
            headers=headers
        )
        
        if success:
            self.borrowed_transaction_id = response.get('id')
            print(f"   📚 Successfully borrowed: {available_book['title']}")
        
        return success

    def test_borrowing_limit(self):
        """Test 3-book borrowing limit"""
        if not self.token:
            self.log_test("Borrowing Limit Test", False, "No authentication token")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get available books
        success, books = self.run_test(
            "Get Books for Limit Test",
            "GET",
            "books",
            200
        )
        
        if not success:
            return False
        
        # Try to borrow multiple books to test limit
        borrowed_count = 0
        for book in books:
            if book.get('available_copies', 0) > 0 and borrowed_count < 4:  # Try to borrow 4 to test limit
                borrow_data = {"book_id": book['id']}
                
                if borrowed_count < 3:
                    # Should succeed for first 3
                    expected_status = 200
                    test_name = f"Borrow Book {borrowed_count + 1}"
                else:
                    # Should fail for 4th book (limit exceeded)
                    expected_status = 400
                    test_name = "Borrow Book Beyond Limit"
                
                success, _ = self.run_test(
                    test_name,
                    "POST",
                    "borrow",
                    expected_status,
                    data=borrow_data,
                    headers=headers
                )
                
                if expected_status == 200 and success:
                    borrowed_count += 1
                elif expected_status == 400 and success:
                    print(f"   ✅ Borrowing limit correctly enforced at {borrowed_count} books")
                    return True
        
        return borrowed_count > 0

    def test_get_borrowed_books(self):
        """Test getting user's borrowed books"""
        if not self.token:
            self.log_test("Get Borrowed Books", False, "No authentication token")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        success, response = self.run_test(
            "Get User Borrowed Books",
            "GET",
            "transactions/borrowed",
            200,
            headers=headers
        )
        
        if success:
            borrowed_count = len(response) if isinstance(response, list) else 0
            print(f"   📚 User has {borrowed_count} borrowed books")
        
        return success

    def test_return_book(self):
        """Test book return functionality"""
        if not self.token or not hasattr(self, 'borrowed_transaction_id'):
            self.log_test("Return Book", False, "No borrowed book to return")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        return_data = {"transaction_id": self.borrowed_transaction_id}
        
        success, response = self.run_test(
            "Return Borrowed Book",
            "POST",
            "return",
            200,
            data=return_data,
            headers=headers
        )
        
        if success:
            fine = response.get('fine', 0)
            print(f"   💰 Book returned with fine: ${fine}")
        
        return success

    def test_librarian_add_book(self):
        """Test librarian adding new book"""
        if not self.librarian_token:
            self.log_test("Librarian Add Book", False, "No librarian authentication")
            return False
        
        headers = {"Authorization": f"Bearer {self.librarian_token}"}
        timestamp = datetime.now().strftime('%H%M%S')
        
        new_book = {
            "title": f"Test Book {timestamp}",
            "author": f"Test Author {timestamp}",
            "category": "Fiction",
            "isbn": f"978-{timestamp}",
            "description": "A test book for API testing",
            "total_copies": 3
        }
        
        success, response = self.run_test(
            "Librarian Add New Book",
            "POST",
            "books",
            200,
            data=new_book,
            headers=headers
        )
        
        if success:
            self.test_book_id = response.get('id')
            print(f"   📚 Added book: {new_book['title']}")
        
        return success

    def test_librarian_delete_book(self):
        """Test librarian deleting book"""
        if not self.librarian_token or not hasattr(self, 'test_book_id'):
            self.log_test("Librarian Delete Book", False, "No book to delete or no librarian auth")
            return False
        
        headers = {"Authorization": f"Bearer {self.librarian_token}"}
        
        success, _ = self.run_test(
            "Librarian Delete Book",
            "DELETE",
            f"books/{self.test_book_id}",
            200,
            headers=headers
        )
        
        return success

    def test_get_stats(self):
        """Test getting library statistics"""
        success, response = self.run_test(
            "Get Library Statistics",
            "GET",
            "stats",
            200
        )
        
        if success:
            stats = response
            print(f"   📊 Stats - Books: {stats.get('total_books', 0)}, Users: {stats.get('total_users', 0)}, Active Borrows: {stats.get('active_borrows', 0)}")
        
        return success

    def test_get_transactions(self):
        """Test getting all transactions (librarian view)"""
        if not self.librarian_token:
            self.log_test("Get All Transactions", False, "No librarian authentication")
            return False
        
        headers = {"Authorization": f"Bearer {self.librarian_token}"}
        
        success, response = self.run_test(
            "Get All Transactions",
            "GET",
            "transactions",
            200,
            headers=headers
        )
        
        if success:
            txn_count = len(response) if isinstance(response, list) else 0
            print(f"   📋 Found {txn_count} total transactions")
        
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Library Management System API Tests")
        print("=" * 60)
        
        # Authentication Tests
        print("\n📝 Testing Authentication...")
        self.test_user_registration()
        self.test_librarian_registration()
        self.test_login()
        
        # Book Catalog Tests
        print("\n📚 Testing Book Catalog...")
        self.test_get_books()
        self.test_book_search_and_filter()
        
        # Borrowing Tests
        print("\n🔄 Testing Borrowing System...")
        self.test_borrow_book()
        self.test_borrowing_limit()
        self.test_get_borrowed_books()
        self.test_return_book()
        
        # Librarian Tests
        print("\n👨‍💼 Testing Librarian Functions...")
        self.test_librarian_add_book()
        self.test_librarian_delete_book()
        
        # Statistics and Transactions
        print("\n📊 Testing Statistics and Transactions...")
        self.test_get_stats()
        self.test_get_transactions()
        
        # Print Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed. Check the details above.")
            return 1

def main():
    tester = LibraryAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())