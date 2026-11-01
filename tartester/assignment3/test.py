#!/usr/bin/env python3
"""Extra checks for a3.py that the public tests do not cover.

Run from the assignment3 directory:

    python3 test.py            # all checks
    python3 test.py timing     # only the timing checks
    python3 test.py weights    # only the correctness checks

Timing checks use the largest game the assignment allows (20 heaps of 20
tokens) with numsimulations 100, the worst case a private test can ask for.
The test script allows 1 second per command.
"""

import io
import random
import sys
import time
from contextlib import redirect_stdout

from a3 import BLACK, WHITE, CommandInterface, HeapGo

TIME_LIMIT = 1.0  # seconds per command in a3test.py
WARN_AT = 0.5     # lab machines may be slower than this one


def largest_game(seed: int = 1) -> HeapGo:
    rng = random.Random(seed)
    heaps = [[(rng.choice((BLACK, WHITE)), rng.randint(1, 20))
              for _ in range(20)] for _ in range(20)]
    return HeapGo(0.5, heaps)


def run_quiet(command, args: str = "") -> str:
    """Run a command, returning what it printed instead of showing it."""
    with redirect_stdout(io.StringIO()) as out:
        command(args)
    return out.getvalue()


def timed(label: str, func) -> bool:
    start = time.time()
    func()
    seconds = time.time() - start
    verdict = "ok" if seconds < WARN_AT else ("SLOW" if seconds < TIME_LIMIT else "FAIL")
    print("{:<48} {:6.3f}s  {}".format(label, seconds, verdict))
    return seconds < TIME_LIMIT


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------
def test_timing() -> bool:
    ok = True
    for policy in ("random", "probabilistic"):
        ci = CommandInterface()
        ci.policy = policy
        ci.numsimulations = 100

        ci.game = largest_game()
        ok &= timed("{} genmove, 20x20, n=100".format(policy),
                    lambda: run_quiet(ci.cmd_genmove))

        ci.game = largest_game()
        ok &= timed("{} simulate x100, 20x20".format(policy),
                    lambda: [run_quiet(ci.cmd_simulate) for _ in range(100)])

        ci.game = largest_game()
        ok &= timed("{} policymoves x1000, 20x20".format(policy),
                    lambda: [run_quiet(ci.cmd_policymoves) for _ in range(1000)])
    return ok


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------
def check(label: str, got, expected) -> bool:
    passed = got == expected
    print("{:<48} {}".format(label, "ok" if passed else "FAIL"))
    if not passed:
        print("    expected: {!r}".format(expected))
        print("    got:      {!r}".format(got))
    return passed


def test_weights() -> bool:
    ok = True
    # Spec example: weights 5, 12 and 3
    game = HeapGo(0.5, [[('b', 5)], [('b', 4), ('b', 8)], [('w', 3)]])
    ok &= check("weights 5 12 3", [game.move_weight(i) for i in range(3)], [5, 12, 3])

    # Rule 1 and rule 2 together, and weights depend on the player
    game = HeapGo(0.5, [[('w', 4), ('b', 2), ('b', 3)], [('b', 6)], [('w', 1), ('w', 2)]])
    ok &= check("black takes own tokens then one white",
                [game.move_weight(i) for i in range(3)], [9, 6, 2])
    game.toplay = WHITE
    ok &= check("white weights differ",
                [game.move_weight(i) for i in range(3)], [3, 6, 3])
    ok &= check("move_weight does not change heaps", game.heaps,
                [[('w', 4), ('b', 2), ('b', 3)], [('b', 6)], [('w', 1), ('w', 2)]])

    # simulate and genmove leave the game untouched / consistent
    ci = CommandInterface()
    ci.game = largest_game()
    before = str(ci.game), dict(ci.game.score), ci.game.toplay
    for _ in range(20):
        run_quiet(ci.cmd_simulate)
    after = str(ci.game), dict(ci.game.score), ci.game.toplay
    ok &= check("simulate restores the game", after, before)

    # Weights persist and probabilities sum to 1 under both policies
    for policy in ("random", "probabilistic"):
        ci.policy = policy
        text = run_quiet(ci.cmd_policymoves).split()
        probs = [float(p) for p in text[1::2]]
        moves = [int(m) for m in text[0::2]]
        ok &= check("{} policymoves sums to ~1".format(policy),
                    abs(sum(probs) - 1.0) < 0.002, True)
        ok &= check("{} policymoves sorted".format(policy), moves, sorted(moves))

    # genmove picks the only winning move in a forced position
    ci = CommandInterface()
    ci.policy = "random"
    ci.game = HeapGo(0.5, [[('b', 10)], [('w', 1)]])
    ok &= check("genmove takes the winning 10", run_quiet(ci.cmd_genmove).strip(), "0")

    # numsimulations limits
    ci = CommandInterface()
    ok &= check("numsimulations 100 accepted", run_quiet_status(ci, "numsimulations", "100"), True)
    ok &= check("numsimulations 0 rejected", run_quiet_status(ci, "numsimulations", "0"), False)
    ok &= check("numsimulations 101 rejected", run_quiet_status(ci, "numsimulations", "101"), False)
    ok &= check("policy bogus rejected", run_quiet_status(ci, "policy", "bogus"), False)
    return ok


def run_quiet_status(ci: CommandInterface, name: str, args: str) -> bool:
    with redirect_stdout(io.StringIO()):
        return ci.commands[name](args)


# ---------------------------------------------------------------------------
def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    ok = True
    if which in ("all", "weights"):
        print("== correctness ==")
        ok &= test_weights()
    if which in ("all", "timing"):
        print("== timing (limit {}s, warn at {}s) ==".format(TIME_LIMIT, WARN_AT))
        ok &= test_timing()
    print("\nALL OK" if ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
