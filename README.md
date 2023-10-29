# ETHLondon 2023 Hackathon: Predictez Project

This repository contains the Predictez (Predict + Tezos) project developed during the ETH London 2023 hackathon.

![image](https://github.com/konradstrachan/ethlondonhackathon2023/assets/21056525/35b0d539-c4ef-4c14-9037-738442421b1e)

## Overview

Predictez is a proof of concept prediction market platform built on the Tezos blockchain using [SmartPy](smartpy.io). It combines the power of prediction markets with the security and decentralization of Tezos. The platform includes two main smart contracts: **PredictezOptimisticOracle** and **PredictezPredictionMarket**. PredictezOptimisticOracle handles the assertion of any fact and dispute process to ensure truthfulness, while PredictezPredictionMarket facilitates prediction market operation and betting on facts that are asserted and finalised on the Oracle.

## PredictezOptimisticOracle

![image](https://github.com/konradstrachan/ethlondonhackathon2023/assets/21056525/47e98404-160a-41f1-b497-0af9cd646be9)

### Description

PredictezOptimisticOracle is an Optimistic Oracle smart contract that allows anyone to assert a statement, which may or may not be truthful. Assertions are made by putting up a bond to prove the sincerity of the statement. When a statement is made it is assumed to be valid by default (Optimistically) however a challenge dispute window opens allowing and anyone can challenge the assertion by putting up their own bond. Each subsequent challenge requires the payment of an increased bond amount disincentivising untruthful participation as all participants found to be acting truthfully will have their bonds (and a share of untruthful bonds) returned to them.

### Functions

- **make_assertion**: Assert a statement as true and provide a bond. The bond will be returned if the assertion is accepted as truthful by all participants.

- **challenge_assertion**: Challenge an assertion within the dispute window by providing a bond. If the challenge is successful, the challenger receives the bond.

- **finalise_assertion**: Finalize an assertion once the challenge window has passed. This formalizes the outcome and returns the bonds placed by the original asserter and successful disputers.

### Views

- **has_assertion_been_made**: Check if a particular assertion has been made.

- **has_assertion_been_finalised**: Check if an assertion has been finalized and the dispute period has finished.

- **when_does_assertion_finalise**: Get the timestamp for when the challenge/dispute window will close for a particular assertion.

- **get_assertion_result**: Get the current belief about the validity of an assertion.

## PredictezPredictionMarket

### Description

PredictezPredictionMarket is a prediction market smart contract that allows users to bet on the outcome of a specific event. Anyone can create a new prediction market by proposing a statement and users can place bets on whether they believe the outcome of the statement will be true or false. 

For example: 

Someone can propose that:

"Biden will with the US Election in 2024" 

The prediction market could open immediately and be set to end just before the outcome is announced on 5 November 2024.

Alternatively:

"The price of Bitcoin will rise above $40k before the end of 2023" 

Anyone can bet as many times as they like on either positive or negative outcome of the statement as more information becomes available until the market closes. 

Once the end time is reached, the Prediction Market will assert the outcome using the Optimistic Oracle and use the despute mechanism to achieve finality on the statement. At this point any bet that matches the winning outcome will be paid out.

### Functions

- **propose_claim**: Create a new prediction market by proposing a claim, specifying the start and end times for the market. The claim must evaluate to a binary outcome (True/False).

- **place_bet**: Allow anyone to place a bet on an active prediction market, betting on either the positive (True) or negative (False) outcome.

- **close_market_and_assert_outcome**: Once the end time is reached, this function initiates the dispute resolution process to determine the outcome of the claim.

- **finalise_outcome**: Finalize the outcome of the prediction market and pay out the winning betters based on the Optimistic Oracle's result.

### Views

- **has_prediction_market**: Check if a prediction market with a given name exists.

- **prediction_market_start**: Get the start time of a prediction market.

- **prediction_market_end**: Get the end time of a prediction market.

## Getting Started

To get started with the Predictez project, follow the steps below:

1. Deploy the PredictezOptimisticOracle and PredictezPredictionMarket contracts on the Tezos blockchain.

2. Use the PredictezOptimisticOracle contract to make assertions and challenge statements.

3. Create prediction markets using the PredictezPredictionMarket contract by proposing claims.

4. Place bets on active prediction markets by using the `place_bet` function.

5. When a prediction market ends, use the `close_market_and_assert_outcome` function to initiate the dispute resolution process.

6. Finalize the outcome of the prediction market with the `finalise_outcome` function.

## Example

Here's a simple example of using PredictezOptimisticOracle and PredictezPredictionMarket:

```python
# Deploy the PredictezOptimisticOracle and PredictezPredictionMarket contracts.

# Make assertions on PredictezOptimisticOracle.
PredictezOptimisticOracle.make_assertion("The max temperature in London on 29/10/23 will be 19C")
# Challenge an assertion.
PredictezOptimisticOracle.challenge_assertion("The max temperature in London on 29/10/23 will be 19C")
# Finalize an assertion.
PredictezOptimisticOracle.finalise_assertion("The max temperature in London on 29/10/23 will be 19C")

# Create a prediction market on PredictezPredictionMarket.
PredictezPredictionMarket.propose_claim("Biden will win the US Election in 2024", start_time, end_time)
# Place bets on the prediction market.
PredictezPredictionMarket.place_bet("Biden will win the US Election in 2024", True)
PredictezPredictionMarket.place_bet("Biden will win the US Election in 2024", False)
# Close the prediction market and initiate the dispute resolution process.
PredictezPredictionMarket.close_market_and_assert_outcome("Biden will win the US Election in 2024")
# Finalize the outcome of the prediction market.
PredictezPredictionMarket.finalise_outcome("Biden will win the US Election in 2024")
