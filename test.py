import matplotlib.pyplot as plt
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler


class MyDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]


# Create a larger dataset
num_samples = 1000
data = list(range(1, num_samples + 1))
dataset = MyDataset(data)

# Generate random weights
weights = np.random.rand(num_samples)
weights /= weights.sum()  # Normalize the weights

# Create a WeightedRandomSampler
generator = torch.Generator().manual_seed(42)  # Fixed seed for reproducibility
sampler = WeightedRandomSampler(
    weights, num_samples=num_samples, replacement=True, generator=generator
)

# Create a data loader
batch_size = 32
data_loader = DataLoader(dataset, batch_size=batch_size, sampler=sampler)

# Calculate the number of batches
num_batches = len(data_loader)


def calculate_coverage(weights, num_draws):
    probabilities = 1 - np.exp(-weights * num_draws / np.sum(weights))
    return np.mean(probabilities)


# Calculate coverage for each batch
coverages = [
    calculate_coverage(weights, i * batch_size) for i in range(1, num_batches + 1)
]

# Print the estimated coverage of the dataset after every batch
print("Estimated coverage of the dataset over an epoch:")
for i, coverage in enumerate(coverages, 1):
    print(
        f"After batch {i}: {coverage * 100:.2f}% of the dataset is expected to be seen"
    )

# Plot the coverage
plt.figure(figsize=(10, 6))
plt.plot(range(1, num_batches + 1), coverages)
plt.title("Dataset Coverage Over Batches")
plt.xlabel("Number of Batches")
plt.ylabel("Expected Dataset Coverage")
plt.grid(True)
plt.show()
