import smartpy as sp

@sp.module
def main():
    class MatchaOptimisticOracle(sp.Contract):
        """
        """

        def __init__(self, initialDuration):
            """Constructor

            Args:
                admin (sp.address): admin of the contract.
                initialDuration (sp.nat): Number of days before a deposit can be withdrawn.
            """
            #sp.cast(statements, sp.set[t.statement])
            self.dispute_minimum_multiple = 2
            self.minimum_bond = 100
            self.data.ledger = {}

        @sp.entrypoint
        def make_assertion(self, statement):
            # Record a new assertion
            # TODO force sending of funds (amount)
            assert sp.amount >= self.minimum_bond
            
            self.data.ledger[statement] = sp.record(
                due=sp.add_days(sp.now, 1),            # Dispute window close time
                asserter=sp.sender,                    # Address of asserter
                bond=sp.amount,                        # Amount paid by person asserting
                disputers=[],
                outcome=True,                          # Accepted opinion on assertion (currently)
                finalised=False                        # Finalised assertion (will not change)
            )

        @sp.entrypoint
        def challenge_assertion(self, statement):
            # Ensure the asserting that is being challenge exists to be challenged
            assert self.data.ledger.contains(statement)
            assert self.data.ledger[statement].finalised == False
            assert self.data.ledger[statement].due < sp.now
            # Cost of dispute grows based on self.dispute_minimum_multiple factor
            amount_required_to_dispute = len(self.data.ledger[statement].disputers) * self.data.ledger[statement].bond * self.dispute_minimum_multiple
            disputers.push(sp.sender)

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
            #if len(self.data.ledger[statement].disputers) /2 == 0:
                # Outcome true, repay bond
                