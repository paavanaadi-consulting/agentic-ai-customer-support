"""
# FILE: data_sources/pdf_processor.py
PDF document processor for extracting and searching content
"""
import os
import PyPDF2
import re
from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

class PDFProcessor:
    """Process and search PDF documents for knowledge extraction"""
    
    def __init__(self, pdf_directory: str = "data/pdfs"):
        self.pdf_directory = pdf_directory
        self.logger = logging.getLogger("PDFProcessor")
        self.documents = {}
        self.vectorizer = None
        self.tfidf_matrix = None
        self.document_chunks = []
        
        # Ensure PDF directory exists
        os.makedirs(pdf_directory, exist_ok=True)
    
    async def initialize(self):
        """Initialize PDF processor and load documents"""
        await self._load_documents()
        await self._build_search_index()
    
    async def _load_documents(self):
        """Load and extract text from all PDF documents"""
        self.logger.info(f"Loading PDF documents from {self.pdf_directory}")
        
        pdf_files = [f for f in os.listdir(self.pdf_directory) if f.endswith('.pdf')]
        
        for pdf_file in pdf_files:
            file_path = os.path.join(self.pdf_directory, pdf_file)
            try:
                text_content = self._extract_text_from_pdf(file_path)
                self.documents[pdf_file] = {
                    'content': text_content,
                    'file_path': file_path,
                    'chunks': self._chunk_text(text_content)
                }
                self.logger.info(f"Loaded PDF: {pdf_file}")
                
            except Exception as e:
                self.logger.error(f"Error loading PDF {pdf_file}: {str(e)}")
        
        self.logger.info(f"Loaded {len(self.documents)} PDF documents")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from a PDF file"""
        text_content = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                except Exception as e:
                    self.logger.warning(f"Error extracting page {page_num + 1}: {str(e)}")
        
        return self._clean_text(text_content)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', '', text)
        
        # Remove very short lines (likely artifacts)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        return '\n'.join(cleaned_lines)
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
        """Split text into searchable chunks"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'chunk_index': chunk_index,
                        'length': len(current_chunk)
                    })
                    chunk_index += 1
                
                current_chunk = sentence + ". "
        
        # Add the last chunk
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'chunk_index': chunk_index,
                'length': len(current_chunk)
            })
        
        return chunks
    
    async def _build_search_index(self):
        """Build TF-IDF search index for document chunks"""
        # Collect all chunks from all documents
        self.document_chunks = []
        
        for doc_name, doc_data in self.documents.items():
            for chunk in doc_data['chunks']:
                self.document_chunks.append({
                    'document': doc_name,
                    'content': chunk['content'],
                    'chunk_index': chunk['chunk_index'],
                    'document_chunk_id': f"{doc_name}_{chunk['chunk_index']}"
                })
        
        if not self.document_chunks:
            self.logger.warning("No document chunks available for indexing")
            return
        
        # Build TF-IDF vectors
        chunk_texts = [chunk['content'] for chunk in self.document_chunks]
        
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(chunk_texts)
        
        self.logger.info(f"Built search index with {len(self.document_chunks)} chunks")
    
    async def search_documents(self, query: str, max_results: int = 10, 
                             min_similarity: float = 0.1) -> List[Dict[str, Any]]:
        """Search documents for relevant content"""
        if not self.vectorizer or not self.document_chunks:
            self.logger.warning("Search index not initialized")
            return []
        
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:max_results]
            
            results = []
            for idx in top_indices:
                similarity = similarities[idx]
                
                if similarity < min_similarity:
                    break
                
                chunk = self.document_chunks[idx]
                results.append({
                    'content': chunk['content'],
                    'document_name': chunk['document'],
                    'chunk_index': chunk['chunk_index'],
                    'relevance': float(similarity),
                    'document_chunk_id': chunk['document_chunk_id']
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def get_document_summary(self, document_name: str) -> Dict[str, Any]:
        """Get summary information about a specific document"""
        if document_name not in self.documents:
            return {}
        
        doc_data = self.documents[document_name]
        
        return {
            'document_name': document_name,
            'file_path': doc_data['file_path'],
            'content_length': len(doc_data['content']),
            'chunk_count': len(doc_data['chunks']),
            'first_100_chars': doc_data['content'][:100] + "..." if len(doc_data['content']) > 100 else doc_data['content']
        }
    
    async def add_document(self, file_path: str) -> bool:
        """Add a new PDF document to the collection"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            # Extract filename
            doc_name = os.path.basename(file_path)
            
            # Extract text
            text_content = self._extract_text_from_pdf(file_path)
            
            # Store document
            self.documents[doc_name] = {
                'content': text_content,
                'file_path': file_path,
                'chunks': self._chunk_text(text_content)
            }
            
            # Rebuild search index
            await self._build_search_index()
            
            self.logger.info(f"Added document: {doc_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding document: {str(e)}")
            return False
    
    def get_document_list(self) -> List[str]:
        """Get list of loaded document names"""
        return list(self.documents.keys())
    
    def get_total_chunks(self) -> int:
        """Get total number of document chunks"""
        return len(self.document_chunks)