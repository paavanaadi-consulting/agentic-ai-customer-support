"""
Fitness evaluation system for genetic algorithm
"""
import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass
import logging

@dataclass
class FitnessMetrics:
    """Container for fitness evaluation metrics"""
    accuracy: float = 0.0
    response_time: float = 0.0
    customer_satisfaction: float = 0.0
    resolution_rate: float = 0.0
    consistency: float = 0.0
    
    def weighted_score(self, weights: Dict[str, float] = None) -> float:
        """Calculate weighted fitness score"""
        if weights is None:
            weights = {
                'accuracy': 0.25,
                'response_time': 0.20,
                'customer_satisfaction': 0.25,
                'resolution_rate': 0.20,
                'consistency': 0.10
            }
        
        score = (
            weights['accuracy'] * self.accuracy +
            weights['response_time'] * (1.0 / (1.0 + self.response_time)) +
            weights['customer_satisfaction'] * self.customer_satisfaction +
            weights['resolution_rate'] * self.resolution_rate +
            weights['consistency'] * self.consistency
        )
        
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1

class FitnessEvaluator:
    """Evaluates fitness of agent chromosomes"""
    
    def __init__(self):
        self.logger = logging.getLogger("FitnessEvaluator")
        self.historical_data = []
        self.baseline_metrics = None
    
    def evaluate_chromosome(self, chromosome, agent, test_cases: List[Dict[str, Any]]) -> float:
        """Evaluate fitness of a chromosome using test cases"""
        if not test_cases:
            return 0.0
        
        # Apply chromosome strategy to agent
        agent.set_chromosome(chromosome)
        
        # Run test cases
        results = []
        for test_case in test_cases:
            try:
                result = agent.process_input(test_case['input'])
                results.append({
                    'test_case': test_case,
                    'result': result,
                    'expected': test_case.get('expected', {}),
                    'success': result.get('success', False)
                })
            except Exception as e:
                self.logger.warning(f"Test case failed: {str(e)}")
                results.append({
                    'test_case': test_case,
                    'result': {'error': str(e)},
                    'success': False
                })
        
        # Calculate fitness metrics
        metrics = self._calculate_metrics(results)
        
        # Return weighted fitness score
        fitness = metrics.weighted_score()
        chromosome.fitness = fitness
        
        return fitness
    
    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> FitnessMetrics:
        """Calculate fitness metrics from test results"""
        if not results:
            return FitnessMetrics()
        
        # Accuracy: percentage of successful responses
        successful = sum(1 for r in results if r['success'])
        accuracy = successful / len(results)
        
        # Response time: average processing time (normalized)
        response_times = [
            r['result'].get('processing_time', 0.0) 
            for r in results if 'processing_time' in r['result']
        ]
        avg_response_time = np.mean(response_times) if response_times else 0.0
        
        # Customer satisfaction: based on expected vs actual results
        satisfaction_scores = []
        for result in results:
            if result['success'] and 'expected' in result['test_case']:
                expected = result['test_case']['expected']
                actual = result['result']
                
                # Simple similarity scoring (can be enhanced)
                similarity = self._calculate_similarity(expected, actual)
                satisfaction_scores.append(similarity)
        
        customer_satisfaction = np.mean(satisfaction_scores) if satisfaction_scores else 0.0
        
        # Resolution rate: percentage of queries that got meaningful responses
        meaningful_responses = sum(
            1 for r in results 
            if r['success'] and len(str(r['result'].get('content', ''))) > 10
        )
        resolution_rate = meaningful_responses / len(results)
        
        # Consistency: variance in response quality
        if len(satisfaction_scores) > 1:
            consistency = 1.0 - np.std(satisfaction_scores)
        else:
            consistency = 1.0 if satisfaction_scores and satisfaction_scores[0] > 0.5 else 0.0
        
        return FitnessMetrics(
            accuracy=accuracy,
            response_time=avg_response_time,
            customer_satisfaction=customer_satisfaction,
            resolution_rate=resolution_rate,
            consistency=max(0.0, consistency)
        )
    
    def _calculate_similarity(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Calculate similarity between expected and actual results"""
        # Simple similarity calculation (can be enhanced with semantic similarity)
        common_keys = set(expected.keys()) & set(actual.keys())
        if not common_keys:
            return 0.0
        
        similarity_scores = []
        for key in common_keys:
            exp_val = str(expected[key]).lower()
            act_val = str(actual.get(key, '')).lower()
            
            if exp_val == act_val:
                similarity_scores.append(1.0)
            elif exp_val in act_val or act_val in exp_val:
                similarity_scores.append(0.7)
            else:
                # Jaccard similarity for text
                exp_words = set(exp_val.split())
                act_words = set(act_val.split())
                if exp_words or act_words:
                    jaccard = len(exp_words & act_words) / len(exp_words | act_words)
                    similarity_scores.append(jaccard)
                else:
                    similarity_scores.append(0.0)
        
        return np.mean(similarity_scores) if similarity_scores else 0.0
