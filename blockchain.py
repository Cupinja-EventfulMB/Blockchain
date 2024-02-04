import hashlib
import time

class Block:
    def __init__(self, index, data, timestamp, previous_hash, difficulty):
        self.index = index
        self.data = data
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.token = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        return hashlib.sha256(
            f"{self.index}{self.data}{self.timestamp}{self.previous_hash}{self.difficulty}{self.token}".encode()).hexdigest()

    def mine_block(self):
        while self.hash[:self.difficulty] != '0' * self.difficulty:
            self.token += 1
            self.hash = self.calculate_hash()

class Blockchain:
    def __init__(self, creation_interval, adjustment_interval):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 1
        self.block_creation_interval = creation_interval
        self.adjustment_interval = adjustment_interval

    def create_genesis_block(self):
        return Block(0, 'Genesis Block', time.time(), '0', self.difficulty)

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        if self.is_valid_new_block(new_block, self.get_last_block()):
            self.chain.append(new_block)

    def is_valid_new_block(self, new_block, previous_block):
        if previous_block.index + 1 != new_block.index:
            return False
        if previous_block.hash != new_block.previous_hash:
            return False
        if new_block.calculate_hash() != new_block.hash:
            return False
        return True

    def adjust_difficulty(self):
        if len(self.chain) % self.adjustment_interval == 0:
            return self.calculate_adjusted_difficulty()
        return self.difficulty

    def calculate_adjusted_difficulty(self):
        last_adjustment_block = self.chain[-self.adjustment_interval]
        expected_time = self.block_creation_interval * self.adjustment_interval
        actual_time = self.get_last_block().timestamp - last_adjustment_block.timestamp
        if actual_time < expected_time / 2:
            return last_adjustment_block.difficulty + 1
        elif actual_time > expected_time * 2:
            return max(1, last_adjustment_block.difficulty - 1)
        else:
            return last_adjustment_block.difficulty

    def calculate_cumulative_difficulty(self):
        return sum([2**block.difficulty for block in self.chain])

    def validate_timestamp(self, new_block):
        current_time = time.time()
        if new_block.timestamp > current_time + 60:
            return False
        if new_block.timestamp < self.get_last_block().timestamp - 60:
            return False
        return True
