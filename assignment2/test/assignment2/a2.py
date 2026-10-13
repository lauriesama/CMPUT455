# CMPUT 455 Assignment 2 starter code
# This is a sample solution for assignment 1.
# Implement the new commands to complete the assignment
# Full assignment specification and game rules on Canvas

import ast
import random
# Improvement 0 Helper (new): time is used for the solver deadline
import time
# Improvement 6 Helper (new): sort moves by gain
from operator import itemgetter
from sys import stderr
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Assignment restrictions (see assignment page)
# ---------------------------------------------------------------------------
MIN_HEAPS = 1
MAX_HEAPS = 20
MIN_TOKENS = 1
MAX_TOKENS = 20
MIN_VALUE = 1
MAX_VALUE = 20
KOMI_LIMIT = 100  # -100 < komi < 100, and komi must be an integer + 0.5

# The time limit, in seconds, for a single solve or genmove command
MIN_TIMELIMIT = 1
MAX_TIMELIMIT = 100
DEFAULT_TIMELIMIT = 1

BLACK = 'b'
WHITE = 'w'
COLORS = (BLACK, WHITE)

Token = Tuple[str, int]
Heap = List[Token]
Heaps = List[Heap]
# Improvement 0 Helper (new): type aliases for the solver cache
# Improvement 5: the cache key no longer contains the score lead. Entries are
# (lower, upper) bounds on the net points the player to move can still gain
# from this position, which depends only on the heap lengths and the player.
# Improvement 6: the key is a single exact integer (see SearchState)
PositionKey = int
# Improvement 7: entries also store the best move found (-1 if none), tried first next time
Bounds = Tuple[int, int, int]
SolveResult = Tuple[Optional[str], Optional[int]]
INFINITY = 10 ** 6
# Improvement 9: most positions kept in the cache before it is emptied.
# Measured peak memory is about 720 MB at 4 million entries (limit 1 GB)
MAX_CACHE_ENTRIES = 4_000_000
# Improvement 8: the clock is read once per this many search nodes
CLOCK_CHECK_INTERVAL = 256


def not_yet() -> bool:
    raise NotImplementedError("Command not implemented.")
    return False


def print_error(error: str) -> None:
    print(error, file=stderr)


def opponent(color: str) -> str:
    return WHITE if color == BLACK else BLACK


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
def is_int(obj: Any) -> bool:
    # bool is a subclass of int; True/False are not valid values
    return isinstance(obj, int) and not isinstance(obj, bool)


def is_token(obj: Any) -> bool:
    return (isinstance(obj, tuple)
            and len(obj) == 2
            and obj[0] in COLORS
            and is_int(obj[1])
            and MIN_VALUE <= obj[1] <= MAX_VALUE)


def is_heap(obj: Any) -> bool:
    return (isinstance(obj, list)
            and MIN_TOKENS <= len(obj) <= MAX_TOKENS
            and all(is_token(token) for token in obj))


def is_heaps(obj: Any) -> bool:
    return (isinstance(obj, list)
            and MIN_HEAPS <= len(obj) <= MAX_HEAPS
            and all(is_heap(heap) for heap in obj))


def parse_komi(text: str) -> Optional[float]:
    try:
        komi = float(text)
    except ValueError:
        return None
    if not (-KOMI_LIMIT < komi < KOMI_LIMIT):
        return None
    if (komi - 0.5) != int(komi - 0.5):
        return None
    return komi


def parse_heaps(text: str) -> Optional[Heaps]:
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return None
    if not is_heaps(parsed):
        return None
    return parsed


# Improvement 0 Helper (new): parse and validate the timelimit argument
def parse_timelimit(args: str) -> Optional[int]:
    parts = args.split()
    if len(parts) != 1 or not parts[0].isdigit():
        return None
    seconds = int(parts[0])
    if not (MIN_TIMELIMIT <= seconds <= MAX_TIMELIMIT):
        return None
    return seconds


def parse_heap_number(args: str) -> Optional[int]:
    parts = args.split()
    if len(parts) != 1:
        return None
    try:
        return int(parts[0])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class HeapGo:
    def __init__(self, komi: float, heaps: Heaps) -> None:
        self.komi = komi
        self.heaps = heaps
        self.toplay = BLACK
        self.score = {BLACK: 0, WHITE: komi}

    def __str__(self) -> str:
        return "k {} {}".format(self.komi, self.heaps)

    def is_legal(self, heap_number: int) -> bool:
        return 0 <= heap_number < len(self.heaps) and len(self.heaps[heap_number]) > 0

    def legal_moves(self) -> List[int]:
        return [i for i in range(len(self.heaps)) if self.is_legal(i)]

    def game_over(self) -> bool:
        return len(self.legal_moves()) == 0

    def play(self, heap_number: int) -> bool:
        if not self.is_legal(heap_number):
            return False
        heap = self.heaps[heap_number]
        gained = 0
        # Rule 1: take all own-color tokens from the top
        while heap and heap[-1][0] == self.toplay:
            gained += heap.pop()[1]
        # Rule 2: then one opponent token, if any remain
        if heap:
            gained += heap.pop()[1]
        self.score[self.toplay] += gained
        self.toplay = opponent(self.toplay)
        return True

    def winner(self) -> Optional[str]:
        if not self.game_over():
            return None
        if self.score[BLACK] > self.score[WHITE]:
            return BLACK
        if self.score[WHITE] > self.score[BLACK]:
            return WHITE
        return None  # draw; impossible with komi = integer + 0.5


# Improvement 0 Helper (new): raised when the solver passes its deadline
class SolveTimeout(Exception):
    pass


# Improvement 0 Helper (new): memoized boolean negamax search with a deadline.
# Returns (winner, move): move is a winning move for the player to move, or
# None if the player to move loses. Each level asks "does any move leave the
# opponent in a lost position?"; the opponent's win is the mover's loss.
def solve_game(game: HeapGo, cache: Dict[PositionKey, Bounds],
               deadline: float) -> SolveResult:
    # Improvement 6: the search runs on precomputed tables (SearchState), so
    # the game itself is never modified
    state = SearchState(game, cache, deadline)
    # Improvement 5: the player to move wins iff lead + (net future gain) > 0.
    # Gains are integers, so that is gain >= need, i.e. gain > need - 1: a
    # null window search (alpha-beta) per root move answers it.
    lead = game.score[game.toplay] - game.score[opponent(game.toplay)]
    need = int(-lead + 0.5)
    moves = state.ordered_moves()
    # Improvement 2: try moves that take the most points first
    for gained, heap_number in moves:
        old_length = state.play(heap_number)
        reply = state.alpha_beta(gained - need, gained - need + 1)
        state.undo(heap_number, old_length)
        if reply <= gained - need:
            return (game.toplay, heap_number)
    if not moves:
        return (game.toplay if lead > 0 else opponent(game.toplay), None)
    return (opponent(game.toplay), None)


# Improvement 6 Helper (new): search state built from a game once per solve.
# A heap only ever loses tokens from its top, so a position is fully described
# by the heap lengths. For every heap and length, tables give the length after
# each colour moves there, and the value of the tokens below that length, so a
# move is a table lookup instead of popping tokens. This replaces the earlier
# make_move, undo_move, move_gain, ordered_moves and remaining_value helpers.
class SearchState:
    def __init__(self, game: HeapGo, cache: Dict[PositionKey, Bounds],
                 deadline: float) -> None:
        self.cache = cache
        self.deadline = deadline
        # Improvement 8: counts nodes so the clock is only read now and then
        self.nodes = 0
        self.colour = COLORS.index(game.toplay)
        self.lens = [len(heap) for heap in game.heaps]
        self.prefix: List[List[int]] = []
        self.newlen: List[List[List[int]]] = [[], []]
        for heap in game.heaps:
            prefix = [0]
            for _, value in heap:
                prefix.append(prefix[-1] + value)
            self.prefix.append(prefix)
            for colour, name in enumerate(COLORS):
                lengths = [0]
                for length in range(1, len(heap) + 1):
                    i = length - 1
                    while i >= 0 and heap[i][0] == name:
                        i -= 1
                    if i >= 0:
                        i -= 1
                    lengths.append(i + 1)
                self.newlen[colour].append(lengths)
        # Exact integer key: heap lengths in mixed radix (lengths are <= 20)
        self.mult = [(MAX_TOKENS + 1) ** h for h in range(len(self.lens))]
        self.key = sum(n * m for n, m in zip(self.lens, self.mult))
        self.remaining = sum(self.prefix[h][n] for h, n in enumerate(self.lens))

    # moves as (points gained, heap number), best first
    def ordered_moves(self) -> List[Tuple[int, int]]:
        colour = self.colour
        moves = []
        for h, length in enumerate(self.lens):
            if length:
                prefix = self.prefix[h]
                moves.append((prefix[length] - prefix[self.newlen[colour][h][length]], h))
        moves.sort(key=itemgetter(0), reverse=True)
        return moves

    # plays a move; returns the heap's old length for undo
    def play(self, h: int) -> int:
        length = self.lens[h]
        new_length = self.newlen[self.colour][h][length]
        prefix = self.prefix[h]
        self.lens[h] = new_length
        self.key += (new_length - length) * self.mult[h]
        self.remaining -= prefix[length] - prefix[new_length]
        self.colour ^= 1
        return length

    def undo(self, h: int, length: int) -> None:
        new_length = self.lens[h]
        prefix = self.prefix[h]
        self.lens[h] = length
        self.key += (length - new_length) * self.mult[h]
        self.remaining += prefix[length] - prefix[new_length]
        self.colour ^= 1

    # Improvement 5 Helper (new): fail-soft alpha-beta in negamax form. Returns
    # the net points the player to move can still gain, exactly if it lies in
    # (alpha, beta), otherwise a bound on it. Bounds are cached per position.
    def alpha_beta(self, alpha: int, beta: int) -> int:
        # Improvement 8: read the clock every CLOCK_CHECK_INTERVAL nodes only
        self.nodes += 1
        if self.nodes % CLOCK_CHECK_INTERVAL == 0 and time.monotonic() > self.deadline:
            raise SolveTimeout()
        # Improvement 3 (moved into the search): the net gain always lies in
        # [-left, left], so the window can be decided without searching
        left = self.remaining
        if left == 0:
            return 0
        if alpha >= left:
            return left
        if beta <= -left:
            return -left

        key = self.key * 2 + self.colour
        lower, upper, hash_move = self.cache.get(key, (-INFINITY, INFINITY, -1))
        if lower >= beta:
            return lower
        if upper <= alpha:
            return upper
        if lower == upper:
            return lower
        low, high = max(alpha, lower), min(beta, upper)

        # Improvement 7: try the best move found last time in this position first
        moves = self.ordered_moves()
        if hash_move >= 0:
            moves.sort(key=lambda move: move[1] != hash_move)
        best = -INFINITY
        best_move = -1
        # Improvement 2: try moves that take the most points first
        for gained, h in moves:
            length = self.play(h)
            value = gained - self.alpha_beta(gained - high, gained - max(low, best))
            self.undo(h, length)
            if value > best:
                best = value
                best_move = h
            if best >= high:
                break

        if best <= low:
            upper = min(upper, best)
        elif best >= high:
            lower = max(lower, best)
        else:
            lower = upper = best
        # Improvement 9: empty the cache when full, it only holds saved work
        if len(self.cache) >= MAX_CACHE_ENTRIES:
            self.cache.clear()
        self.cache[key] = (lower, upper, best_move)
        return best


CommandMap = Dict[str, Callable[[str], bool]]


class CommandInterface:
    def __init__(self) -> None:
        self.game: Optional[HeapGo] = None
        self.timelimit = DEFAULT_TIMELIMIT
        # you can add your own initialisation here
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
            "solve": self.cmd_solve,
            "timelimit": self.cmd_timelimit,
            }

#============================================================================
# Command implementations
#============================================================================
    def cmd_heapgo(self, args: str) -> bool:
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            print_error("usage: heapgo komi game")
            return False
        komi = parse_komi(parts[0])
        if komi is None:
            print_error("invalid komi: {}".format(parts[0]))
            return False
        heaps = parse_heaps(parts[1])
        if heaps is None:
            print_error("invalid game: {}".format(parts[1]))
            return False
        self.game = HeapGo(komi, heaps)
        return True

    def cmd_show(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        print(self.game)
        return True

    def cmd_toplay(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        if args not in COLORS:
            print_error("invalid color: {}".format(args))
            return False
        self.game.toplay = args
        return True

    def cmd_play(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        heap_number = parse_heap_number(args)
        if heap_number is None:
            print_error("invalid heap number: {}".format(args))
            return False
        if not self.game.play(heap_number):
            print_error("illegal move: {}".format(heap_number))
            return False
        return True

    def cmd_legal(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        heap_number = parse_heap_number(args)
        if heap_number is None:
            print_error("invalid heap number: {}".format(args))
            return False
        print("yes" if self.game.is_legal(heap_number) else "no")
        return True

    # Improvement 1 (existing improved): was a random move; now uses the solver
    def cmd_genmove(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        moves = self.game.legal_moves()
        if not moves:
            print_error("no legal moves")
            return False
        # Improvement 1: play the solver's winning move; fall back to a
        # random legal move if the game is lost or the solver times out
        result = self.run_solver()
        winning_move = result[1] if result is not None else None
        move = winning_move if winning_move is not None else random.choice(moves)
        self.game.play(move)
        print(move)
        return True

    # Improvement 1 Helper (new): run the solver within the time limit; returns
    # None if it does not finish in time (also used by cmd_solve)
    def run_solver(self) -> Optional[SolveResult]:
        assert self.game is not None
        deadline = time.monotonic() + self.timelimit
        try:
            # Improvement 6: the search works on its own tables, so the real
            # game is never modified, even on a timeout
            return solve_game(self.game, {}, deadline)
        except SolveTimeout:
            return None

    def cmd_score(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        print("b {} w {}".format(self.game.score[BLACK], self.game.score[WHITE]))
        return True

    def cmd_winner(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        winner = self.game.winner()
        if winner is None:
            print_error("game not over" if not self.game.game_over() else "draw")
            return False
        print(winner)
        return True

#============================================================================
# You need to implement the following methods.
#============================================================================
    # Improvement 0 (existing improved): was a stub; now solves the game
    def cmd_solve(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        result = self.run_solver()
        if result is None:
            return False
        winner, move = result
        if winner is None:
            print_error("draw")
            return False
        if winner == self.game.toplay and move is not None:
            print("{} {}".format(winner, move))
        else:
            print(winner)
        return True

    # Improvement 0 (existing improved): was a stub; now sets the time limit
    def cmd_timelimit(self, args: str) -> bool:
        seconds = parse_timelimit(args)
        if seconds is None:
            print_error("invalid time limit: {}".format(args))
            return False
        self.timelimit = seconds
        return True
#============================================================================
# End of functions requiring implementation
#============================================================================

#============================================================================
# The code below should not need modification
# Anyway, you may change or add to this code as you see fit
#============================================================================
    def cmd_help(self, ignore_args: str) -> bool:
        print("\nKnown commands:")
        for cmd in self.commands:
            print(cmd)
        return True

    def process_command(self, cmd_name: str, cmd_args: str) -> None:
        status = "= -1"
        cmd = self.commands.get(cmd_name)
        if cmd:
            try:
                if cmd(cmd_args):
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
