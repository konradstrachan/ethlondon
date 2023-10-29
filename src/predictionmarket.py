import smartpy as sp

@sp.module
def main():
    class PredictezPredictionMarket(sp.Contract):
        """
        Prediction market that allows anyone to bet on the outcome of an event.

        For example: 
            Someone can propose that "Biden will with the US Election in 2024"
            The prediction market could open immediately and be set to end just
            before the outcome is announced on 5 November 2024

            Anyone can place a bet either that the claim is true or false until
            that time. Once the end time is reached, the Prediction Market will
            Assert the outcome using the Optimistic Oracle and use the despute
            mechanism to achieve finality on the statement. At this point any
            bet that matches the winning outcome will be paid out
        """
                    
        def __init__(self):
            self.data.claims = {}

        @sp.entry_point
        def propose_claim(self, prediction, start_time, end_time):
            """
            Create a new claim that creates a market that others can speculate on. 
            All claims must evaluate to Yes / No (True/False) statements which 
            can then be evaluated based on fact.

            e.g. The max temperature in London on 29/10/23 will be 19C

            Args:
                prediction (string): name of market
            """
            # Make sure the claim hasn't already been proposed
            assert not self.data.claims.contains(prediction)
            # Sanity check timining
            assert start_time < end_time
            # Can't create a claim that can't become active
            assert sp.now < end_time
            # Prevent spam by requiring the proposer to initialise the
            # pool with a small amount of funds asserting the positive
            # outcome
            assert sp.amount >= sp.mutez(100)

            self.data.claims[prediction] = sp.record(
                start_time = start_time,
                end_time = end_time,
                finalising = False,
                finalised = False,
                outcome = False,
                bets = {},
                poolTrue = sp.amount,
                poolFalse = 0
            )

        @sp.entry_point
        def place_bet(self, prediction, outcome):
            """
            Enables anyone to place a bet on a prediction market currently active
            either betting the outcome is positive (true) or negative (false)

            Args:
                prediction (string): name of market
            """
            assert self.data.claims.contains(prediction)

            claim = self.data.claims[prediction]
            # Betting is not allowed yet
            assert claim.start_time <= sp.now 
            # Betting has finished
            assert claim.end_time > sp.now 
            # Market has not yet finished
            assert claim.resolved == False
            # Bet amount must be greater than a small base amount
            # to prevent spam and inflated compute cost on payout
            assert sp.amount > sp.mutez(10)

            predicted_outcome = sp.cast(bool, outcome)

            if predicted_outcome:
                self.data.claims[prediction].poolTrue += sp.amount
            else:
                self.data.claims[prediction].poolFalse += sp.amount

            bet = sp.record(bettor=sp.sender, amount=sp.amount, claimIsTrue=predicted_outcome)
            self.data.claims[prediction].bets.push(bet)

        @sp.entry_point
        def close_market_and_assert_outcome(self, prediction):
            """
            Once the end time has passed the market will go into a despute
            resolution mode whereby the claim that has been bet against will
            be proposed to the Optimistic Oracle. This starts the process of
            challenging / disputing the claim which enables the final result
            to be stored and the winning betters to be paid

            Args:
                prediction (string): name of market
            """
            assert self.data.claims.contains(prediction)

            claim = self.data.claims[prediction]
            # Check claim is not already resolved
            assert claim.resolved == False
            # Make sure the end of the prediction period has come
            assert sp.now > claim.end_time 
            # Process to get outcome hasn't already begun
            assert claim.finalising == False
            
            # use OO to start a dispute window to verify the outcome
            claim.finalising = True

            # TODO it's not clear using inheritance or composition how this works 
            # so this logic has been mocked out for sake of completion
            # An example of how it could be called is provided
            #PredictezOptimisticOracle.make_assertion(prediction)

        @sp.entry_point
        def finalise_outcome(self, prediction):
            """
            Once the end time has passed the market and the claim has finished
            the challenge / dispute claim window, this will finalise the outcome
            and pay the winners

            Args:
                prediction (string): name of market
            """
            assert self.data.claims.contains(prediction)

            claim = self.data.claims[prediction]
            # Make sure the end of the prediction period has come (belt and braces)
            assert sp.now > claim.end_time 
            # Make sure the market is waiting for the confirmed outcome
            assert claim.finalising == True
            # Check claim is not already been finalised and paid out
            assert claim.resolved == False
            
            # TODO it's not clear using inheritance or composition how this works 
            # so this logic has been mocked out for sake of completion
            # An example of how it could be called is provided
            
            #assert PredictezOptimisticOracle.has_assertion_been_finalised() == True
            #oo_assertion_result_final PredictezOptimisticOracle.get_assertion_result()
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

        @sp.onchain_view()
        def has_prediction_market(self, prediction):
            """
            Return whether a prediction market exists

            Args:
                prediction (string): name of market
            """
            return self.data.claims.contains(prediction)
        
        @sp.onchain_view()
        def prediction_market_start(self, prediction):
            """
            Return starting time of a prediction market

            Args:
                prediction (string): name of market
            """
            return self.data.claims[prediction].start_time
        
        @sp.onchain_view()
        def prediction_market_end(self, prediction):
            """
            Return ending time of a prediction market

            Args:
                prediction (string): name of market
            """
            return self.data.claims[prediction].end_time
