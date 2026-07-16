
use std::collections::HashMap;

use rust_decimal::Decimal;

pub enum PmSport {
    Baseball,
    Basketball,
    Soccer,
    Tennis,
}

pub enum PmUnitClass {
    Binary,
    HandicapMargin,
    Participant,
    Total,
}

// pub enum PmUnitClass {
//     Binary(bool),            // unit="Yes"  / unit="No"
//     HandicapMargin(Decimal), // e.g. unit="+3.5"
//     Participant(String),     // e.g. unit="Home Team"
//     Total(Decimal),          // e.g. unit=2.5  ("over/under 2.5 goals")
// }

// // internal id
// // sports: sport-date-league-resolution-.....
// // politics: politics-date-resolution.....

// pub enum Key {
//     Domain, // politics, soccer, crypto
//     Date,
//     League,
//     ResolutionMechanic, // totals, spreads...
// }

pub struct PmDimension {
    pub key: String,   // TODO enum? period | participant | market_type
    pub value: String, // TODO enum? full_game | combined | total
}

// TODO one for each sport?
pub enum PmSettlementMechanic {
    // # Defines the resolution logic applied to all outcomes in this market.
    // #
    // # "over"    — outcomes settle yes sequentially as the running value
    // #             passes each unit threshold upward.
    // #             (over 1.5 settles before over 2.5, etc.)
    // #
    // # "diff"    — all outcomes settle simultaneously against the
    // #             end-game score differential. Used for handicaps.
    // #
    // # "rank"    — each outcome's unit is its final finishing position.
    // #             Resolves 1 if position <= number_of_winners, else 0.
    // #             Ties trigger dead-heat: partial value between 0–1.
    // #
    // # "two_way" — binary market; exactly one outcome resolves 1, the other 0.
    // #             (e.g. moneyline, Yes/No proposition)
    Diff,
    Over,
    Rank,
    TwoWay,
}

pub struct PmContract {
    pub id: uuid::Uuid,
    pub key: String,
    pub name: String,             // e.g. Over 2.5
    pub alias: String,            // e.g. o2.5
    pub unit_class: PmUnitClass,  // needs to be consistend with PmUnitClassName from PmProperties
    pub unit_class_value: String, // team name, 2.5, yes/no
}

pub struct PmProperties {
    pub unit_class: PmUnitClass,
    pub settlement_mechanic: PmSettlementMechanic,
    pub number_of_winners: u8,
    pub dead_heat_possible: bool,
    pub push_possible: bool,
    pub two_way_possible: bool,
    pub can_partially_settle: bool,
}

pub struct PmMarket {
    pub market_id: uuid::Uuid,
    pub fixture_id: uuid::Uuid,
    // TODO pub meta
    pub dimensions: Vec<PmDimension>,
    pub properties: PmProperties,
    pub contracts: Vec<uuid::Uuid>, // contract ids
}

pub struct PmSettings {
    pub lower_price_range: Decimal,
    pub upper_price_range: Decimal,
    pub single_quote: Decimal,
    pub max_exposure: Decimal,
}

pub struct PmFixture {
    pub fixture_id: uuid::Uuid,
    // TODO pub meta
    pub dimensions: Vec<PmDimension>,
    pub base_template: Option<String>,
    // TODO pub market_dimension_vocabulary:
    // TODO pub properties
    pub settings: PmSettings,
    pub markets: Vec<PmMarket>,
}

pub struct PmContractState {
    pub contract: PmContract,
    pub position: Decimal,
    // TODO
    // .. all dynamic data
    // size, avg_price
    // pub kalshi_fair: Decimal,
    // pub model_fair: Decimal,
    // pub kalshi_quoting_anchor: Decimal,
    // pub quote: Decimal, // bid, ask
}

// TODO by sports? enum?
#[derive(Debug, PartialEq)]
pub struct PmOutcomeState {
    pub all_more: Decimal,
    pub win_by_2: Decimal,
    pub win_by_1: Decimal,
    pub draw: Decimal,
    pub all_less: Decimal,
}

pub struct PmMarketState {
    pub market: PmMarket,
    pub settings: PmSettings,
    pub contract_states: HashMap<uuid::Uuid, PmContractState>, // by contract_id
    pub outcome_states: HashMap<String, PmOutcomeState>,       // global, exchange
}

impl PmMarketState {
    pub fn update_contract_state(&self, internal_ticker_id: &str, position: Decimal) {
        // TODO figure out which contract state to update given the internal_ticker_id
    }

    pub fn update_outcome_state(&self) {
        // TODO recompute the outcome states from the current contract states
    }
}

#[cfg(test)]
mod tests {
    use rust_decimal_macros::dec;

    use super::*;

    // e.g. https://api.elections.kalshi.com/trade-api/v2/events/KXWCGAME-26JUL09FRAMAR
    // {
    //     "event": {
    //         "category": "Sports",
    //         "event_ticker": "KXWCGAME-26JUL09FRAMAR",
    //         "mutually_exclusive": true,
    //         "series_ticker": "KXWCGAME",
    //         "title": "France vs Morocco: Regulation Time Moneyline"
    //     },
    //     "markets": [
    //         {
    //             "close_time": "2026-07-23T20:00:00Z",
    //             "event_ticker": "KXWCGAME-26JUL09FRAMAR",
    //             "market_type": "binary",
    //             "occurrence_datetime": "2026-07-09T23:00:00Z",
    //             "strike_type": "structured",
    //             "ticker": "KXWCGAME-26JUL09FRAMAR-FRA",
    //         },
    //         {
    //             "event_ticker": "KXWCGAME-26JUL09FRAMAR",
    //             "market_type": "binary",
    //             "occurrence_datetime": "2026-07-09T23:00:00Z",
    //             "strike_type": "structured",
    //             "ticker": "KXWCGAME-26JUL09FRAMAR-MAR",
    //         },
    //         {
    //             "event_ticker": "KXWCGAME-26JUL09FRAMAR",
    //             "market_type": "binary",
    //             "occurrence_datetime": "2026-07-09T23:00:00Z",
    //             "strike_type": "structured",
    //             "ticker": "KXWCGAME-26JUL09FRAMAR-TIE",
    //         }
    //     ]
    // }

    #[test]
    fn test_moneyline() {
        // position update with ticker e.g. KXWCGAME-26JUL09FRAMAR-FRA
        // convert kalshi ticker to internal ticker e.g. soccer-wc-fra-mar-0
        // get market state for this internal ticker
        // update contract state
        // update outcome state

        let contract_id_1 = uuid::Uuid::new_v4();
        let contract_id_2 = uuid::Uuid::new_v4();
        let contract_id_3 = uuid::Uuid::new_v4();
        let contract_states = HashMap::from([
            (
                contract_id_1,
                PmContractState {
                    contract: PmContract {
                        id: contract_id_1,
                        key: "france".into(),
                        name: "".into(),
                        alias: "".into(),
                        unit_class: PmUnitClass::Binary,
                        unit_class_value: "".into(),
                    },
                    position: dec!(0),
                },
            ),
            (
                contract_id_2,
                PmContractState {
                    contract: PmContract {
                        id: contract_id_2,
                        key: "draw".into(),
                        name: "".into(),
                        alias: "".into(),
                        unit_class: PmUnitClass::Binary,
                        unit_class_value: "".into(),
                    },
                    position: dec!(0),
                },
            ),
            (
                contract_id_3,
                PmContractState {
                    contract: PmContract {
                        id: contract_id_3,
                        key: "morocco".into(),
                        name: "".into(),
                        alias: "".into(),
                        unit_class: PmUnitClass::Binary,
                        unit_class_value: "".into(),
                    },
                    position: dec!(0),
                },
            ),
        ]);

        let market = PmMarket {
            market_id: uuid::Uuid::new_v4(),
            fixture_id: uuid::Uuid::new_v4(),
            dimensions: vec![],
            properties: PmProperties {
                unit_class: PmUnitClass::Binary,
                settlement_mechanic: PmSettlementMechanic::TwoWay,
                number_of_winners: 1,
                dead_heat_possible: false,
                push_possible: false,
                two_way_possible: true,
                can_partially_settle: false,
            },
            contracts: contract_states.keys().cloned().collect(),
        };

        let mut market_state = PmMarketState {
            market,
            settings: PmSettings {
                lower_price_range: dec!(0.05),
                upper_price_range: dec!(0.95),
                single_quote: dec!(10),
                max_exposure: dec!(10),
            },
            contract_states,
            outcome_states: HashMap::from([
                (
                    "outcome1".to_string(),
                    PmOutcomeState {
                        all_more: dec!(0),
                        win_by_2: dec!(0),
                        win_by_1: dec!(0),
                        draw: dec!(0),
                        all_less: dec!(0),
                    },
                ),
                (
                    "outcome2".to_string(),
                    PmOutcomeState {
                        all_more: dec!(0),
                        win_by_2: dec!(0),
                        win_by_1: dec!(0),
                        draw: dec!(0),
                        all_less: dec!(0),
                    },
                ),
                (
                    "outcome3".to_string(),
                    PmOutcomeState {
                        all_more: dec!(0),
                        win_by_2: dec!(0),
                        win_by_1: dec!(0),
                        draw: dec!(0),
                        all_less: dec!(0),
                    },
                ),
            ]),
        };

        market_state.update_contract_state("soccer-wc-fra-mar-0", dec!(10));
        market_state.update_outcome_state();

        // TODO
        // assert_eq!(
        //     market_state.outcome_states[""],
        //     PmOutcomeState {
        //         all_more: dec!(0),
        //         win_by_2: dec!(0),
        //         win_by_1: dec!(0),
        //         draw: dec!(0),
        //         all_less: dec!(0),
        //     },
        // )
    }
}