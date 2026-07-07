from itertools import chain
from random import seed, shuffle
from collections import defaultdict


# Unicode suit base code points: Hearts, Diamonds, Clubs, Spades
SUIT_BASE = [0x1F0B0, 0x1F0C0, 0x1F0D0, 0x1F0A0]

# Numbers 0 to 12 represent the Hearts, from Ace to King
# Numbers 13 to 25 represent the Diamonds, from Ace to King
# Numbers 26 to 38 represent the Clubs, from Ace to King
# Numbers 39 to 51 represent the Spades, from Ace to King


def card_to_unicode(card):
    suit = card // 13 # 0~12 -> 0 -> Hearts, 13~25 -> 1 -> Diamonds...
    number = card % 13 # number = 0 -> Ace, number = 1 -> 2, number = 2 -> 3...number = 12 -> King
    
    if number <= 9:
        offset = number + 1 # offset - how far the card is from the base
    elif number == 10:
        offset = 0xB # 11 -> Jack
    elif number == 11:
        offset = 0xD # 12 -> Queen
    else:
        offset = 0xE # King
        
    return chr(SUIT_BASE[suit] + offset)
    # Decide suit - use suit as an index to retrieve the base code corresponding to that suit
    # Then decide A,1,2..., K


def is_picture(card):
    return card % 13 >= 10


def format_row(layout, row):
    """ Build the formatted string for one row of the 4×4 layout.
        Tabs are calculated relative to the previous visible card to maintain alignment. """

    # Within each row, the first card is preceded by one tab character, 
    # the second by two tabs, the third by three tabs, and the fourth by four tabs
    
    line = ""
    previous_c = -1 # Column index of the previous card (-1 -> none yet)
    
    for c in range(4):
        card = layout[row * 4 + c] # Map 2D position (row, col) to 1D index
        
        if card is not None:
            tabs = c + 1 if previous_c == -1 else c - previous_c
            line += "\t" * tabs + card_to_unicode(card)
            previous_c = c # Update the column index of the last placed card
            
    return line


def print_layout(layout):
    """ Print the layout row by row using format_row() """
    
    for row in range(4):
        print(format_row(layout, row))


def play_game(initial_seed):
    """ Simulate the solitaire game using the given initial seed.
         The function initialises and shuffles a 52-card deck, then plays up to four rounds. 
         In each round, cards are drawn to fill a 4×4 layout. 
         Any picture cards are removed and replaced. 
         The game ends when no more picture cards can be removed or all 12 have been removed. """
    
    # Initialise seed and create a standard 52-card deck (0-51)
    current_seed = initial_seed
    cards = list(range(52))
    seed(current_seed)
    shuffle(cards)

    # Print initial game state
    print()
    print("Deck shuffled. Ready to start!")
    print("]" * len(cards)) # Face-down cards in the deck

    # Round labels and total removed picture cards counter
    round_names = ['first', 'second', 'third', 'fourth']
    total_removed = 0

    for round_num in range(4):
        deck = list(cards)

        print()
        
        if round_num == 0:
            print("Starting the first round...")
        else:
            print(f"After shuffling, starting the {round_names[round_num]} round...")

        # Initialise empty 4×4 layout
        layout = [None] * 16
        need_draw = 16 # Number of cards that need to be drawn initially

        while need_draw > 0:
            vacant = [pos for pos in range(16) if layout[pos] is None]
            actual_draw = min(need_draw, len(deck))
            
            if actual_draw == 0:
                break
                
            # Fill vacant positions with drawn cards
            for j in range(actual_draw):
                layout[vacant[j]] = deck.pop()

            print()
            
            word = 'card' if actual_draw == 1 else 'cards'
            print(f"Drawing {actual_draw} {word}:")
            print("]" * len(deck)) # Remaining face-down cards
            print_layout(layout) # Display current layout

            # Identify indexes of picture cards
            pictures = [pos for pos in range(16)
                        if layout[pos] is not None and is_picture(layout[pos])]

            if not pictures:
                break

            n_pics = len(pictures)
            
            print()
            
            # Print removal message
            word = 'picture card' if n_pics == 1 else 'picture cards'
            print(f"Removing {n_pics} {word}:")

            # Update total removed count
            total_removed += n_pics

            # Remove picture cards from layout
            for pos in pictures:
                layout[pos] = None
            print_layout(layout)

            need_draw = n_pics # Set number of cards to draw in next iteration

            if total_removed == 12:
                break

        if total_removed == 12:
            break

        # Prepare deck for next round (if not the last round)
        if round_num < 3:
            remaining = sorted(chain((c for c in layout if c is not None), deck))
            current_seed += 1
            seed(current_seed)
            shuffle(remaining)
            cards = remaining

    print()

    # Print final game result
    if total_removed == 12:
        print("You removed all picture cards. You won! \U0001F600")
    elif total_removed == 0:
        print("You removed no picture cards. You lost! \U0001F61E")
    else:
        word = 'picture card' if total_removed == 1 else 'picture cards'
        print(f"You removed only {total_removed} {word}. You lost! \U0001F61E")


def simulate(n, i):
    """ Run multiple simulations of the solitaire game and report statistics.
    This function simulates n independent games, starting from seed i.
    For each game, the deck is shuffled deterministically using an incremented seed. 
    The game is played following the same rules as play_game(), but without printing intermediate steps.
    The function records how many picture cards are removed in each game and prints a table of relative frequencies.
    """

    results = defaultdict(int)

    # Run n simulations
    for g in range(n):
        current_seed = i + g
        cards = list(range(52))
        seed(current_seed)
        shuffle(cards)

        total_removed = 0

        for round_num in range(4):
            deck = list(cards)
            layout = [None] * 16
            need_draw = 16

            while need_draw > 0:
                vacant = [pos for pos in range(16) if layout[pos] is None]
                actual_draw = min(need_draw, len(deck))
                
                if actual_draw == 0:
                    break
                    
                for j in range(actual_draw):
                    layout[vacant[j]] = deck.pop()

                pictures = [pos for pos in range(16)
                            if layout[pos] is not None and is_picture(layout[pos])]

                if not pictures:
                    break

                n_pics = len(pictures)
                total_removed += n_pics
                
                for pos in pictures:
                    layout[pos] = None

                need_draw = n_pics

                if total_removed == 12:
                    break

            if total_removed == 12:
                break

            if round_num < 3:
                remaining = sorted(chain((c for c in layout if c is not None), deck))
                current_seed += 1
                seed(current_seed)
                shuffle(remaining)
                cards = remaining

        results[total_removed] += 1

    # Print results table
    print("Number of picture cards removed | Relative frequency")
    print("-" * 52)

    # Display results sorted by number of cards removed
    for k in sorted(results.keys()):
        pct = results[k] / n * 100

        # Format output for alignment
        k_str = str(k).rjust(31)
        pct_str = f"{pct:.2f}%".rjust(18)
        
        print(f"{k_str} | {pct_str}")


if __name__ == '__main__':
    user_input = int(input("Enter an integer to pass to the seed() function: "))
    play_game(user_input)
