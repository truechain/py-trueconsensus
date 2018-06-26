'use strict';

// https://explorer.nebulas.io/#/testnet/address/n1otzGZ87uv9NriHL5hW4Rka5SfkD7Edhxr

/**
state info


startInfo: {
  question: "Who will win the FIFA 2018?",
  oracle: "n1rwlkwerwelk6l7kwerer33wlr",
  // meta data about oracle.  eg. description.W
  oracleMeta: "http://data.com/oracleinfo", 
  outcomes: [
    "england",
    "italy",
    "brazil",
    "germany"
  ],
  betEndBlock: 367898, // block height where bet ends
}

oracleOutcome: 1, // outcome is specified by 0, 1, 2, 3

bets: []





format of bets
{
  user: "n1klklfj389jky5jhjdasl", // should be an address
  amount: 100, // may allow multi token later
  outcome: 1, // user bets on outcome 0, 1,2,3, or...
}

format of challenge
{
  user: "0xklafj389jky5jhjdasl", // should be an address
  amount: 100,
}

format of vote
{
  user: "n1klklfj389jky5jhjdasl", // should be an address
  amount: 1000,
  outcome: 1,
}



initMarket1 = {
  id: 1, // market id
  phaseTime: {}, // the start and end time of each phase (time in blockheight)
  bets: [],
  oracles: [], // list of approved oracles when market is created
  oracleOutcome: -1, // for hackathon, we only have one oracle, so we makes it simple.
                    // just one single result.  outcome is specified by 1, 2, ....
                    // 0 indicate no outcome yet
  //oracleOutcomes: [], // when oracle pushes the result, it is stored here.
  challenge: {},
  voteRecords: [], // list of all vote
  // votes: {
  //   outcome1: 0,
  //   outcome2: 0,
  //   outcome3: 0,
  // }, // aggregated result of vote
}
*/

const UNDEFINED_OUTCOME = -1;

var PredictContract = function() {};

// save value to contract, only after height of block, users can takeout
PredictContract.prototype = {
    init: function() {
        //TODO:
    },

    start: function(startInfo) {
        console.log("start()");
        // todo: sanitize inputs
        if (startInfo) {
            var from = Blockchain.transaction.from;
            var blockHeight = new BigNumber(Blockchain.block.height);
            startInfo.from = from;
            LocalContractStorage.set("startInfo", startInfo);
        }
    },

    bet: function(outcome) {
        console.log("bet().  outcome: ", outcome);
        // todo: sanitize inputs
        // todo: check phase and timing
        var from = Blockchain.transaction.from;
        var value = Blockchain.transaction.value;
        var blockHeight = new BigNumber(Blockchain.block.height);
        console.log("from: " + from + ", value: " + value + ", height: " + blockHeight);

        var bets;

        // for demo, we assume only 1 bet per person
        var betObj = {
            user: from,
            amount: value,
            outcome: outcome,
        }

        bets = LocalContractStorage.get("bets");
        if (!bets) {
            // bets not exist yet
            bets = [];

        } else {

        }
        console.log("bets before adding: ", bets);

        bets.push(betObj);

        console.log("bets: ", bets);
        LocalContractStorage.set("bets", bets);

        console.log("bet() ends");
    },

    oracle: function(outcome) {
        // for this demo, only one oracle result
        console.log("oracle().  outcome: ", outcome);
        // todo: sanitize inputs
        // todo: check phase and timing
        var from = Blockchain.transaction.from;
        var value = Blockchain.transaction.value;
        var blockHeight = new BigNumber(Blockchain.block.height);
        console.log("from: " + from + ", value: " + value + ", height: " + blockHeight);

        LocalContractStorage.set("oracleOutcome", outcome);

        console.log("oracle() ends");
    },


    distribute: function() {
        // distribute the token based on outcome
        // todo: make sure distribute can only be called once.
        console.log("distribute()");
        // todo: check phase and timing
        var from = Blockchain.transaction.from;
        var value = Blockchain.transaction.value;
        var blockHeight = new BigNumber(Blockchain.block.height);
        console.log("from: " + from + ", value: " + value + ", height: " + blockHeight);
        // from and value is not used here.


        var challenge = LocalContractStorage.get("challenge");
        var bets = LocalContractStorage.get("bets");
        var oracleOutcome = LocalContractStorage.get("oracleOutcome");
        var finalOutcome = oracleOutcome;
        var bet;
        var user;
        var amount;
        var userOutcome;
        var payoutAmount;
        var betsIdx = 0;
        var betPoolTotal = new BigNumber(0);
        var winnerPoolTotal = new BigNumber(0);
        var payouts = [];
        var distribution = {
            betPoolTotal: 0,
            winnerPoolTotal: 0,
        }
        var voteOutcome;

        // determine the outcome
        if (!challenge) {
            // if not challenged
            console.log("no challenge");
            Event.Trigger("distribute", "no challenge");
            finalOutcome = oracleOutcome;
        } else {
            Event.Trigger("distribute", "challenged.");
            voteOutcome = this.countVote();
            if (voteOutcome === UNDEFINED_OUTCOME) {
                finalOutcome = oracleOutcome;
            } else {
                finalOutcome = voteOutcome;
            }
        }

        Event.Trigger("distribute", "finalOutcome: " + finalOutcome);
        LocalContractStorage.set("finalOutcome", finalOutcome);
        // todo: deal with situation where there is no oracle outcome

        if (challenge && voteOutcome !== UNDEFINED_OUTCOME) {
            this.handlePayout("vote");
        }

        if (finalOutcome !== UNDEFINED_OUTCOME) {
            // distribute based on original outcome

            if (true) {

                if (bets) {
                    Event.Trigger("distribute", "bets: " + JSON.stringify(bets));

                    // calculate bet pool total and winner pool total amount.
                    // so we can calculate the payout based on ratio
                    // of user bet in the winning pool
                    for (betsIdx = 0; betsIdx < bets.length; betsIdx++) {
                        bet = bets[betsIdx];
                        Event.Trigger("distribute", "bets[" + betsIdx + "]: " + JSON.stringify(bet));
                        user = bet.user;
                        amount = bet.amount;
                        userOutcome = bet.outcome;
                        betPoolTotal = betPoolTotal.plus(amount);
                        if (finalOutcome == userOutcome) {
                            // winner pool
                            winnerPoolTotal = winnerPoolTotal.plus(amount);
                        }
                    }

                    Event.Trigger("distribute", "betPoolTotal: " + betPoolTotal + ", winnerPoolTotal: " + winnerPoolTotal);
                    console.log("betPoolTotal: " + betPoolTotal + ", winnerPoolTotal: " + winnerPoolTotal);
                    distribution.betPoolTotal = betPoolTotal;
                    distribution.winnerPoolTotal = winnerPoolTotal;
                    LocalContractStorage.set("distribution", distribution);


                    for (betsIdx = 0; betsIdx < bets.length; betsIdx++) {
                        bet = bets[betsIdx];
                        Event.Trigger("distribute", "bets[" + betsIdx + "]: " + JSON.stringify(bet));
                        user = bet.user;
                        amount = new BigNumber(bet.amount);
                        userOutcome = bet.outcome;
                        console.log("bet: ", bet);
                        // payout is user's bet in proportion to the entire pool.
                        // payout = ( userAmount / winnerPoolTotal ) * betPoolTotal
                        // todo: we might want to floor it to prevent multiple rounding to exceed the total payout
                        payoutAmount = amount.times(betPoolTotal).dividedBy(winnerPoolTotal);
                        Event.Trigger("distribute", "payoutAmount: " + payoutAmount);
                        console.log("payoutAmount: ", payoutAmount);

                        if (finalOutcome == userOutcome) {
                            Event.Trigger("distribute", "transfer " + payoutAmount + " to " + user);
                            console.log("transfer " + payoutAmount + " to " + user);
                            var payoutElem = {
                                user: user,
                                betAmount: amount,
                                payoutAmount: payoutAmount,
                            }
                            payouts.push(payoutElem);


                            var result = Blockchain.transfer(user, payoutAmount);
                            if (!result) {
                                Event.Trigger("distribute", "transfer failed: " + payoutAmount + " to " + user);
                                console.log("transfer failed");
                                throw new Error("transfer failed.");
                            } else {
                                Event.Trigger("distribute", "transfer result: " + JSON.stringify(result));
                            }
                        }
                    }

                    LocalContractStorage.set("payouts", payouts);
                    Event.Trigger("distribute", "payouts: " + JSON.stringify(payouts));
                }
            }
        }

        console.log("distribute() ends");
    },


    verifyAddress: function(address) {
        // 1-valid, 0-invalid
        var result = Blockchain.verifyAddress(address);
        return {
            valid: result == 0 ? false : true
        };
    },

    /** get prediction mkt info */
    getMktInfo: function() {
        return LocalContractStorage.get("startInfo");
    },

    /** return bet from a particular address */
    betOf: function(address) {

    },

    getBets: function() {
        return LocalContractStorage.get("bets");
    },

    getOracleOutcome: function() {
        return LocalContractStorage.get("oracleOutcome");
    },

    /** return challenge info */
    getChallenge: function() {
        return LocalContractStorage.get("challenge");
    },

    voteOf: function(address) {

    },

    getVotes: function() {
        return LocalContractStorage.get("votes");
    },

    /** get distribution info */
    getDistribution: function() {
        return LocalContractStorage.get("distribution");
    },

    /** get distribution info */
    getVoteDistribution: function() {
        return LocalContractStorage.get("voteDistribution");
    },

    /** get array of payout */
    getPayouts: function() {
        return LocalContractStorage.get("payouts");
    },

    getVotePayouts: function() {
        return LocalContractStorage.get("votePayouts");
    },

    /** return an object with the vote count for each outcome
     * eg. { "1": BigNumber(15), "2": BigNumber(1005) }
     * outcome: numVotes
     */
    getVoteCount: function() {
        return LocalContractStorage.get("voteCount");
    },

    /**
     * return the outcome based on vote
     * outcome could be -1 (undefined) if there is no vote
     */
    getVoteOutcome: function() {
        return LocalContractStorage.get("voteOutcome");
    },

};
module.exports = PredictContract;





/*


## market phase
1. open new market
2. allow bet
3. someone bets (record them)
4. market closes (by time)

## resolve phase

condition to enter phase: time

10. get datresolvea from oracle
11. determine the result and record it

condition to end phase: time

## challenge phase

condition to enter phase: time, someone triggers it

20. someone stake their coin and challenges

condition to end phase: time

## vote phase

condition to enter phase: challenge phase completed

30. anyone can stake their coin and vote

condition to end phase: time

## distribute phase
condition to enter phase: time

40. determine the final outcome

```
if (challenged)
  update the final outcome according to voting results
  distributed the staked coins in voting pool according to voting results.
distribute betting pool coins according to outcome
```

condition to end phase: when everything in the phase is executed

*/

