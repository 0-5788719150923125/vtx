import csv
import os
import random
import shutil
import sys

sys.path.append("/src")

from common import get_identity

root_dir = "/lab/structure"

num_samples = 100000


# Create interesting structures
def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    def get_samples(count):
        samples = []
        i = 0
        while i < count:
            block = get_identity()
            samples.append([block, block[::-1]])
            i = i + 1
        return samples

    def get_random_samples(count):
        samples = []
        i = 0
        while i < count:
            samples.append([get_identity(), get_identity()])
            i = i + 1
        return samples

    with open(f"{root_dir}/train/random.csv", "w", newline="") as file:
        agents = get_random_samples(num_samples)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        csvwriter.writerows(agents[1:])

    with open(f"{root_dir}/train/mirror.csv", "w", newline="") as file:
        agents = get_samples(num_samples)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        csvwriter.writerows(agents[1:])

    with open(f"{root_dir}/train/left-sorted-mirror.csv", "w", newline="") as file:
        agents = get_samples(num_samples)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        sorted_list = sorted(agents, key=lambda x: int(x[0]), reverse=False)
        csvwriter.writerows(sorted_list)

    with open(f"{root_dir}/train/right-sorted-mirror.csv", "w", newline="") as file:
        agents = get_samples(num_samples)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        sorted_list = sorted(agents, key=lambda x: int(x[1]), reverse=True)
        csvwriter.writerows(sorted_list)

    def random_fibonacci_list(length):
        """
        Generates a list of Fibonacci numbers of the given length, starting at a random position in the Fibonacci sequence.
        """
        fibonacci_list = []
        a, b = 0, 1
        for i in range(random.randint(0, length)):
            # advance the Fibonacci sequence to a random position
            a, b = b, a + b
        fibonacci_list.append(a)
        fibonacci_list.append(b)
        for i in range(length - 2):
            # generate the next Fibonacci number by summing the previous two
            next_fibonacci = fibonacci_list[-1] + fibonacci_list[-2]
            fibonacci_list.append(next_fibonacci)
        return fibonacci_list

    with open(f"{root_dir}/train/fibonacci.csv", "w", newline="") as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(
            [
                "one",
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
                "eight",
                "nine",
                "ten",
                "eleven",
                "twelve",
                "thirteen",
                "fourteen",
                "fifteen",
                "sixteen",
                "seventeen",
                "eighteen",
                "nineteen",
                "twenty",
                "twenty-one",
                "twenty-two",
                "twenty-three",
            ]
        )
        i = 0
        numbers = []
        count = num_samples / 10
        while i < count:
            sequence = random_fibonacci_list(23)
            if random.random() < 0.5:
                sequence.reverse()
            numbers.append(sequence)
            i = i + 1
        csvwriter.writerows(numbers)


if __name__ == "__main__":
    main()
