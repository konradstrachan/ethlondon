import smartpy as sp

@sp.module
def main():
    class MatchaOptimisticOracle(sp.Contract):
        """
        """
 
        def __init__(self):
            """Constructor

            Args:
            """
            self.data.dispute_minimum_multiple = sp.nat(2)
            self.data.minimum_bond = sp.mutez(100)
            self.data.ledger = {}

        @sp.entrypoint
        def test(self):
            a = [1,2,3,4]
            b = 0
            for v in a:
                b = b + v

        @sp.entrypoint
        def make_assertion(self, statement):
            # Record a new assertion
            # TODO force sending of funds (amount)
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
            assert self.data.ledger.contains(statement)
            # Ensure assertion can be finalised as the challenge window has passed
            assert self.data.ledger[statement].due > sp.now
            # Check it already wasn't finalsed
            assert self.data.ledger[statement].finalised == False

            self.data.ledger[statement].finalised = True
            
            if len(self.data.ledger[statement].disputers) == 0:
                # Assertion was not challenged, repay the bond
                sp.send(self.data.ledger[statement].asserter, self.data.ledger[statement].bond)
            else:
                if self.data.ledger[statement].outcome == True:
                    # Outcome true, repay bond as if no disputes occurred
                    sp.send(self.data.ledger[statement].asserter, self.data.ledger[statement].bond)

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
                        disputeBondToReturn = sp.mutez(100)
                        sp.send(disputer, disputeBondToReturn)

if "templates" not in __name__:
    asserter = sp.test_account("Bob")
    challenger = sp.test_account("Alice")

    @sp.add_test(name="Basic Proposing test", is_default=True)
    def basic_scenario():
        scenario = sp.test_scenario()
        scenario.add_module(main)
        
        scenario.h1("Proposing test")
        scenario.h1("Propose assertion")
        
        # Create contract
        c = main.MatchaOptimisticOracle()
        # Add contract object to scenario
        scenario += c

        #c.delegate(admin.public_key_hash).run(sender=admin, voting_powers=voting_powers)

    #@sp.add_test(name="Full")
    #def test():
    #    sc = sp.test_scenario([main, testing])
    #    sc.h1("Full test")
    #    sc.h2("Origination")
    #    c = main.BakingSwap(admin.address, 0, 10000)
    #    sc += c
    #    sc.h2("Delegator")
    #    delegator = testing.Receiver()
    #    sc += delegator
    #    sc.h2("Admin receiver")
    #    admin_receiver = testing.Receiver()
    #    sc += admin_receiver