# CMPUT 455 Assignment 1 starter code
# Implement the specified commands to complete the assignment
# Full assignment specification and game rules on Canvas

from sys import stderr
from typing import List, Dict, Callable

def not_yet() -> bool:
    raise NotImplementedError("Command not implemented.")
    return False

def print_error(error: str) -> None:
    print(error, file = stderr)

CommandMap = Dict[str, Callable[[str], bool]]

class CommandInterface:
    def __init__(self) -> None:
        # you can add your own initialisation here
        self.game = None
        self.komi = 0.0
        self.player = "b"
        self.black_score = 0
        self.white_score = 0
        self.commands: CommandMap = {
            "help": self.cmd_help,
            "heapgo": self.cmd_heapgo,
            "show": self.cmd_show,
            "toplay": self.cmd_toplay,
            "play": self.cmd_play,
            "legal": self.cmd_legal,
            "genmove": self.cmd_genmove,
            "score": self.cmd_score,
            "winner": self.cmd_winner,
            }

#============================================================================
# You need to implement the following methods.
#============================================================================
    def cmd_heapgo(self, args: str) -> bool:
        # Checks for valid input
        if args is None:
            return False

        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            return False

        komi_text, game_text = parts
        try:
            komi = float(komi_text)
            game = eval(game_text)
        except Exception:
            return False

        if not isinstance(game, list):
            return False
        if not (1 <= len(game) <= 10):
            return False

        for heap in game:
            if not isinstance(heap, list):
                return False
            if not (1 <= len(heap) <= 10):
                return False
            for token in heap:
                if not isinstance(token, tuple) or len(token) != 2:
                    return False
                color, value = token
                if color not in ("b", "w"):
                    return False
                if not isinstance(value, int) or isinstance(value, bool):
                    return False
                if not (1 <= value <= 20):
                    return False

        # Initialize if valid
        self.game = game
        self.komi = komi
        self.player = "b"
        self.black_score = 0
        self.white_score = 0
        return True

    def cmd_show(self, args: str) -> bool:
        # Show komi and current game state.
        if args.strip():
            return False
        if self.game is None:
            return False
        print("k " + str(self.komi) + " " + str(self.game))
        return True

    def cmd_toplay(self, args: str) -> bool:
        # Set the current player to play next. Must be "b" or "w". 
        if self.game is None:
            return False
        color = args.strip()
        if color not in ("b", "w"):
            return False
        self.player = color
        return True

    def cmd_play(self, args: str) -> bool:
        # Play a move for the current player on the specified heap index.
        if self.game is None:
            return False
        try:
            heap_index = int(args.strip())
        except Exception:
            return False
        if heap_index < 0 or heap_index >= len(self.game):
            return False
        heap = self.game[heap_index]
        if not heap:
            return False

        color = self.player
        gained = 0

        while heap and heap[-1][0] == color:
            gained += heap[-1][1]
            heap.pop()

        if heap and heap[-1][0] != color:
            gained += heap[-1][1]
            heap.pop()

        if color == "b":
            self.black_score += gained
        else:
            self.white_score += gained

        self.player = "w" if color == "b" else "b"
        return True

    def cmd_legal(self, args: str) -> bool:
        # Check if the specified heap index is a legal move for the current player.
        if self.game is None:
            return False
        try:
            heap_index = int(args.strip())
        except Exception:
            return False
        if heap_index < 0:
            return False
        if heap_index >= len(self.game):
            print("no")
            return True
        if self.game[heap_index]:
            print("yes")
        else:
            print("no")
        return True

    def cmd_genmove(self, args: str) -> bool:
        #  Generate a move for the current player. The move is the index of the first non-empty heap.
        if args.strip():
            return False
        if self.game is None:
            return False

        legal = [i for i, heap in enumerate(self.game) if heap]
        if not legal:
            return False

        move = legal[0]
        color = self.player
        heap = self.game[move]
        gained = 0

        while heap and heap[-1][0] == color:
            gained += heap[-1][1]
            heap.pop()

        if heap and heap[-1][0] != color:
            gained += heap[-1][1]
            heap.pop()

        if color == "b":
            self.black_score += gained
        else:
            self.white_score += gained

        self.player = "w" if color == "b" else "b"
        print(move)
        return True

    def cmd_score(self, args: str) -> bool:
        # Print the current score for both players, including komi for white.
        if args.strip():
            return False
        if self.game is None:
            return False
        white_total = self.white_score + self.komi
        print("b " + str(self.black_score) + " w " + str(white_total))
        return True

    def cmd_winner(self, args: str) -> bool:
        # Determine the winner based on the current score and komi. Print "b" for black, "w" for white, or "draw" if scores are equal.
        if args.strip():
            return False
        if self.game is None:
            return False
        if any(heap for heap in self.game):
            return False

        b_total = self.black_score
        w_total = self.white_score + self.komi
        if b_total > w_total:
            print("b")
        elif w_total > b_total:
            print("w")
        else:
            print("draw")
        return True
#============================================================================
# End of functions requiring implementation
#============================================================================

#============================================================================
# The code below should not need modification
# Anyway, you may change or add to this code as you see fit
# Examples:
# You can add class variables to __init__ above
# You can add better error messages
# You can put commands inside your own Heap Go class
# etc.
#============================================================================
    # List available commands
    def cmd_help(self, ignore_args: str) -> bool:
        print("\nKnown commands:")
        for cmd in self.commands:
            print(cmd)
        return True

    def process_command(self, cmd_name: str, cmd_args: str) -> None:
        # Try to find command, None if wrong name
        status = "= -1"
        cmd = self.commands.get(cmd_name)
        if cmd:
            try:
                if cmd(cmd_args): # success!
                    status = "= 1"
            except Exception as e:
                print_error(f"Command {cmd_name} with arguments {cmd_args} failed with exception: {e}")
        else:
            print_error("Unknown command. Type 'help' for commands.")
        print(status)
    
    def main_loop(self) -> None:
        process_commands = True
        while process_commands:
            try:
                line = input()
            except EOFError:
                break
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            cmd_name = parts[0]
            if cmd_name == "exit":
                process_commands = False
                continue
            cmd_args = parts[1] if len(parts) > 1 else ""
            self.process_command(cmd_name, cmd_args)

if __name__ == "__main__":
    interface = CommandInterface()
    interface.main_loop()

