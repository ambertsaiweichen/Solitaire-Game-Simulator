from itertools import chain
from random import seed, shuffle
from collections import defaultdict

# Unicode suit base code points: Hearts, Diamonds, Clubs, Spades
SUIT_BASE = [0x1F0B0, 0x1F0C0, 0x1F0D0, 0x1F0A0]


def card_to_unicode(card):
    suit = card // 13
    rank = card % 13
    if rank <= 9:
        offset = rank + 1
    elif rank == 10:    # Jack
        offset = 0xB
    elif rank == 11:    # Queen (skip Knight at 0xC)
        offset = 0xD
    else:               # King
        offset = 0xE
    return chr(SUIT_BASE[suit] + offset)


def ordinal(n):
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    rem = n % 10
    if rem == 1:
        return f"{n}st"
    elif rem == 2:
        return f"{n}nd"
    elif rem == 3:
        return f"{n}rd"
    else:
        return f"{n}th"


def format_pile(pile):
    if not pile:
        return ""
    return "[" * (len(pile) - 1) + card_to_unicode(pile[-1])


def format_stacks_line(stacks):
    """Four stacks (H, D, C, S). 4-space prefix; positions at string indices 4, 19, 34, 49.
    Each nonempty stack: top card unicode + '[' * (size-1). No trailing spaces."""
    result = []
    for i in range(4):
        stack = stacks[i]
        if not stack:
            continue
        pos = 4 + i * 15
        while len(result) < pos:
            result.append(' ')
        for _ in range(len(stack) - 1):
            result.append('[')
        result.append(card_to_unicode(stack[-1]))
    return ''.join(result)


def try_place(card, inc_stacks, dec_stacks):
    """Try to place card onto a stack. Returns action message string if placed, None otherwise."""
    suit = card // 13
    rank = card % 13
    # Priority 1: Start a new stack (Ace → increasing, King → decreasing)
    if rank == 0 and not inc_stacks[suit]:
        inc_stacks[suit].append(card)
        return "Starting a stack."
    if rank == 12 and not dec_stacks[suit]:
        dec_stacks[suit].append(card)
        return "Starting a stack."
    # Priority 2: Extend existing increasing stack
    if inc_stacks[suit] and inc_stacks[suit][-1] % 13 + 1 == rank:
        inc_stacks[suit].append(card)
        return "Extending an increasing stack."
    # Priority 3: Extend existing decreasing stack
    if dec_stacks[suit] and dec_stacks[suit][-1] % 13 - 1 == rank:
        dec_stacks[suit].append(card)
        return "Extending a decreasing stack."
    return None


def add_pattern(collected, deck, pile, inc_stacks, dec_stacks, message=None):
    """Append one 4-line pattern to collected, always preceded by a blank separator.
    If message is provided, it is inserted after the blank and before the 4 pattern lines."""
    collected.append("")
    if message is not None:
        collected.append(message)
    collected.append("]" * len(deck))
    collected.append(format_pile(pile))
    collected.append(format_stacks_line(inc_stacks))
    collected.append(format_stacks_line(dec_stacks))


def parse_command(raw, n_lines):
    """Parse a viewer command string. Returns ('q',None), ('last',k), ('first',k),
    ('range',(m,n)), or None for invalid input.
    Spaces allowed: at start/end of input, between first number and '--', after '--'.
    No space between '-' and digits of a negative number."""
    if raw.strip() == 'q':
        return ('q', None)

    pos = 0
    length = len(raw)

    # Skip leading spaces
    while pos < length and raw[pos] == ' ':
        pos += 1

    # Try to read leading digits (positive integer or first part of range)
    start = pos
    while pos < length and raw[pos].isdigit():
        pos += 1

    if pos > start:
        first_val = int(raw[start:pos])
        mark = pos
        # Skip spaces (before '--' or before end of string)
        while pos < length and raw[pos] == ' ':
            pos += 1
        # Check for '--'
        if pos + 1 < length and raw[pos] == '-' and raw[pos + 1] == '-':
            pos += 2
            # Skip spaces after '--'
            while pos < length and raw[pos] == ' ':
                pos += 1
            # Read second digits
            start2 = pos
            while pos < length and raw[pos].isdigit():
                pos += 1
            if pos > start2:
                second_val = int(raw[start2:pos])
                # Skip trailing spaces
                while pos < length and raw[pos] == ' ':
                    pos += 1
                if pos == length and 1 <= first_val <= second_val <= n_lines:
                    return ('range', (first_val, second_val))
        else:
            # Check if just a positive integer (only trailing spaces remain)
            pos = mark
            while pos < length and raw[pos] == ' ':
                pos += 1
            if pos == length and 1 <= first_val <= n_lines:
                return ('last', first_val)
    else:
        # Try negative integer: '-' immediately followed by digits (no space allowed)
        if pos < length and raw[pos] == '-':
            pos += 1
            start = pos
            while pos < length and raw[pos].isdigit():
                pos += 1
            if pos > start:
                neg_val = -int(raw[start:pos])
                while pos < length and raw[pos] == ' ':
                    pos += 1
                if pos == length and -n_lines <= neg_val <= -1:
                    return ('first', -neg_val)

    return None


def play_game(initial_seed):
    cards = list(range(52))
    seed(initial_seed)
    shuffle(cards)

    deck = list(cards)
    inc_stacks = defaultdict(list)
    dec_stacks = defaultdict(list)
    total_placed = 0

    collected = ["Deck shuffled. Ready to start!", "]" * 52]

    round_num = 0
    game_over = False

    while not game_over:
        placed_this_round = 0
        pile = []

        # Round announcement: preceded by one blank line; blank after comes from add_pattern
        collected.append("")
        collected.append(f"Starting the {ordinal(round_num + 1)} round...")

        while deck:
            # Draw up to 3 cards from top of deck onto face-up pile
            draw = min(3, len(deck))
            for _ in range(draw):
                pile.append(deck.pop())

            add_pattern(collected, deck, pile, inc_stacks, dec_stacks)

            # Try to place top card(s) from face-up pile
            while pile:
                action = try_place(pile[-1], inc_stacks, dec_stacks)
                if action is not None:
                    pile.pop()
                    placed_this_round += 1
                    total_placed += 1
                    add_pattern(collected, deck, pile, inc_stacks, dec_stacks, action)
                    if total_placed == 52:
                        game_over = True
                        break
                else:
                    break

            if game_over:
                break

        if not game_over:
            if placed_this_round == 0:
                game_over = True
            else:
                # Turn face-up pile face-down to form new deck: physical flip reverses order.
                # Bottom of face-up pile (pile[0]) becomes top of new deck (drawn first).
                deck = pile[::-1]
                round_num += 1

    unplaced = 52 - total_placed

    print()
    if unplaced == 0:
        print("You placed all cards. You won! \U0001F600")
    else:
        print(f"You could not place {unplaced} cards. You lost! \U0001F61E")

    n_lines = len(collected)
    print()
    print(f"There are {n_lines} lines of output. What do you want me to do?")
    print()
    print("Enter: q to quit")
    print(f"       a last line number (between 1 and {n_lines})")
    print(f"       a first line number (between -1 and -{n_lines})")
    print(f"       a range of line numbers (of the form m--n with 1 <= m <= n <= {n_lines})")

    while True:
        try:
            raw = input("       ")
        except EOFError:
            break
        result = parse_command(raw, n_lines)

        if result is not None and result[0] == 'q':
            break

        # Print blank, optional content, blank, then re-prompt
        print()
        if result is not None:
            cmd, val = result
            if cmd == 'last':
                for line in collected[:val]:
                    print(line)
            elif cmd == 'first':
                for line in collected[-val:]:
                    print(line)
            elif cmd == 'range':
                m_val, n_val = val
                for line in collected[m_val - 1:n_val]:
                    print(line)
            print()

        print("Enter: q to quit")
        print(f"       a last line number (between 1 and {n_lines})")
        print(f"       a first line number (between -1 and -{n_lines})")
        print(f"       a range of line numbers (of the form m--n with 1 <= m <= n <= {n_lines})")


def simulate(n, i):
    results = defaultdict(int)

    for g in range(n):
        cards = list(range(52))
        seed(i + g)
        shuffle(cards)

        deck = list(cards)
        inc_stacks = defaultdict(list)
        dec_stacks = defaultdict(list)
        total_placed = 0
        game_over = False

        while not game_over:
            placed_this_round = 0
            pile = []

            while deck:
                draw = min(3, len(deck))
                for _ in range(draw):
                    pile.append(deck.pop())

                while pile:
                    placed = try_place(pile[-1], inc_stacks, dec_stacks)
                    if placed:
                        pile.pop()
                        placed_this_round += 1
                        total_placed += 1
                        if total_placed == 52:
                            game_over = True
                            break
                    else:
                        break

                if game_over:
                    break

            if not game_over:
                if placed_this_round == 0:
                    game_over = True
                else:
                    deck = pile[::-1]

        results[52 - total_placed] += 1

    print("Number of cards left | Relative frequency")
    print("-" * 41)
    for k in sorted(results.keys(), reverse=True):
        pct = results[k] / n * 100
        k_str = str(k).rjust(20)
        pct_str = f"{pct:.2f}%".rjust(18)
        print(f"{k_str} | {pct_str}")


if __name__ == '__main__':
    user_input = int(input("Enter an integer to pass to the seed() function: "))
    play_game(user_input)