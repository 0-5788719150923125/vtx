import random

import numpy as np


class EvolutionaryNeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size):
        self.weights1 = np.random.randn(input_size, hidden_size)
        self.weights2 = np.random.randn(hidden_size, output_size)

    def forward(self, X):
        self.hidden = np.tanh(np.dot(X, self.weights1))
        self.output = np.tanh(np.dot(self.hidden, self.weights2))
        return self.output

    def get_weights(self):
        return np.concatenate([self.weights1.flatten(), self.weights2.flatten()])

    def set_weights(self, weights):
        split = self.weights1.size
        self.weights1 = weights[:split].reshape(self.weights1.shape)
        self.weights2 = weights[split:].reshape(self.weights2.shape)


def mutate(weights, mutation_rate=0.1, mutation_scale=0.1):
    mutation = np.random.randn(*weights.shape) * mutation_scale
    mutation_mask = np.random.random(weights.shape) < mutation_rate
    return weights + mutation * mutation_mask


def crossover(parent1, parent2):
    crossover_point = random.randint(0, len(parent1))
    child = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
    return child


def evaluate_fitness(network, X, y):
    predictions = network.forward(X)
    mse = np.mean((predictions - y) ** 2)
    return 1 / (1 + mse)  # Higher fitness for lower error


def evolutionary_training(population_size, generations, X, y):
    input_size, hidden_size, output_size = X.shape[1], 5, y.shape[1]
    population = [
        EvolutionaryNeuralNetwork(input_size, hidden_size, output_size)
        for _ in range(population_size)
    ]

    for generation in range(generations):
        # Evaluate fitness
        fitnesses = [evaluate_fitness(network, X, y) for network in population]

        # Select parents
        parents = random.choices(population, weights=fitnesses, k=population_size)

        # Create next generation
        new_population = []
        for i in range(0, population_size, 2):
            parent1, parent2 = parents[i], parents[i + 1]
            child1_weights = mutate(
                crossover(parent1.get_weights(), parent2.get_weights())
            )
            child2_weights = mutate(
                crossover(parent2.get_weights(), parent1.get_weights())
            )

            child1, child2 = EvolutionaryNeuralNetwork(
                input_size, hidden_size, output_size
            ), EvolutionaryNeuralNetwork(input_size, hidden_size, output_size)
            child1.set_weights(child1_weights)
            child2.set_weights(child2_weights)

            new_population.extend([child1, child2])

        population = new_population

        if generation % 10 == 0:
            best_fitness = max(fitnesses)
            print(f"Generation {generation}: Best Fitness = {best_fitness}")

    return population[fitnesses.index(max(fitnesses))]


# Example usage
X = np.random.randn(100, 2)
y = (X[:, 0] > X[:, 1]).reshape(-1, 1).astype(float)

best_network = evolutionary_training(population_size=50, generations=100, X=X, y=y)
print("Training complete. Best network found.")
