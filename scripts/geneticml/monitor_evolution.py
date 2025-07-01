#!/usr/bin/env python3
"""
GeneticML Evolution Visualization and Monitoring Script
"""
import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.geneticML import EvolutionEngine, GeneticAlgorithm

class EvolutionMonitor:
    """Monitor and visualize genetic algorithm evolution"""
    
    def __init__(self, output_dir="./evolution_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log_generation(self, generation, stats, agents_info):
        """Log generation statistics"""
        log_data = {
            'generation': generation,
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'agents_info': agents_info
        }
        
        # Write to JSON log
        log_file = self.output_dir / f"evolution_log_{self.run_id}.json"
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_data)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        # Print to console
        print(f"\nGeneration {generation + 1}:")
        for agent_id, agent_stats in stats.items():
            print(f"  {agent_id}: Best={agent_stats['best_fitness']:.4f}, "
                  f"Avg={agent_stats['average_fitness']:.4f}, "
                  f"Diversity={agent_stats['diversity']:.4f}")
    
    def create_summary_report(self, evolution_results):
        """Create a summary report of evolution results"""
        report_file = self.output_dir / f"evolution_summary_{self.run_id}.md"
        
        with open(report_file, 'w') as f:
            f.write("# GeneticML Evolution Summary Report\n\n")
            f.write(f"**Run ID:** {self.run_id}\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            
            f.write("## Configuration\n")
            config = evolution_results.get('config', {})
            for key, value in config.items():
                f.write(f"- **{key}:** {value}\n")
            
            f.write("\n## Results\n")
            f.write(f"- **Total Generations:** {evolution_results.get('final_generation', 0)}\n")
            f.write(f"- **Total Interactions:** {evolution_results.get('total_interactions', 0)}\n")
            
            f.write("\n## Best Chromosomes\n")
            best_chromosomes = evolution_results.get('best_chromosomes', {})
            for agent_id, chromosome_data in best_chromosomes.items():
                f.write(f"\n### Agent: {agent_id}\n")
                f.write(f"- **Fitness:** {chromosome_data['fitness']:.4f}\n")
                f.write(f"- **Generation:** {chromosome_data['generation']}\n")
                f.write("- **Genes:**\n")
                for gene, value in chromosome_data['genes'].items():
                    f.write(f"  - {gene}: {value}\n")
        
        print(f"Summary report saved to: {report_file}")
        return report_file

class CustomEvolutionEngine(EvolutionEngine):
    """Extended evolution engine with monitoring capabilities"""
    
    def __init__(self, agents, config, monitor=None):
        super().__init__(agents, config)
        self.monitor = monitor
    
    async def evolve(self, max_generations: int = None):
        """Enhanced evolve method with monitoring"""
        max_gen = max_generations or self.config.max_generations
        
        self.logger.info(f"Starting monitored evolution for {max_gen} generations...")
        
        for generation in range(max_gen):
            self.current_generation = generation
            
            # Evolve each agent type
            generation_stats = {}
            agents_info = {}
            
            for agent_id, ga in self.genetic_algorithms.items():
                stats = await self._evolve_agent(agent_id, ga)
                generation_stats[agent_id] = stats
                
                # Collect agent info
                best_chromosome = ga.get_best_chromosome()
                agents_info[agent_id] = {
                    'best_genes': best_chromosome.genes if best_chromosome else {},
                    'population_size': len(ga.population),
                    'generation': ga.generation
                }
            
            # Monitor generation
            if self.monitor:
                self.monitor.log_generation(generation, generation_stats, agents_info)
            
            # Record generation results
            self.evolution_history.append({
                'generation': generation,
                'timestamp': datetime.now().isoformat(),
                'stats': generation_stats
            })
            
            # Check convergence
            if self._check_convergence(generation_stats):
                self.logger.info(f"Convergence achieved at generation {generation + 1}")
                break
        
        # Apply best chromosomes
        await self._apply_best_chromosomes()
        
        self.logger.info("Monitored evolution completed!")

def create_test_agents():
    """Create test agents for evolution"""
    
    class TestAgent:
        def __init__(self, agent_id, gene_template, gene_ranges):
            self.agent_id = agent_id
            self.gene_template = gene_template
            self.gene_ranges = gene_ranges
            self.chromosome = None
        
        def set_chromosome(self, chromosome):
            self.chromosome = chromosome
        
        def process_input(self, input_data):
            # Simulate processing with chromosome-influenced behavior
            success_rate = 0.5
            if self.chromosome:
                # Use chromosome genes to influence success rate
                confidence = self.chromosome.genes.get('confidence', 0.5)
                success_rate = min(0.95, confidence + 0.2)
            
            import random
            success = random.random() < success_rate
            
            return {
                'success': success,
                'content': f'Response from {self.agent_id}',
                'processing_time': random.uniform(0.1, 0.5),
                'confidence': success_rate
            }
    
    # Define agent configurations
    agents = {
        'query_agent': TestAgent(
            'query_agent',
            {
                'confidence_threshold': 0.8,
                'context_window': 1000,
                'detail_level': 'medium',
                'timeout': 5.0
            },
            {
                'confidence_threshold': (0.1, 1.0),
                'context_window': (100, 5000),
                'detail_level': ['low', 'medium', 'high'],
                'timeout': (1.0, 30.0)
            }
        ),
        'knowledge_agent': TestAgent(
            'knowledge_agent',
            {
                'search_depth': 5,
                'relevance_threshold': 0.7,
                'max_sources': 10,
                'synthesis_level': 'detailed'
            },
            {
                'search_depth': (1, 10),
                'relevance_threshold': (0.1, 1.0),
                'max_sources': (1, 20),
                'synthesis_level': ['basic', 'detailed', 'comprehensive']
            }
        ),
        'response_agent': TestAgent(
            'response_agent',
            {
                'tone': 'friendly',
                'personalization': 0.7,
                'empathy_level': 0.8,
                'length_preference': 'medium'
            },
            {
                'tone': ['professional', 'friendly', 'casual'],
                'personalization': (0.0, 1.0),
                'empathy_level': (0.0, 1.0),
                'length_preference': ['short', 'medium', 'long']
            }
        )
    }
    
    return agents

async def run_monitored_evolution(args):
    """Run evolution with monitoring and visualization"""
    
    # Configuration
    class Config:
        def __init__(self):
            self.population_size = args.population_size
            self.mutation_rate = args.mutation_rate
            self.crossover_rate = args.crossover_rate
            self.elite_size = args.elite_size
            self.max_generations = args.max_generations
            self.fitness_threshold = args.fitness_threshold
    
    # Create test agents
    agents = create_test_agents()
    
    # Create monitor
    monitor = EvolutionMonitor(args.output_dir)
    
    # Initialize evolution engine
    config = Config()
    engine = CustomEvolutionEngine(agents, config, monitor)
    await engine.initialize()
    
    print("Starting monitored evolution...")
    print(f"Configuration:")
    print(f"  Population Size: {config.population_size}")
    print(f"  Mutation Rate: {config.mutation_rate}")
    print(f"  Crossover Rate: {config.crossover_rate}")
    print(f"  Max Generations: {config.max_generations}")
    print(f"  Output Directory: {args.output_dir}")
    
    # Run evolution
    start_time = time.time()
    await engine.evolve()
    elapsed_time = time.time() - start_time
    
    # Create summary report
    results = engine.export_results()
    results['execution_time_seconds'] = elapsed_time
    
    report_file = monitor.create_summary_report(results)
    
    print(f"\nEvolution completed in {elapsed_time:.2f} seconds")
    print(f"Final status: {engine.get_status()}")
    print(f"Results saved to: {monitor.output_dir}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='GeneticML Evolution Monitor')
    parser.add_argument('--population-size', type=int, default=20, help='Population size')
    parser.add_argument('--mutation-rate', type=float, default=0.1, help='Mutation rate')
    parser.add_argument('--crossover-rate', type=float, default=0.8, help='Crossover rate')
    parser.add_argument('--elite-size', type=int, default=5, help='Elite size')
    parser.add_argument('--max-generations', type=int, default=10, help='Maximum generations')
    parser.add_argument('--fitness-threshold', type=float, default=0.9, help='Fitness threshold')
    parser.add_argument('--output-dir', default='./evolution_results', help='Output directory')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GENETICML EVOLUTION MONITOR")
    print("=" * 60)
    
    asyncio.run(run_monitored_evolution(args))

if __name__ == "__main__":
    main()
