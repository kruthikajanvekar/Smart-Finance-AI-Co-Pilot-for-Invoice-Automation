import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
from typing import List, Dict, Tuple
from config import Config

class CustomerRAGEngine:
    def __init__(self):
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.index = None
        self.documents = []
        self.customer_contexts = {}
        
    def load_communication_history(self) -> pd.DataFrame:
        """Load customer communication history"""
        try:
            return pd.read_csv(os.path.join(Config.DATA_DIR, "communication_history.csv"))
        except Exception as e:
            print(f"Error loading communication history: {e}")
            return pd.DataFrame()
    
    def create_customer_documents(self, comm_df: pd.DataFrame) -> List[Dict]:
        """Create documents from communication history for embedding"""
        documents = []
        
        for _, row in comm_df.iterrows():
            doc = {
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'communication_id': row['communication_id'],
                'date': row['date'],
                'type': row['type'],
                'content': row['content'],
                'sentiment': row['sentiment'],
                'response_time_hours': row['response_time_hours'],
                'payment_result': row['payment_result'],
                'full_text': f"""
                Customer: {row['customer_name']}
                Date: {row['date']}
                Communication Type: {row['type']}
                Content: {row['content']}
                Customer Sentiment: {row['sentiment']}
                Response Time: {row['response_time_hours']} hours
                Outcome: {row['payment_result']}
                """
            }
            documents.append(doc)
        
        return documents
    
    def build_vector_index(self):
        """Build FAISS vector index from customer communications"""
        comm_df = self.load_communication_history()
        if comm_df.empty:
            return
        
        # Create documents
        self.documents = self.create_customer_documents(comm_df)
        
        # Extract text for embedding
        texts = [doc['full_text'] for doc in self.documents]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        # Build customer context summaries
        self._build_customer_contexts(comm_df)
        
        print(f"✅ Built vector index with {len(self.documents)} communications")
    
    def _build_customer_contexts(self, comm_df: pd.DataFrame):
        """Build customer-specific context summaries"""
        for customer_id in comm_df['customer_id'].unique():
            customer_comms = comm_df[comm_df['customer_id'] == customer_id]
            
            # Analyze communication patterns
            avg_response_time = customer_comms['response_time_hours'].mean()
            preferred_communication = customer_comms['type'].mode().iloc[0]
            success_rate = len(customer_comms[customer_comms['payment_result'].isin(['paid_full', 'paid_partial'])]) / len(customer_comms)
            recent_sentiment = customer_comms.iloc[-1]['sentiment'] if not customer_comms.empty else 'neutral'
            
            # Effective communication strategies
            successful_comms = customer_comms[customer_comms['payment_result'].isin(['paid_full', 'paid_partial'])]
            effective_tones = successful_comms['sentiment'].tolist() if not successful_comms.empty else ['neutral']
            
            self.customer_contexts[customer_id] = {
                'avg_response_time_hours': avg_response_time,
                'preferred_communication': preferred_communication,
                'payment_success_rate': success_rate,
                'recent_sentiment': recent_sentiment,
                'effective_tones': effective_tones,
                'total_communications': len(customer_comms),
                'last_communication_date': customer_comms['date'].max()
            }
    
    def search_similar_interactions(self, query: str, customer_id: str = None, top_k: int = 3) -> List[Dict]:
        """Search for similar customer interactions"""
        if self.index is None:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k * 3)  # Get more to filter
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                
                # Filter by customer if specified
                if customer_id and doc['customer_id'] != customer_id:
                    continue
                
                results.append({
                    **doc,
                    'similarity_score': float(score)
                })
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_customer_insights(self, customer_id: str) -> Dict:
        """Get comprehensive customer insights for personalized communication"""
        if customer_id not in self.customer_contexts:
            return {}
        
        context = self.customer_contexts[customer_id]
        
        # Generate insights
        insights = {
            'communication_profile': {
                'response_speed': 'fast' if context['avg_response_time_hours'] < 24 else 'slow',
                'preferred_channel': context['preferred_communication'],
                'payment_reliability': 'high' if context['payment_success_rate'] > 0.7 else 'low',
                'recent_mood': context['recent_sentiment']
            },
            'recommendations': {
                'best_tone': max(set(context['effective_tones']), key=context['effective_tones'].count),
                'follow_up_timing': f"{int(context['avg_response_time_hours'] * 1.5)} hours",
                'escalation_risk': 'low' if context['payment_success_rate'] > 0.7 else 'high'
            },
            'historical_context': {
                'total_interactions': context['total_communications'],
                'last_contact': context['last_communication_date'],
                'success_rate_percentage': round(context['payment_success_rate'] * 100, 1)
            }
        }
        
        return insights
    
    def save_index(self, filepath: str = "customer_rag_index.pkl"):
        """Save the RAG index and documents"""
        if self.index is None:
            return
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'customer_contexts': self.customer_contexts
            }, f)
        
        faiss.write_index(self.index, filepath.replace('.pkl', '.faiss'))
        print(f"✅ Saved RAG index to {filepath}")
    
    def load_index(self, filepath: str = "customer_rag_index.pkl"):
        """Load the RAG index and documents"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.customer_contexts = data['customer_contexts']
            
            self.index = faiss.read_index(filepath.replace('.pkl', '.faiss'))
            print(f"✅ Loaded RAG index from {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading RAG index: {e}")
            return False