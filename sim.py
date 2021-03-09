from typing import Any, List, Set, Dict, Tuple
import random
from abc import ABC, abstractmethod


class Card:
    def __init__(self, colour: str, number: int, type: str = "normal"):
        self.colour = colour
        self.number = number
        self.type = type


class Hand:
    def __init__(self, cards: List[Card]):
        if len(cards) < 10 or len(cards) > 10:
            raise Exception("Invalid number of cards")
        self.cards = cards

    def print(self):
        for i, card in enumerate(self.cards):
            print('Card {}: C: {}/N:{}'.format(i, card.colour, card.number))


def init_deck():
    deck: List[Card] = []
    colours = ["green", "yellow", "red", "blue"]
    for colour in colours:
        for i in range(1, 13):
            deck.append(Card(colour, i))
    for i in range(8):
        deck.append(Card("black", -1, "joker"))

    random.shuffle(deck)

    return deck


deck = init_deck()

hand = Hand(deck[0:10])
hand.print()


class Condition(ABC):

    def __init__(self, required_number: int, sub_conditions: Set['Condition'] = []) -> None:
        super().__init__()
        self.required_number = required_number
        self.sub_conditions = sub_conditions

    def hand_passed(self, hand: Hand) -> bool:
        possibilities = self.possibilities(hand)
        if(len(possibilities) > 0):
            return True
        return False

    @abstractmethod
    def possibilities(self, hand: Hand) -> List[Set[int]]:
        pass


class SetBased(Condition):
    def __init__(self, required_number: int) -> None:
        super().__init__(required_number)

    def internal_possibilities(self, prefix: Set[int], sub_range: List[int], remaining_levels: int) -> List[Set[int]]:
        remover_idx = 0
        sub_combinations: List[Set[int]] = []
        if remaining_levels == 1:
            for rem in range(len(sub_range)):
                list_modified = sub_range[:]
                del list_modified[rem]
                sub_combinations.append(set(list_modified).union(prefix))
        else:
            for rem in range(len(sub_range)-remaining_levels+1):
                list_modified = sub_range[:]
                del list_modified[rem]
                prefix_ = set(list_modified[0:rem])
                sub_range_ = list_modified[rem:]
                possibilities = self.internal_possibilities(
                    prefix_, sub_range_, remaining_levels-1)
                sub_combinations.extend(possibilities)
        for sub_combination in sub_combinations:
            sub_combination.update(prefix)

        return sub_combinations

    @abstractmethod
    def find_matches(self, hand: Hand, colour: str = "any", number: int = -1) -> List[Set[int]]:
        pass

    @abstractmethod
    def candidates(self, hand: Hand) -> List[Tuple[str, int]]:
        pass

    def possibilities(self, hand: Hand) -> List[Set[int]]:
        possibilities = []
        candidates = self.candidates(hand)
        for candidate in candidates:
            candidate_possibilities = self.find_matches(
                hand, candidate[0], candidate[1])
            possibilities.extend(candidate_possibilities)
        return possibilities


class ListBased(Condition):
    def __init__(self, required_number: int) -> None:
        super().__init__(required_number)

    def get_combinations(self, remaining_list: List[Set[int]]) -> List[Set[int]]:
        combinations: List[Set[int]] = []
        if len(remaining_list) == 1:

            return [set([pos]) for pos in remaining_list[0]]
        else:
            sub_combinations = self.get_combinations(remaining_list[1:])
            for position in remaining_list[0]:
                for sub_combination in sub_combinations:
                    extended_set = sub_combination.union([position])
                    combinations.append(extended_set)
        return combinations

    def get_possibilities(self, full_list: List[Set[int]]) -> List[Set[int]]:
        sub_combinations: List[Set[int]] = []

        for i in range(len(full_list)-self.required_number+1):
            sub_range = full_list[i:self.required_number+i]

            combinations_on_list = self.get_combinations(sub_range)

            sub_combinations.extend(combinations_on_list)
        return sub_combinations

    def possibilities(self, hand: Hand) -> List[Set[int]]:
        possibilities = []
        candidates = self.candidates(hand)
        current_number = 1

        while current_number <= 12:
            streak: List[Set[int]] = []
            available_jokers = list(filter(
                lambda card: card[1].number == -1, candidates))
            streak_broken = False

            while not streak_broken:
                number_cards = list(filter(
                    lambda card: card[1].number == current_number, candidates))
                if len(number_cards) == 0 and len(available_jokers) > 0:
                    streak.append(set([available_jokers.pop()[0]]))
                elif len(number_cards) > 0:
                    streak.append(set([card[0] for card in number_cards]))
                else:
                    streak_broken = True
                current_number += 1
            possibilities.extend(self.get_possibilities(streak))
        return possibilities

    @ abstractmethod
    def candidates(self, hand: Hand) -> List[Card]:
        pass


class SameNumber(SetBased):
    def __init__(self, required_number: int) -> None:
        super().__init__(required_number)

    def candidates(self, hand: Hand) -> List[Tuple[str, int]]:
        available_numbers = set(
            [card.number for card in hand.cards if card.number != -1])
        return [("any", number) for number in available_numbers]

    def find_matches(self, hand: Hand, colour: str = "any", number: int = -1) -> List[Set[int]]:
        # return super().find_matches(colour, number)
        matches: List[int] = []
        for i, card in enumerate(hand.cards):
            if card.number == number or card.number == -1:
                matches.append(i)

        if len(matches) < self.required_number:
            return []

        if len(matches) == self.required_number:
            return [set(matches)]
        return self.internal_possibilities(set(), matches, len(matches)-self.required_number)


class SameColour(SetBased):
    def __init__(self, required_number: int) -> None:
        super().__init__(required_number)

    def candidates(self, hand: Hand) -> List[Tuple[str, int]]:
        available_colours = set(
            [card.colour for card in hand.cards if "black" not in card.colour])
        return [(colour, -1) for colour in available_colours]

    def find_matches(self, hand: Hand, colour: str = "any", number: int = -1) -> List[Set[int]]:
        # return super().find_matches(colour, number)
        matches: List[int] = []
        for i, card in enumerate(hand.cards):
            if card.colour == colour or card.number == -1:
                matches.append(i)

        if len(matches) < self.required_number:
            return []

        if len(matches) == self.required_number:
            return [set(matches)]
        return self.internal_possibilities(set(), matches, len(matches)-self.required_number)


class AnyList(ListBased):
    def __init__(self, required_number: int) -> None:
        super().__init__(required_number)

    def candidates(self, hand: Hand) -> List[Card]:
        return sorted(enumerate(hand.cards), key=lambda card: card[1].number)


class SameColourList(AnyList):
    def __init__(self, required_number: int) -> None:
        super().__init__(required_number)

    def all_same_colour(self, hand: Hand, positions: Set[int]) -> bool:
        targets = list(
            filter(lambda pos: hand.cards[pos].number != -1, positions))
        if len(targets) == 0:
            return True
        target = hand.cards[targets[0]]
        for pos in positions:
            if target.colour not in hand.cards[pos].colour:
                return False
        return True

    def possibilities(self, hand: Hand) -> List[Set[int]]:
        all_list_possibilities = super().possibilities(hand)
        return list(filter(lambda possibilities: self.all_same_colour(hand, possibilities), all_list_possibilities))


class GroupCondition(Condition):
    def __init__(self, sub_conditions: Set[Condition] = []) -> None:
        super().__init__(0, sub_conditions)

    def possibilities(self, hand: Hand) -> bool:
        sub_possibilities = [condition.possibilities(
            hand) for condition in self.sub_conditions]

        remaining_possibilities: List[Set[int]] = []
        for i in range(len(sub_possibilities)):
            if i == 0:
                remaining_possibilities.extend(sub_possibilities[i])
            else:
                b_poss_s = sub_possibilities[i]
                new_poss = []
                for a_poss in remaining_possibilities:
                    for b_poss in b_poss_s:
                        if a_poss.isdisjoint(b_poss):
                            new_poss.append(a_poss.union(b_poss))
                remaining_possibilities = new_poss
        return remaining_possibilities


test_hand = Hand([
    Card("blue", 1),  # 0
    Card("blue", 2),  # 1
    Card("blue", 3),  # 2
    Card("red", 4),  # 3
    Card("red", 5),  # 4
    Card("red", 6),  # 5
    Card("red", 6),  # 6
    Card("red", -1),  # 7
    Card("red", -1),  # 8
    Card("red", -1),  # 9
])

four_list = SameColourList(3)
four_colours = SameColour(4)

combination = GroupCondition([four_list, four_colours])

posssibles = combination.possibilities(test_hand)

n_sims = 1e4


class Experiment:
    def __init__(self, condition: Condition) -> None:
        self.condition = condition
        self.runs = 0
        self.successes = 0

    def run(self, hand: Hand):
        self.runs += 1
        if(self.condition.hand_passed(hand)):
            self.successes += 1

    def rate(self):
        return float(self.successes)/self.runs


experiments_done = {
    # einfach
    "drei-zwillinge": Experiment(GroupCondition([SameNumber(2), SameNumber(2), SameNumber(2)])),
    "fünf-einer-farbe": Experiment(SameColour(5)),
    "drillinge+dreierfolge": Experiment(GroupCondition([SameNumber(3), AnyList(3)])),
    "zwilling+dreierfolge": Experiment(GroupCondition([SameNumber(2), AnyList(3)])),
    "zwei-drillinge": Experiment(GroupCondition([SameNumber(3), SameNumber(3)])),
    # mittel
    "sech-einer-farbe": Experiment(SameColour(6)),
    "siebernerfolge": Experiment(AnyList(7)),
    "sechsersnerfolge": Experiment(AnyList(6)),
    "vier-zwillinge": Experiment(GroupCondition([SameNumber(2), SameNumber(2), SameNumber(2), SameNumber(2)])),
    "drillinge+viererfolge": Experiment(GroupCondition([SameNumber(3), AnyList(4)])),
    "zwillinge+viererfolge": Experiment(GroupCondition([SameNumber(2), AnyList(4)])),
    "fünfling": Experiment(SameNumber(5)),
    "drillinge+vier-einer-farbe": Experiment(GroupCondition([SameNumber(3), SameColour(4)])),
    # schwer
    "sieben-einer-farbe": Experiment(SameColour(7)),
    "siebernerfolge": Experiment(AnyList(8)),
    "fünfling-zwillinge": Experiment(GroupCondition([SameNumber(5), SameNumber(2)])),
    "neunerfolge": Experiment(AnyList(9)),
    "zwei-vierlinge": Experiment(GroupCondition([SameNumber(4), SameNumber(4)])),
    "viererfolge einer f.+zwilling": Experiment(GroupCondition([SameColourList(4), SameNumber(2)])),
    "viererfolge einer f.+drilling": Experiment(GroupCondition([SameColourList(4), SameNumber(3)])),
    "acht-einer-farbe": Experiment(SameColour(8)),
    "fünfererfolge einer f.": Experiment(SameColourList(5)),
    # sehr schwer
    "fünfererfolge einer f.+drilling": Experiment(GroupCondition([SameColourList(5), SameNumber(3)])),
    "viererfolge einer f.+dreierfolge": Experiment(GroupCondition([SameColourList(4), AnyList(3)])),
    "viererfolge einer f.+drilling": Experiment(GroupCondition([SameColourList(4), SameNumber(3)])),
    "fünfling+drillinge": Experiment(GroupCondition([SameNumber(5), SameNumber(3)])),
    "fünfling+dreierfolge einer f.": Experiment(GroupCondition([SameNumber(5), SameColourList(3)])),
    "vierlinge+viererfolge einer f.": Experiment(GroupCondition([SameNumber(4), SameColourList(4)])),


}

experiments = {
    "5er+4erfolge": Experiment(GroupCondition([AnyList(5), AnyList(4)])),
}
for sim in range(int(n_sims)):
    deck = init_deck()
    hand = Hand(deck[0:10])
    if sim % 100:
        print("Sim {}/{} ({} done)".format(sim, n_sims, (sim/n_sims)*100))
    for experiment in experiments:
        experiments[experiment].run(hand)

for experiment in experiments:
    print("Experiment {} has success rate of {}".format(
        experiment, experiments[experiment].rate()*100))
