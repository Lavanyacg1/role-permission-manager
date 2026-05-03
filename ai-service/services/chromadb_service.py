import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# Global client variable
_client = None
_collection = None

def get_client():
    """Get or create ChromaDB client."""
    global _client
    if _client is None:
        try:
            _client = chromadb.PersistentClient(
                path="./chroma_data",
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("ChromaDB client created successfully.")
        except Exception as e:
            logger.error(f"ChromaDB client error: {e}")
            _client = None
    return _client

def get_collection():
    """Get or create the knowledge collection."""
    global _collection
    client = get_client()
    if client is None:
        return None
    try:
        _collection = client.get_or_create_collection(
            name="role_knowledge",
            metadata={"description": "Domain knowledge about roles and permissions"}
        )
        return _collection
    except Exception as e:
        logger.error(f"ChromaDB collection error: {e}")
        return None

def seed_knowledge():
    """Seed ChromaDB with 10 domain knowledge documents."""
    collection = get_collection()
    if collection is None:
        logger.warning("ChromaDB not available — skipping seed.")
        return

    documents = [
        "Admin roles should follow the principle of least privilege to minimize security risks.",
        "Multi-factor authentication must be enforced for all high-privilege roles.",
        "Role-based access control ensures users only access resources needed for their job.",
        "Regular access reviews should be conducted quarterly to detect permission creep.",
        "Finance department roles require strict separation of duties to prevent fraud.",
        "HR roles with access to employee records must comply with data privacy regulations.",
        "DevOps roles with deployment permissions pose high risk and need change management.",
        "Read-only roles are low risk but should still be audited annually.",
        "User account management permissions should be restricted to a small number of admins.",
        "All role changes must be logged in an audit trail for compliance purposes."
    ]

    ids = [f"doc_{i}" for i in range(len(documents))]

    try:
        # Check if already seeded
        existing = collection.count()
        if existing >= 10:
            logger.info(f"ChromaDB already seeded with {existing} documents.")
            return

        collection.add(
            documents=documents,
            ids=ids
        )
        logger.info(f"ChromaDB seeded with {len(documents)} documents.")
    except Exception as e:
        logger.error(f"ChromaDB seed error: {e}")

def query_knowledge(query: str, n_results: int = 3) -> list:
    """Query ChromaDB for relevant knowledge."""
    collection = get_collection()
    if collection is None:
        return []
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        logger.error(f"ChromaDB query error: {e}")
        return []