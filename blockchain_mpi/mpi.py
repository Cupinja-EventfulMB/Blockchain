from mpi4py import MPI
import hashlib
import time
import sys
import threading

class Block:
    def __init__(self, index, data, timestamp, previous_hash, difficulty, token=0):
        self.index = index
        self.data = data
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.token = token
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        return hashlib.sha256(
            f"{self.index}{self.data}{self.timestamp}{self.previous_hash}{self.difficulty}{self.token}".encode()).hexdigest()

    def mine_block(self, num_threads):
        print(f"Starting mining new block at index {self.index}...", flush=True)
        start_time = time.time()
        self.found = False
        self.mining_thread_id = None
        lock = threading.Lock() 

        def mine_range(start_token, thread_id):
            nonlocal self
            token = start_token
            while not self.found:
                with lock:
                    if self.found: 
                        break
                temp_hash = hashlib.sha256(
                    f"{self.index}{self.data}{self.timestamp}{self.previous_hash}{self.difficulty}{token}".encode()
                ).hexdigest()
                if temp_hash[:self.difficulty] == '0' * self.difficulty:
                    with lock:
                        if not self.found:  
                            self.found = True
                            self.token = token
                            self.hash = temp_hash
                            self.mining_thread_id = thread_id
                            print(f"Thread {thread_id} mined the block with token {token}")  
                            break
                token += num_threads  

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=mine_range, args=(i, i))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        end_time = time.time()
        if self.found:
            print(f"New block mined by thread {self.mining_thread_id}: {self.hash}", flush=True)
            print(f"Mining completed in {end_time - start_time} seconds.", flush=True)
        else:
            print("Failed to mine the block.", flush=True)

    def is_valid(self, previous_block):
        if self.index != previous_block.index + 1:
            return False
        if self.previous_hash != previous_block.hash:
            return False
        if self.hash != self.calculate_hash():
            return False
        if not self.validate_timestamp(previous_block):
            return False
        return True

    def validate_timestamp(self, previous_block):
        if self.timestamp > time.time() + 60:
            return False
        if self.timestamp < previous_block.timestamp - 60:
            return False
        return True

class Blockchain:
    def __init__(self, creation_interval, adjustment_interval):
        self.difficulty = 1
        self.chain = [self.create_genesis_block()]
        self.block_creation_interval = creation_interval
        self.adjustment_interval = adjustment_interval

    def create_genesis_block(self):
        return Block(0, 'Genesis Block', time.time(), '0', self.difficulty)

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        if new_block.is_valid(self.get_last_block()):
            self.chain.append(new_block)
            self.difficulty = self.adjust_difficulty()

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

def mine_blocks(blockchain, rank, num_blocks, num_threads):
    stop_mining = False
    while len(blockchain.chain) < num_blocks and not stop_mining:
        if comm.Iprobe(source=MPI.ANY_SOURCE, tag=77, status=status):
            stop_mining = True
            comm.recv(source=status.Get_source(), tag=77)
            print(f"Rank {rank} received a stop signal and is stopping mining.")
            break

        last_block = blockchain.get_last_block()
        new_block = Block(
            index=len(blockchain.chain),
            data=f"Block {len(blockchain.chain)} Data",
            timestamp=time.time(),
            previous_hash=last_block.hash,
            difficulty=blockchain.difficulty
        )
        new_block.mine_block(num_threads)

        if new_block.is_valid(last_block):
            blockchain.add_block(new_block)
            print(f"Rank {rank} mined a new block: {new_block.hash}")

            if len(blockchain.chain) == num_blocks:
                for dest in range(size):
                    if dest != rank:
                        comm.send(None, dest=dest, tag=77)
                print(f"Rank {rank} reached the target block count and is broadcasting a stop signal.")
                break
        else:
            print(f"Invalid block at index {new_block.index} by rank {rank}", flush=True)
            break

    return blockchain.calculate_cumulative_difficulty()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: mpirun -n <num_processes> python script.py <num_blocks> <num_threads>")
        sys.exit()

    num_blocks = int(sys.argv[1]) 
    num_threads = int(sys.argv[2])  

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    status = MPI.Status()

    blockchain = Blockchain(10, 10)

    if rank == 0:
        start_time = time.time() 
        for dest in range(1, size):
            comm.send(None, dest=dest, tag=99)

    if rank != 0:
        comm.recv(source=0, tag=99)

    cum_value = mine_blocks(blockchain, rank, num_blocks, num_threads) 

    cum_values = comm.gather(cum_value, root=0)

    if rank == 0:
        best_cum_value = max(cum_values)
        best_blockchain_index = cum_values.index(best_cum_value) + 1
        print(f"Best Blockchain: Blockchain {best_blockchain_index}", flush=True)
        print(f"Best Cumulative Value: {best_cum_value}", flush=True)
        
        end_time = time.time()  
        total_time = end_time - start_time
        print(f"Total execution time: {total_time} seconds")