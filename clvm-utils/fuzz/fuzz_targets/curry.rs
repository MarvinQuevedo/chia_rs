#![no_main]
use clvm_traits::{CurriedArgs, FromClvm, ToClvm};
use libfuzzer_sys::fuzz_target;

use clvm_utils::CurriedProgram;
use clvmr::allocator::Allocator;
use fuzzing_utils::{make_tree, BitCursor};

fuzz_target!(|data: &[u8]| {
    let mut a = Allocator::new();
    let input = make_tree(&mut a, &mut BitCursor::new(data), true);
    if let Ok(curry) = CurriedProgram::<CurriedArgs>::from_clvm(&a, input) {
        curry.to_clvm(&mut a).unwrap();
    }
});
