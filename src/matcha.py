import smartpy as sp

@sp.module
def main():
    class MatchaOptimisticOracle(sp.Contract):
        """
        Optimistic Oracle that allows anyone to assert to a statement which may
        or may not be truthful. Anyone asserting a statement must put up a bond
        to prove the sincerity of their statement.

        Once a statement is made there is a challenge / dispute window that allows
        anyone to challenge the statement provided they also put up a bond. The 
        process of challenging an assertion extends the challenge window allowing
        anyone else to further challenge.

        Each time the truthfulness of an assertion is challenge the disputer must
        put up an increased amount of collateral as a bond. Only disputers that 
        are ultimately judged to be making truthful disputes will have their bond
        returned (along with a proportion of the bond from the disputers that were
        found to be untruthful).

        Example:

        Bob could assert that "The max temperature in London on the 23rd of January 2023 was 10C"
        Alice could then contest this on chain if she knew better. If she was proved 
        to be correct she would keep not only the bond she paid to challenge but
        also Bob's bond (and any other bonds paid to further challenge her) too
        """
 
        def __init__(self):
            self.data.dispute_minimum_multiple = sp.nat(2)
            self.data.minimum_bond = sp.mutez(100)
            self.data.ledger = {}

        @sp.entrypoint
        def make_assertion(self, statement):
            """
            Assert a particular statement is true along with providing a bond which
            will be returned after the challenge / dispute window should the assertion
            be accepted as truthful by all participants

            Args:
                statement (string): assertion
            """
            # Record a new assertion
            assert sp.amount >= self.data.minimum_bond

            assertion = sp.record(
                due=sp.add_days(sp.now, 1),            # Dispute window close time
                asserter=sp.sender,                    # Address of asserter
                bond=sp.amount,                        # Amount paid by person asserting
                disputers=[],
                outcome=True,                          # Accepted opinion on assertion (currently)
                finalised=False                        # Finalised assertion (will not change)
            )

            self.data.ledger[statement] = assertion

        @sp.entrypoint
        def challenge_assertion(self, statement):
            """
            Any assertion that has been made untruthfully can be challenging within
            the challenge / dispute window. This function allows anyone to challenge
            an assertion provided they put up a bond and are within the allowed time
            period to do so

            Args:
                statement (string): assertion
            """
            # Ensure the asserting that is being challenge exists to be challenged
            assert self.data.ledger.contains(statement)
            assert self.data.ledger[statement].finalised == False
            assert self.data.ledger[statement].due < sp.now
            # Cost of dispute grows based on self.dispute_minimum_multiple factor
            number_of_disputes = len(self.data.ledger[statement].disputers)
            dispute_multiplier = number_of_disputes * self.data.dispute_minimum_multiple
            amount_required_to_dispute = number_of_disputes * dispute_multiplier

            # TODO : this is not correct but relies on a type conversion between
            # nat and mutez, the util is not working for some reason so hardcode for now
            assert sp.amount == sp.mutez(100) #utils.nat_to_mutez(amount_required_to_dispute)

            # TODO this pushes to the front of the list? Ideally stick on the back
            self.data.ledger[statement].disputers.push(sp.sender)

            # Flip the outcome
            self.data.ledger[statement].outcome = not self.data.ledger[statement].outcome

            # Extend the window to allow for counter challenges
            self.data.ledger[statement].due = sp.add_days(sp.now, 1)

        @sp.entrypoint
        def finalise_assertion(self, statement):
            """
            Once the challenge / dispute window for an assertion
            has passed anyone can finalise it. This formalises the outcome
            and returns:
            
            1. the bond placed by the original asserter (assuming they
            were not successfully challenged)
            2. the bond of all successful disputers

            Args:
                statement (string): assertion
            """
            assert self.data.ledger.contains(statement)
            # Ensure assertion can be finalised as the challenge window has passed
            assert self.data.ledger[statement].due > sp.now
            # Check it already wasn't finalsed
            assert self.data.ledger[statement].finalised == False

            self.data.ledger[statement].finalised = True

            remaining_bond = self.data.ledger[statement].bond
            
            # Sweetener for whoever finalises the outcome (1% bonus)
            if sp.sender != self.data.ledger[statement].asserter:
                bonus = sp.split_tokens(self.data.ledger[statement].bond, 1, 100)
                sp.send(sp.sender, bonus)
                remaining_bond = self.data.ledger[statement].bond - bonus
            
            if len(self.data.ledger[statement].disputers) == 0:
                # Assertion was not challenged, repay the bond
                sp.send(self.data.ledger[statement].asserter, remaining_bond)
            else:
                if self.data.ledger[statement].outcome == True:
                    # Outcome true, repay bond as if no disputes occurred
                    sp.send(self.data.ledger[statement].asserter, remaining_bond)

                # Since we just keep track of the order of disputes we
                # need to infer based on the fact that each dispute changed
                # the proposed outcome what each address voted for
                disputerVoted = False

                # Return funds based on the winning outcome
                for disputer in self.data.ledger[statement].disputers:
                    if disputerVoted == self.data.ledger[statement].outcome:
                        # This disputer won, repay their bond
                        # TODO: as with the line above where we are unable
                        #       to calculate the amount, each disputer pays a
                        #       fixed amount, so this makes it easy here to know
                        #       what we should return
                        # TODO: Simply multiplying by 2 here assumes the same number
                        #       of disputers for and against
                        disputeBondToReturn = sp.mutez(200)
                        sp.send(disputer, disputeBondToReturn)
        
        @sp.onchain_view()
        def has_assertion_been_made(self, statement):
            """
            Return whether a particular assertion has been made

            Args:
                statement (string): assertion
            """
            return self.data.ledger.contains(statement)

        @sp.onchain_view()
        def has_assertion_been_finalised(self, statement):
            """
            Return whether an assertion has been finalised and
            the dispute period has finished. If this returns false
            an assertion may still be challenged

            Args:
                statement (string): assertion
            """
            assert self.data.ledger.contains(statement)
            return not self.data.ledger[statement].finalised

        @sp.onchain_view()
        def when_does_assertion_finalise(self, statement):
            """
            Return when the challenge / dispute window will/did 
            close for a particular assertion

            Args:
                statement (string): assertion
            """
            assert self.data.ledger.contains(statement)
            return self.data.ledger[statement].due
        
        @sp.onchain_view()
        def get_assertion_result(self, statement):
            """
            Return the current belief as to the validity of 
            the assertion. This will return whether an assertion
            that was made is currently believed to be true or false.

            NOTE that this can change up until the assertion is
            finalised. Do not take the value as the final result
            without also checking that has_assertion_been_finalised
            returns true

            Args:
                statement (string): assertion
            """
            assert self.data.ledger.contains(statement)
            return self.data.ledger[statement].outcome
            

if "templates" not in __name__:
    # Initialize test scenario
    scenario = sp.test_scenario()
    
    # Define test parameters
    minimum_bond = sp.mutez(100)
    dispute_minimum_multiple = sp.nat(2)
    assertion = "The max temperature in London on the 23rd of January 2023 was 10C"
    
    # Deploy the MatchaOptimisticOracle contract
    contract = scenario.add_module(main.MatchaOptimisticOracle)
    
    # Test case 1: Make an assertion
    @scenario
    def test_make_assertion():
        scenario.h1("Make an assertion")
        contract.make_assertion(statement=assertion).run(sender=sp.address("alice"), amount=minimum_bond)
    
    # Test case 2: Challenge an assertion
    @scenario
    def test_challenge_assertion():
        scenario.h1("Challenge an assertion")
        contract.challenge_assertion(statement=assertion).run(sender=sp.address("bob"), amount=minimum_bond)
    
    # Test case 3: Finalize an assertion
    @scenario
    def test_finalize_assertion():
        scenario.h1("Finalize an assertion")
        contract.finalise_assertion(statement=assertion).run(sender=sp.address("carol"))
    
    # Test case 4: Check if an assertion has been made
    @scenario
    def test_has_assertion_been_made():
        scenario.h1("Check if an assertion has been made")
        contract.has_assertion_been_made(statement=assertion).assert_equal(True)
    
    # Test case 5: Check if an assertion has been finalized
    @scenario
    def test_has_assertion_been_finalised():
        scenario.h1("Check if an assertion has been finalized")
        contract.has_assertion_been_finalised(statement=assertion).assert_equal(True)
    
    # Test case 6: Get the finalization time of an assertion
    @scenario
    def test_when_does_assertion_finalise():
        scenario.h1("Get the finalization time of an assertion")
        contract.when_does_assertion_finalise(statement=assertion).assert_greater(0)
    
    # Test case 7: Get the result of an assertion
    @scenario
    def test_get_assertion_result():
        scenario.h1("Get the result of an assertion")
        contract.get_assertion_result(statement=assertion).assert_equal(True)
    
    # Run the test scenarios
    scenario.verify()