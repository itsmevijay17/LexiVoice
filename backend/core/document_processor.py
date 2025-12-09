"""
Document processing for RAG pipeline.

Purpose: Load legal documents and split them into searchable chunks.

Key Concepts:
- Chunking: Breaking long text into smaller pieces (better for search)
- Metadata: Extra info about each chunk (title, source, country)
"""
import json
import re
from typing import List, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """
    A piece of a document with its metadata.
    
    Think of it like a highlighted paragraph in a textbook,
    with notes about which chapter/page it came from.
    """
    text: str              # The actual content
    title: str             # Document title
    section: str           # Legal section number
    source_url: str        # Where it came from
    country: str           # india/canada/usa
    category: str          # immigration/labor/civil
    chunk_id: int          # Which chunk number (0, 1, 2...)
    total_chunks: int      # How many chunks total from this document


class DocumentProcessor:
    """
    Loads and processes legal documents for RAG.
    
    Main job: Convert JSON files into searchable chunks.
    """
    
    def __init__(self, chunk_size: int = 500):
        """
        Initialize the processor.
        
        Args:
            chunk_size: Max characters per chunk (default: 500)
                       Why 500? Long enough for context, short enough for search
        """
        self.chunk_size = chunk_size
        logger.info(f"📄 DocumentProcessor initialized (chunk_size={chunk_size})")
    
    def load_documents(self, country: str) -> List[Dict]:
        """
        Load legal documents from JSON file.
        
        Args:
            country: 'india', 'canada', or 'usa'
            
        Returns:
            List of document dictionaries
        
        Example:
            docs = processor.load_documents('india')
            # Returns: [{'title': '...', 'content': '...', ...}, ...]
        """
        file_path = f"backend/data/laws/{country}.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            logger.info(f"✅ Loaded {len(documents)} documents for {country}")
            return documents
            
        except FileNotFoundError:
            logger.error(f"❌ File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {file_path}: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        What it does:
        - Removes extra whitespace (multiple spaces → single space)
        - Removes weird characters
        - Strips leading/trailing spaces
        
        Example:
            "Hello    world  \n  test" → "Hello world test"
        """
        # Replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters but keep punctuation
        text = re.sub(r'[^\x20-\x7E]', '', text)
        
        return text.strip()
    
    def split_into_chunks(self, text: str) -> List[str]:
        """
        Split text into smaller chunks.
        
        Strategy: Split by sentences, but keep chunks under max size.
        
        Why sentences? Better than splitting mid-word or mid-sentence!
        
        Args:
            text: Full document text
            
        Returns:
            List of text chunks
        
        Example:
            text = "First sentence. Second sentence. Third sentence."
            chunks = split_into_chunks(text)
            # Might return: ["First sentence. Second sentence.", "Third sentence."]
        """
        # If text is short enough, return as-is
        if len(text) <= self.chunk_size:
            return [text]
        
        # Split by sentence endings (. ! ?)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Will adding this sentence exceed chunk size?
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                # Add to current chunk
                current_chunk += (" " + sentence if current_chunk else sentence)
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # Don't forget the last chunk!
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def process_documents(self, documents: List[Dict]) -> List[DocumentChunk]:
        """
        Convert documents into chunks with metadata.
        
        This is the MAIN function that does everything:
        1. Cleans each document
        2. Splits into chunks
        3. Adds metadata to each chunk
        
        Args:
            documents: List of document dicts from JSON
            
        Returns:
            List of DocumentChunk objects ready for embedding
        """
        all_chunks = []
        
        for doc in documents:
            # Clean the content
            clean_content = self.clean_text(doc['content'])
            
            # Split into chunks
            text_chunks = self.split_into_chunks(clean_content)
            
            # Create DocumentChunk objects with metadata
            for idx, text in enumerate(text_chunks):
                chunk = DocumentChunk(
                    text=text,
                    title=doc['title'],
                    section=doc.get('section', ''),
                    source_url=doc.get('source_url', ''),
                    country=doc['country'],
                    category=doc['category'],
                    chunk_id=idx,
                    total_chunks=len(text_chunks)
                )
                all_chunks.append(chunk)
        
        logger.info(f"✅ Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks
    
    def get_statistics(self, chunks: List[DocumentChunk]) -> Dict:
        """
        Calculate statistics about the chunks.
        
        Useful for understanding your data!
        
        Returns:
            Dictionary with stats like total chunks, avg length, etc.
        """
        if not chunks:
            return {}
        
        chunk_lengths = [len(c.text) for c in chunks]
        
        stats = {
            'total_chunks': len(chunks),
            'total_documents': len(set(c.title for c in chunks)),
            'avg_chunk_length': sum(chunk_lengths) / len(chunk_lengths),
            'min_chunk_length': min(chunk_lengths),
            'max_chunk_length': max(chunk_lengths),
            'chunks_by_country': {},
            'chunks_by_category': {}
        }
        
        # Count chunks per country
        for chunk in chunks:
            country = chunk.country
            stats['chunks_by_country'][country] = \
                stats['chunks_by_country'].get(country, 0) + 1
        
        # Count chunks per category
        for chunk in chunks:
            category = chunk.category
            stats['chunks_by_category'][category] = \
                stats['chunks_by_category'].get(category, 0) + 1
        
        return stats