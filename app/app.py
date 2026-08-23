import os
import psycopg2
import logging
from flask import Flask, jsonify, render_template, request

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load DB Configurations from environment variables
DB_PRIMARY_HOST = os.environ.get("DB_PRIMARY_HOST", "")
DB_REPLICA_HOST = os.environ.get("DB_REPLICA_HOST", "")
DB_NAME = os.environ.get("DB_NAME", "webappdb")
DB_USER = os.environ.get("DB_USER", "dbadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Fallback for testing/local environments when DB is not configured
IS_LOCAL_TEST = not DB_PRIMARY_HOST

def get_db_connection(host, host_type="Primary"):
    """Establish a connection to the specified database host with SSL enforced."""
    if IS_LOCAL_TEST:
        # Mock connection or raise error which we catch in mock
        raise psycopg2.OperationalError("Database host not configured. Running in mock/test mode.")
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=5432,
            sslmode="require", # Enforce encryption in-transit
            connect_timeout=5
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to {host_type} DB at {host}: {e}")
        raise e

def get_primary_connection():
    return get_db_connection(DB_PRIMARY_HOST, "Primary")

def get_replica_connection():
    return get_db_connection(DB_REPLICA_HOST, "Read Replica")

def init_db():
    """Create tables and insert initial sample data on the primary database."""
    if IS_LOCAL_TEST:
        logger.info("Local/Test mode: Skipping DB initialization.")
        return
    
    conn = None
    try:
        conn = get_primary_connection()
        cur = conn.cursor()
        
        # Create Items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price NUMERIC(10, 2) NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create Audits table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id SERIAL PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Check if tables are empty, insert sample records if so
        cur.execute("SELECT COUNT(*) FROM items;")
        count = cur.fetchone()[0]
        if count == 0:
            logger.info("Initializing tables with sample data...")
            sample_items = [
                ("Enterprise Server Rack", "Standard 42U Server Rack for data center deployments", 1299.99, 15),
                ("Fibre Channel Switch", "High-speed SAN switch with 24 active ports", 4500.00, 5),
                ("LTO-9 Tape Library", "Automated tape drive storage for long-term backups", 8999.00, 2),
                ("Gigabit Firewall Appliance", "Next-gen enterprise firewall with IPSec VPN support", 750.50, 20),
                ("Category 6A Ethernet Cable 1000ft", "Solid copper spool for high bandwidth runs", 220.00, 50)
            ]
            for item in sample_items:
                cur.execute(
                    "INSERT INTO items (name, description, price, quantity) VALUES (%s, %s, %s, %s) RETURNING id;",
                    item
                )
                item_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO audits (action, item_id, details) VALUES (%s, %s, %s);",
                    ("INITIALIZATION", item_id, f"Seeded sample item '{item[0]}' with price ${item[2]}.")
                )
        
        conn.commit()
        cur.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# Initialize database on startup
init_db()

@app.route('/health')
def health():
    """Health check endpoint for ALB target group."""
    status = {"status": "healthy", "database_configured": not IS_LOCAL_TEST}
    if not IS_LOCAL_TEST:
        try:
            conn = get_primary_connection()
            conn.close()
            status["primary_db"] = "connected"
        except Exception as e:
            status["primary_db"] = f"error: {str(e)}"
            return jsonify(status), 500
    else:
        status["primary_db"] = "mock_mode"
    return jsonify(status), 200

@app.route('/')
def index():
    """Render the dashboard UI."""
    return render_template('index.html')

@app.route('/api/items', methods=['GET'])
def get_items():
    """Retrieve all items from the Primary database (transactional read)."""
    if IS_LOCAL_TEST:
        # Mock data for local development/testing
        mock_items = [
            {"id": 1, "name": "Mock Item A", "description": "Mock description A", "price": 10.00, "quantity": 5},
            {"id": 2, "name": "Mock Item B", "description": "Mock description B", "price": 20.00, "quantity": 10}
        ]
        return jsonify({"source": "Mock (Local)", "items": mock_items})
    
    conn = None
    try:
        conn = get_primary_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, price, quantity, created_at FROM items ORDER BY id DESC;")
        rows = cur.fetchall()
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "price": float(r[3]),
                "quantity": r[4],
                "created_at": r[5].isoformat()
            })
        cur.close()
        return jsonify({"source": "Primary Database", "items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/items', methods=['POST'])
def add_item():
    """Create a new item in the Primary database (transactional write)."""
    data = request.json or {}
    name = data.get("name")
    description = data.get("description", "")
    price = data.get("price")
    quantity = data.get("quantity")
    
    if not name or price is None or quantity is None:
        return jsonify({"error": "Missing required fields: name, price, quantity"}), 400
    
    if IS_LOCAL_TEST:
        return jsonify({
            "source": "Mock (Local)",
            "message": "Item added successfully (mocked)",
            "item": {"name": name, "price": price, "quantity": quantity}
        }), 201
    
    conn = None
    try:
        conn = get_primary_connection()
        cur = conn.cursor()
        
        # Insert Item
        cur.execute(
            "INSERT INTO items (name, description, price, quantity) VALUES (%s, %s, %s, %s) RETURNING id, created_at;",
            (name, description, price, quantity)
        )
        r = cur.fetchone()
        item_id = r[0]
        created_at = r[1]
        
        # Insert Audit Log
        cur.execute(
            "INSERT INTO audits (action, item_id, details) VALUES (%s, %s, %s);",
            ("CREATE_ITEM", item_id, f"Created new item '{name}' via web application dashboard.")
        )
        
        conn.commit()
        cur.close()
        return jsonify({
            "source": "Primary Database",
            "message": "Item added successfully",
            "item": {
                "id": item_id,
                "name": name,
                "description": description,
                "price": float(price),
                "quantity": int(quantity),
                "created_at": created_at.isoformat()
            }
        }), 201
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/report', methods=['GET'])
def get_report():
    """
    Retrieve inventory aggregate reports from the Read Replica database.
    Runs a complex query joining items and audits table with aggregate calculations.
    """
    if IS_LOCAL_TEST:
        # Mock data for local testing
        mock_report = [
            {"name": "Mock Item A", "action_count": 3, "inventory_value": 50.00, "avg_price": 10.00},
            {"name": "Mock Item B", "action_count": 1, "inventory_value": 200.00, "avg_price": 20.00}
        ]
        return jsonify({"source": "Mock (Local)", "report": mock_report})
    
    conn = None
    try:
        # Connect to Read Replica
        conn = get_replica_connection()
        cur = conn.cursor()
        
        # Run complex query with joins and aggregations
        complex_query = """
            SELECT 
                i.name,
                COUNT(a.id) AS action_count,
                SUM(i.price * i.quantity) AS inventory_value,
                AVG(i.price) AS avg_price
            FROM items i
            LEFT JOIN audits a ON i.id = a.item_id
            GROUP BY i.id, i.name
            ORDER BY inventory_value DESC;
        """
        cur.execute(complex_query)
        rows = cur.fetchall()
        
        report = []
        for r in rows:
            report.append({
                "name": r[0],
                "action_count": r[1],
                "inventory_value": float(r[2]) if r[2] is not None else 0.0,
                "avg_price": float(r[3]) if r[3] is not None else 0.0
            })
        cur.close()
        return jsonify({"source": "Read Replica Database", "report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/db-status', methods=['GET'])
def db_status():
    """Retrieve connection SSL parameters and host definitions to verify security settings."""
    status = {
        "primary_configured": bool(DB_PRIMARY_HOST),
        "replica_configured": bool(DB_REPLICA_HOST),
        "primary_host": DB_PRIMARY_HOST,
        "replica_host": DB_REPLICA_HOST,
        "ssl_mode_requested": "require"
    }
    
    if IS_LOCAL_TEST:
        status["primary_ssl_active"] = False
        status["replica_ssl_active"] = False
        status["connection_notes"] = "Running in mock/local mode."
        return jsonify(status)
    
    # Check Primary SSL
    try:
        conn = get_primary_connection()
        cur = conn.cursor()
        # Query pg_stat_ssl to get current connection status
        cur.execute("SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid();")
        r = cur.fetchone()
        status["primary_ssl_active"] = r[0] if r else False
        status["primary_ssl_version"] = r[1] if r else None
        status["primary_ssl_cipher"] = r[2] if r else None
        cur.close()
        conn.close()
    except Exception as e:
        status["primary_ssl_active"] = False
        status["primary_ssl_error"] = str(e)
        
    # Check Replica SSL
    try:
        conn = get_replica_connection()
        cur = conn.cursor()
        cur.execute("SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid();")
        r = cur.fetchone()
        status["replica_ssl_active"] = r[0] if r else False
        status["replica_ssl_version"] = r[1] if r else None
        status["replica_ssl_cipher"] = r[2] if r else None
        cur.close()
        conn.close()
    except Exception as e:
        status["replica_ssl_active"] = False
        status["replica_ssl_error"] = str(e)
        
    return jsonify(status)

if __name__ == '__main__':
    # Running locally
    app.run(host='0.0.0.0', port=5000, debug=True)
