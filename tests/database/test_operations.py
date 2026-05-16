"""
Database Tests - data-intensive operations
These run on on-premise HCI with high-performance storage
"""

import pytest
import psycopg2
from datetime import datetime


class TestDatabaseOperations:
    """Tests for database operations"""
    
    @pytest.fixture
    def db_connection(self):
        """Database connection fixture"""
        conn = psycopg2.connect(
            host="localhost",
            database="testdb",
            user="testuser",
            password="testpass"
        )
        yield conn
        conn.close()
    
    def test_bulk_insert_performance(self, db_connection):
        """Test bulk insert performance"""
        cursor = db_connection.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                created_at TIMESTAMP
            )
        """)
        
        # Bulk insert 10,000 records
        start_time = datetime.now()
        
        data = [
            (f"User {i}", f"user{i}@test.com", datetime.now())
            for i in range(10000)
        ]
        
        cursor.executemany(
            "INSERT INTO test_users (name, email, created_at) VALUES (%s, %s, %s)",
            data
        )
        db_connection.commit()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Assert performance
        assert duration < 5.0, f"Bulk insert took {duration}s, expected < 5s"
        
        # Verify count
        cursor.execute("SELECT COUNT(*) FROM test_users")
        count = cursor.fetchone()[0]
        assert count >= 10000
        
        # Cleanup
        cursor.execute("DROP TABLE test_users")
        db_connection.commit()
    
    def test_query_performance(self, db_connection):
        """Test query performance on large dataset"""
        cursor = db_connection.cursor()
        
        # Create indexed table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                category VARCHAR(50),
                price DECIMAL(10, 2),
                created_at TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON products(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price ON products(price)")
        
        # Query should use index
        start_time = datetime.now()
        
        cursor.execute("""
            SELECT * FROM products 
            WHERE category = 'Electronics' AND price > 100.00
            LIMIT 100
        """)
        
        results = cursor.fetchall()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Assert query performance
        assert duration < 1.0, f"Query took {duration}s, expected < 1s"
        
        # Cleanup
        cursor.execute("DROP TABLE products")
        db_connection.commit()
