import os

class Memo:
    def __init__(self):
        self.memo_file = "storage/memory/memo.txt"
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.memo_file), exist_ok=True)
        # Initialize an empty list to store memos
        self.memos = []
        # Load existing memos from the file
        self._load_memos()

    def _load_memos(self):
        """Load memos from the file into the list."""
        if os.path.exists(self.memo_file):
            with open(self.memo_file, 'r') as file:
                self.memos = [line.strip() for line in file.readlines()]

    def _save_memos(self):
        """Save the current list of memos to the file."""
        with open(self.memo_file, 'w') as file:
            for memo in self.memos:
                file.write(memo + '\n')

    def write_memo(self, memo_text):
        """Write a new memo and save it to the file."""
        self.memos.append(memo_text)
        self._save_memos()

    def read_memo(self, num: int=None):
        """Read all memos from the list."""
        if num:
            return self.memos[-num:]
        else:
            return self.memos

# Example usage:
memo = Memo()
print(memo.read_memo(2))  # Output: ['Buy groceries', 'Call John']