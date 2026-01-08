#![cfg_attr(not(test), no_std)]
#![cfg_attr(not(test), no_main)]
extern crate alloc;

// src/lib.rs
use odra::prelude::*;

#[odra::odra_error]
pub enum Error {
    Unauthorized = 1,
}

#[odra::module]
pub struct RiskOracle {
    pub risk_scores: Mapping<String, u8>,
    pub admin: Var<Address>,
    pub last_update: Var<u64>,
}

#[odra::module]
impl RiskOracle {
    pub fn init(&mut self) {
        let caller = self.env().caller();
        self.admin.set(caller);
    }

    pub fn update_risk(&mut self, validator: String, score: u8) {
        let caller = self.env().caller();
        if caller != self.admin.get().unwrap() {
             self.env().revert(Error::Unauthorized); 
        }
        
        self.risk_scores.set(&validator, score);
        self.last_update.set(self.env().get_block_time());
    }

    pub fn get_risk(&self, validator: String) -> u8 {
        self.risk_scores.get_or_default(&validator)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use odra::host::{Deployer, NoArgs};

    #[test]
    fn test_risk_oracle() {
        let env = odra_test::env();
        let mut contract = RiskOracle::deploy(&env, NoArgs);
        
        // Admin updates risk
        contract.update_risk("validator_1".to_string(), 50);
        assert_eq!(contract.get_risk("validator_1".to_string()), 50);

        // Check non-existent
        assert_eq!(contract.get_risk("validator_2".to_string()), 0);
    }
}
