use crate::error::{Error, Result};
use chia_protocol::Bytes32;
use chia_protocol::Coin;
use clvm_traits::{FromClvm, ToClvm};
use clvm_utils::tree_hash;
use clvm_utils::CurriedProgram;
use clvmr::allocator::{Allocator, NodePtr};
use hex_literal::hex;

#[derive(FromClvm, ToClvm)]
#[clvm(tuple)]
struct SingletonStruct {
    mod_hash: Bytes32,
    launcher_id: Bytes32,
    launcher_puzzle_hash: Bytes32,
}

#[derive(FromClvm, ToClvm)]
#[clvm(curried_args)]
struct SingletonArgs {
    singleton_struct: SingletonStruct,
    inner_puzzle: NodePtr,
}

#[derive(FromClvm, ToClvm)]
#[clvm(proper_list)]
struct LineageProof {
    parent_parent_coin_id: Bytes32,
    parent_inner_puzzle_hash: Bytes32,
    parent_amount: u64,
}

#[derive(FromClvm, ToClvm)]
#[clvm(proper_list)]
struct SingletonSolution {
    lineage_proof: LineageProof,
    amount: u64,
    inner_solution: NodePtr,
}

// given a puzzle, solution and coin of a singleton
// this function validates the lineage proof and returns a new
// solution targeting the new_parent ID.
pub fn fast_forward_singleton(
    a: &mut Allocator,
    puzzle: NodePtr,
    solution: NodePtr,
    coin: &Coin,
    new_parent: &Coin,
) -> Result<NodePtr> {
    let puzzle_hash = tree_hash(a, puzzle);

    if puzzle_hash != new_parent.puzzle_hash {
        // we can only fast-forward if the puzzle hash match the new coin
        // the spend is assumed to be valied already, so we don't check it
        // against the original coin being spent
        return Err(Error::PuzzleHashMismatch);
    }

    // a coin with an even amount is not a valid singleton
    // as defined by singleton_top_layer_v1_1.clsp
    if (new_parent.amount & 1) == 1 {
        return Err(Error::CoinAmountEven);
    }

    let singleton = CurriedProgram::<SingletonArgs>::from_clvm(a, puzzle)?;
    let mut new_solution = SingletonSolution::from_clvm(a, solution)?;

    // this is the tree hash of the singleton top layer puzzle
    // the tree hash of singleton_top_layer_v1_1.clsp
    if singleton.args.singleton_struct.mod_hash
        != hex!("7faa3253bfddd1e0decb0906b2dc6247bbc4cf608f58345d173adb63e8b47c9f")
    {
        return Err(Error::NotSingletonModHash);
    }

    let inner_puzzle_hash = tree_hash(a, singleton.args.inner_puzzle);
    if inner_puzzle_hash != new_solution.lineage_proof.parent_inner_puzzle_hash {
        return Err(Error::InnerPuzzleHashMismatch);
    }

    // we can only fast-forward if the coin amount stay the same
    // this is to minimize the risk of producing an invalid spend, after
    // fast-forward. e.g. we might end up attempting to spend more that the
    // amount of the coin
    if coin.amount != new_solution.lineage_proof.parent_amount {
        return Err(Error::CoinAmountMismatch);
    }

    // update the solution to use the new parent coin's information
    new_solution.lineage_proof.parent_parent_coin_id = new_parent.parent_coin_info;

    Ok(new_solution.to_clvm(a)?)
}
