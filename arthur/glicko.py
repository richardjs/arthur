import math


NEW_RATING = 1500
NEW_RD = 350
C = 0

q = math.log(10) / 400


class Rating:
    def __init__(self, r=NEW_RATING, rd=NEW_RD):
        self.r = r
        self.rd = rd

    def _e(self, opponent):
        return 1 / (1 + 10 ** (-opponent._g() * (self.r - opponent.r) / 400))

    def _g(self, rd=None):
        if not rd:
            rd = self.rd
        return 1 / math.sqrt((1 + 3 * q**2 * rd**2 / math.pi**2))

    def update(self, wins=[], losses=[], draws=[]):
        d2 = (
            q**2
            * sum(
                opponent._g() ** 2 * self._e(opponent) * (1 - self._e(opponent))
                for opponent in wins + losses + draws
            )
        ) ** -1

        r = self.r + (q / (1 / self.rd**2 + 1 / d2)) * sum(
            opponent._g() * (score - self._e(opponent))
            for score, opponent in (
                [(1, opponent) for opponent in wins]
                + [(0, opponent) for opponent in losses]
                + [(0.5, opponent) for opponent in draws]
            )
        )

        rd = math.sqrt((1 / self.rd**2 + 1 / d2) ** -1)

        return Rating(r, rd)

    def expected(self, opponent):
        return 1 / (
            1
            + 10
            ** (
                -self._g(math.sqrt(self.rd**2 + opponent.rd**2))
                * (self.r - opponent.r)
                / 400
            )
        )

    def __str__(self):
        return f"r={self.r} rd={self.rd}"
