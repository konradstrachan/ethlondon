import smartpy as sp

@sp.module
def main():
    class MatchaPredictionMarket(sp.Contract):
        def __init__(self):
            self.data.claims = {}

        @sp.entry_point
        def propose_claim(self, prediction, startTime, endTime):
            assert startTime < endTime

            self.data.claims[prediction] = sp.record(
                startTime = startTime,
                endTime = endTime,
                finalising = False,
                finalised = False,
                outcome = False,
                bets = {},
                poolTrue = 0,
                poolFalse = 0
            )

        @sp.entry_point
        def place_bet(self, prediction, outcome):
            claim = self.data.claims[prediction]
            # Betting is not allowed yet
            assert claim.startTime <= sp.now 
            # Betting has finished
            assert claim.endTime > sp.now 
            # Market has not yet finished
            assert claim.resolved == False
            # Bet amount must be greater than 0
            assert sp.amount > 0

            predicted_outcome = sp.cast(bool, outcome)

            if predicted_outcome:
                self.data.claims[prediction].poolTrue += sp.amount
            else:
                self.data.claims[prediction].poolFalse += sp.amount

            bet = sp.record(bettor=sp.sender, amount=sp.amount, claimIsTrue=predicted_outcome)
            self.data.claims[prediction].bets.push(bet)

        @sp.entry_point
        def close_market_and_assert_outcome(self, prediction):
            claim = self.data.claims[prediction]
            # Check claim is not already resolved
            assert claim.resolved == False
            # Make sure the end of the prediction period has come
            assert sp.now > claim.endTime 
            # Process to get outcome hasn't already begun
            assert claim.finalising == False
            
            # TODO use OO to start a dispute window to verify the outcome
            claim.finalising = True

        @sp.entry_point
        def finalise_outcome(self, prediction):
            claim = self.data.claims[prediction]
            # Make sure the end of the prediction period has come (belt and braces)
            assert sp.now > claim.endTime 
            # Make sure the market is waiting for the confirmed outcome
            assert claim.finalising == True
            # Check claim is not already been finalised and paid out
            assert claim.resolved == False
            
            # TODO check outcome has been finalised in OO
            oo_has_assertion_been_finalised = True
            oo_assertion_result_final = True

            # Claim assertion has now been finalised
            claim.finalising = False
            claim.resolved = True

            claim.outcome = oo_assertion_result_final

            totalPrizePool = claim.poolTrue + claim.poolFalse

            # Go through and pay the winners from the pool of bets
            for bet in claim.bets:
                if claim.outcome == bet.claimIsTrue:
                    outcomePool = 0

                    if claim.outcome == True:
                        outcomePool = claim.poolTrue
                    else:
                        outcomePool = claim.poolFalse

                    # Share of winnings proportional to the total funds as
                    # a fraction of the bet as a fraction of the winning pool 
                    winnings = (bet.amount / outcomePool) * totalPrizePool

                    sp.send(bet.bettor, winnings)
                    #sp.emit(RewardPaid(sp.sender, winnings))

            self.data.claims[prediction].resolved = True

        # TODO VIEW METHOD
