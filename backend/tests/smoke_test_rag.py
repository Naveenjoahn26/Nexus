"""
NEXUS EDU — RAG Pipeline Smoke Test.

End-to-end test: create a sample document → ingest → retrieve → verify.
"""

import asyncio
import tempfile
import os
import sys

# Ensure we're running from the backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SAMPLE_CONTENT = """
Introduction to Data Structures

A data structure is a way of organizing and storing data so that it can be accessed
and modified efficiently. Different data structures are suited to different kinds of
applications, and some are highly specialized to specific tasks.

Arrays

An array is a collection of elements stored at contiguous memory locations. The idea
is to store multiple items of the same type together. This makes it easier to calculate
the position of each element by simply adding an offset to a base value. Arrays allow
random access to elements, meaning any element can be accessed directly if its index
is known.

The time complexity for accessing an element in an array is O(1), which makes arrays
extremely efficient for lookup operations. However, inserting or deleting elements
requires shifting elements, resulting in O(n) time complexity.

Linked Lists

A linked list is a linear data structure where each element is a separate object called
a node. Each node contains two fields: the data and a reference to the next node in the
sequence. Unlike arrays, linked lists do not store elements in contiguous memory locations.

The main advantage of linked lists over arrays is that insertion and deletion operations
can be performed in O(1) time if we have a reference to the node. However, accessing an
element requires traversal from the head, resulting in O(n) time complexity.

Binary Search Trees

A Binary Search Tree (BST) is a tree data structure in which each node has at most two
children, referred to as the left child and the right child. For each node, all elements
in the left subtree are less than the node, and all elements in the right subtree are
greater than the node.

The average time complexity for search, insertion, and deletion in a BST is O(log n).
However, in the worst case (when the tree becomes a skewed tree), the time complexity
degrades to O(n). Balanced BSTs like AVL trees and Red-Black trees maintain O(log n)
complexity in all cases.

Hash Tables

A hash table is a data structure that implements an associative array abstract data type,
a structure that maps keys to values. A hash table uses a hash function to compute an
index into an array of buckets or slots, from which the desired value can be found.

Hash tables provide O(1) average time complexity for search, insertion, and deletion
operations. However, in the worst case, when many keys hash to the same bucket (collision),
the time complexity can degrade to O(n). Common collision resolution strategies include
chaining and open addressing.

Dijkstra's Algorithm

Dijkstra's algorithm is a graph search algorithm that solves the single-source shortest
path problem for a graph with non-negative edge weights. It was conceived by computer
scientist Edsger W. Dijkstra in 1956 and published three years later.

The algorithm maintains a set of vertices whose shortest distance from the source is
already known. At each step, it selects the vertex with the minimum distance value,
adds it to the set, and updates the distance values of its adjacent vertices.
"""


async def main():
    from app.ai.rag.pipeline import RAGPipeline

    print("=" * 60)
    print("NEXUS EDU — RAG Pipeline Smoke Test")
    print("=" * 60)

    # Create a temp file with sample content
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_CONTENT)
        temp_path = f.name

    try:
        # Initialize pipeline
        print("\n[1] Initializing RAG pipeline...")
        pipeline = RAGPipeline()
        print("    [OK] Pipeline initialized.")

        # Ingest document
        print("\n[2] Ingesting sample document...")
        result = await pipeline.ingest(
            document_id="test_doc_001",
            file_path=temp_path,
            course_id="cs101",
            metadata={"title": "Data Structures Notes"},
        )
        print(f"    [OK] Ingested: {result.child_chunk_count} child + {result.parent_chunk_count} parent chunks")

        # Test queries
        queries = [
            ("What is the time complexity of array access?", False),
            ("Dijkstra's algorithm", False),
            ("linked list vs array", False),
            ("What are hash tables?", True),  # With parent expansion
        ]

        for query, use_parent in queries:
            print(f"\n[3] Query: '{query}' (parent={'on' if use_parent else 'off'})")
            chunks = await pipeline.retrieve(
                query=query,
                course_id="cs101",
                top_k=3,
                use_parent=use_parent,
            )
            for i, chunk in enumerate(chunks):
                preview = chunk.content[:120].replace("\n", " ")
                print(f"    [{i+1}] score={chunk.score:.4f} | {preview}...")

        # Test deletion
        print("\n[4] Deleting document...")
        deleted = await pipeline.delete_document("test_doc_001", "cs101")
        print(f"    [OK] Deleted {deleted} chunks.")

        # Verify empty results after deletion
        post_delete = await pipeline.retrieve("arrays", "cs101", top_k=3)
        print(f"    [OK] Post-delete retrieval: {len(post_delete)} results (expected 0).")

        # Cleanup course
        await pipeline.delete_course("cs101")

        print("\n" + "=" * 60)
        print("SMOKE TEST PASSED [OK]")
        print("=" * 60)

    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    asyncio.run(main())
