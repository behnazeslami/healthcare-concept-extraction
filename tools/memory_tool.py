"""
Memory Tool - Stores and retrieves successful extraction examples for few-shot learning
Enables agent to learn from feedback and past successes
"""

import logging
from typing import List, Dict, Optional
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryTool:
    """
    Agent memory for few-shot learning.
    Stores successful extractions and retrieves similar examples.
    """
    
    def __init__(self, memory_file: str = "agent_memory.json"):
        """
        Initialize memory tool.
        
        Args:
            memory_file: Path to JSON file storing memory
        """
        self.memory_file = Path(memory_file)
        self.memory = self._load_memory()
    
    def _load_memory(self) -> List[Dict]:
        """Load memory from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
                return []
        return []
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def store_success(self, clinical_text: str, concepts: List[str], 
                     main_note: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Store a successful extraction in memory.
        
        Args:
            clinical_text: Input text
            concepts: Successfully extracted concepts
            main_note: Context note
            metadata: Additional metadata (confidence, tools_used, etc.)
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'clinical_text': clinical_text,
            'concepts': concepts,
            'main_note': main_note,
            'metadata': metadata or {}
        }
        
        self.memory.append(entry)
        self._save_memory()
        
        logger.info(f"Stored successful extraction in memory. Total entries: {len(self.memory)}")
    
    def store_feedback(self, clinical_text: str, predicted: List[str], 
                      correct: List[str], notes: Optional[str] = None):
        """
        Store user feedback for learning.
        
        Args:
            clinical_text: Input text
            predicted: Agent's prediction
            correct: User's correction
            notes: Optional user notes
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'clinical_text': clinical_text,
            'predicted_concepts': predicted,
            'correct_concepts': correct,
            'user_notes': notes,
            'feedback': True
        }
        
        self.memory.append(entry)
        self._save_memory()
        
        logger.info(f"Stored feedback in memory. Total entries: {len(self.memory)}")
    
    def retrieve_similar(self, clinical_text: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve similar past examples for few-shot learning.
        
        Args:
            clinical_text: Current text to match
            top_k: Number of similar examples to return
        
        Returns:
            List of similar memory entries
        """
        if not self.memory:
            return []
        
        # Simple similarity: word overlap (in production: use embeddings)
        similarities = []
        current_words = set(clinical_text.lower().split())
        
        for entry in self.memory:
            entry_words = set(entry['clinical_text'].lower().split())
            overlap = len(current_words & entry_words)
            similarity = overlap / len(current_words | entry_words) if current_words | entry_words else 0
            similarities.append((similarity, entry))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        similar = [entry for sim, entry in similarities[:top_k] if sim > 0.1]
        
        if similar:
            logger.info(f"Retrieved {len(similar)} similar examples from memory")
        
        return similar
    
    def build_few_shot_prompt(self, clinical_text: str, similar_examples: List[Dict]) -> str:
        """
        Build few-shot prompt using similar examples.
        
        Args:
            clinical_text: Current text
            similar_examples: Similar past examples
        
        Returns:
            Few-shot prompt string
        """
        if not similar_examples:
            return clinical_text
        
        prompt = "Here are some similar examples:\n\n"
        
        for i, example in enumerate(similar_examples, 1):
            concepts_str = ", ".join(example.get('concepts', []) or example.get('correct_concepts', []))
            prompt += f"Example {i}:\n"
            prompt += f"Text: {example['clinical_text']}\n"
            prompt += f"Concepts: {concepts_str}\n\n"
        
        prompt += f"Now extract concepts from:\nText: {clinical_text}\n"
        
        return prompt
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about memory"""
        if not self.memory:
            return {'total_entries': 0}
        
        feedback_count = sum(1 for e in self.memory if e.get('feedback', False))
        
        return {
            'total_entries': len(self.memory),
            'feedback_entries': feedback_count,
            'success_entries': len(self.memory) - feedback_count,
            'oldest_entry': self.memory[0]['timestamp'] if self.memory else None,
            'newest_entry': self.memory[-1]['timestamp'] if self.memory else None
        }